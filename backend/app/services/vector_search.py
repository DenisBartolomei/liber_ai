"""
Vector Search Service using Qdrant for LIBER
Handles semantic search for wine recommendations
"""
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from flask import current_app
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct


class VectorSearchService:
    """
    Service for semantic wine search using Qdrant vector database.
    Uses OpenAI embeddings for text vectorization.
    """
    
    def __init__(self):
        self.qdrant_host = current_app.config.get('QDRANT_HOST', 'localhost')
        self.qdrant_port = current_app.config.get('QDRANT_PORT', 6333)
        self.collection_name = current_app.config.get('QDRANT_COLLECTION', 'wines')
        self.embedding_model = current_app.config.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
        self.embedding_dimensions = 1536  # text-embedding-3-small dimensions
        
        # Initialize clients
        self.openai_client = OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
        
        try:
            self.qdrant_client = QdrantClient(
                host=self.qdrant_host, 
                port=self.qdrant_port
            )
            self._ensure_collection_exists()
        except Exception as e:
            print(f"Warning: Could not connect to Qdrant: {e}")
            self.qdrant_client = None
    
    def _ensure_collection_exists(self):
        """Create the collection if it doesn't exist."""
        if not self.qdrant_client:
            return
            
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimensions,
                    distance=Distance.COSINE
                )
            )
            print(f"Created Qdrant collection: {self.collection_name}")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a text using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimensions
    
    def index_product(self, product) -> bool:
        """
        Index a product in the vector database.
        
        Args:
            product: Product model instance
            
        Returns:
            bool: Success status
        """
        if not self.qdrant_client:
            print("Qdrant client not available")
            return False
        
        try:
            # Generate text representation
            text = product.get_embedding_text()
            
            # Get embedding
            embedding = self._get_embedding(text)
            
            # Generate or use existing qdrant_id
            if not product.qdrant_id:
                product.qdrant_id = str(uuid.uuid4())
            
            # Prepare payload
            payload = {
                'product_id': product.id,
                'venue_id': product.venue_id,
                'name': product.name,
                'type': product.type,
                'region': product.region,
                'grape_variety': product.grape_variety,
                'vintage': product.vintage,
                'price': float(product.price) if product.price else None,
                'description': product.description,
                'tasting_notes': product.tasting_notes,
                'food_pairings': product.food_pairings,
                'is_available': product.is_available
            }
            
            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=product.qdrant_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            # Update product with embedding timestamp
            product.embedding_updated_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            print(f"Error indexing product {product.id}: {e}")
            return False
    
    def delete_product(self, product) -> bool:
        """
        Remove a product from the vector database.
        
        Args:
            product: Product model instance
            
        Returns:
            bool: Success status
        """
        if not self.qdrant_client or not product.qdrant_id:
            return False
        
        try:
            self.qdrant_client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[product.qdrant_id]
                )
            )
            return True
        except Exception as e:
            print(f"Error deleting product {product.id}: {e}")
            return False
    
    def bulk_index(self, products: List) -> int:
        """
        Bulk index multiple products.
        
        Args:
            products: List of Product model instances
            
        Returns:
            int: Number of successfully indexed products
        """
        if not self.qdrant_client:
            return 0
        
        success_count = 0
        points = []
        
        for product in products:
            try:
                text = product.get_embedding_text()
                embedding = self._get_embedding(text)
                
                if not product.qdrant_id:
                    product.qdrant_id = str(uuid.uuid4())
                
                payload = {
                    'product_id': product.id,
                    'venue_id': product.venue_id,
                    'name': product.name,
                    'type': product.type,
                    'region': product.region,
                    'grape_variety': product.grape_variety,
                    'vintage': product.vintage,
                    'price': float(product.price) if product.price else None,
                    'description': product.description,
                    'tasting_notes': product.tasting_notes,
                    'food_pairings': product.food_pairings,
                    'is_available': product.is_available
                }
                
                points.append(PointStruct(
                    id=product.qdrant_id,
                    vector=embedding,
                    payload=payload
                ))
                
                product.embedding_updated_at = datetime.utcnow()
                success_count += 1
                
            except Exception as e:
                print(f"Error preparing product {product.id}: {e}")
        
        if points:
            try:
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
            except Exception as e:
                print(f"Error bulk upserting: {e}")
                return 0
        
        return success_count
    
    def search(
        self, 
        query: str, 
        venue_id: int,
        limit: int = 10,
        wine_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        available_only: bool = True
    ) -> List[Dict]:
        """
        Search for wines semantically matching the query.
        
        Args:
            query: Search query (e.g., "vino rosso corposo per la carne")
            venue_id: Filter by venue
            limit: Max results to return
            wine_type: Filter by wine type (red, white, etc.)
            min_price: Minimum price filter
            max_price: Maximum price filter
            available_only: Only return available wines
            
        Returns:
            List of wine dictionaries with scores
        """
        if not self.qdrant_client:
            # Fallback to database search if Qdrant is not available
            return self._fallback_search(query, venue_id, limit)
        
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            
            # Build filter conditions
            must_conditions = [
                models.FieldCondition(
                    key="venue_id",
                    match=models.MatchValue(value=venue_id)
                )
            ]
            
            if available_only:
                must_conditions.append(
                    models.FieldCondition(
                        key="is_available",
                        match=models.MatchValue(value=True)
                    )
                )
            
            if wine_type:
                must_conditions.append(
                    models.FieldCondition(
                        key="type",
                        match=models.MatchValue(value=wine_type)
                    )
                )
            
            if min_price is not None:
                must_conditions.append(
                    models.FieldCondition(
                        key="price",
                        range=models.Range(gte=min_price)
                    )
                )
            
            if max_price is not None:
                must_conditions.append(
                    models.FieldCondition(
                        key="price",
                        range=models.Range(lte=max_price)
                    )
                )
            
            # Search Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=models.Filter(must=must_conditions),
                limit=limit
            )
            
            # Transform results
            wines = []
            for hit in results:
                wine = hit.payload.copy()
                wine['id'] = wine.pop('product_id', None)
                wine['score'] = hit.score
                wines.append(wine)
            
            return wines
            
        except Exception as e:
            print(f"Search error: {e}")
            return self._fallback_search(query, venue_id, limit)
    
    def _fallback_search(
        self, 
        query: str, 
        venue_id: int, 
        limit: int
    ) -> List[Dict]:
        """Fallback to database search when Qdrant is unavailable."""
        from app.models import Product
        
        # Simple keyword-based search
        query_lower = query.lower()
        
        products = Product.query.filter_by(
            venue_id=venue_id,
            is_available=True
        ).all()
        
        # Score products based on keyword matching
        scored = []
        for p in products:
            score = 0
            text = f"{p.name} {p.type} {p.region} {p.grape_variety} {p.description or ''}".lower()
            
            for word in query_lower.split():
                if word in text:
                    score += 1
            
            if score > 0:
                scored.append((p, score))
        
        # Sort by score and return top results
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [p.to_dict() for p, _ in scored[:limit]]
    
    def find_similar(
        self, 
        product_id: int, 
        venue_id: int,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find wines similar to a given product.
        
        Args:
            product_id: ID of the reference product
            venue_id: Filter by venue
            limit: Max results
            
        Returns:
            List of similar wine dictionaries
        """
        from app.models import Product
        
        product = Product.query.get(product_id)
        if not product or not product.qdrant_id:
            return []
        
        if not self.qdrant_client:
            return []
        
        try:
            # Get the product's vector
            point = self.qdrant_client.retrieve(
                collection_name=self.collection_name,
                ids=[product.qdrant_id],
                with_vectors=True
            )
            
            if not point:
                return []
            
            vector = point[0].vector
            
            # Search for similar
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="venue_id",
                            match=models.MatchValue(value=venue_id)
                        ),
                        models.FieldCondition(
                            key="is_available",
                            match=models.MatchValue(value=True)
                        )
                    ],
                    must_not=[
                        models.FieldCondition(
                            key="product_id",
                            match=models.MatchValue(value=product_id)
                        )
                    ]
                ),
                limit=limit
            )
            
            wines = []
            for hit in results:
                wine = hit.payload.copy()
                wine['id'] = wine.pop('product_id', None)
                wine['similarity_score'] = hit.score
                wines.append(wine)
            
            return wines
            
        except Exception as e:
            print(f"Similarity search error: {e}")
            return []

