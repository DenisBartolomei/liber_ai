"""
Wine Description Generator Service
Uses fine-tuned GPT model to generate professional wine descriptions
"""
import json
import logging
from typing import Dict, Optional, List
from openai import OpenAI, APIError, RateLimitError
from flask import current_app
from app.services.fine_tuned_selector import FineTunedWineSelector

logger = logging.getLogger(__name__)


class WineDescriptionGenerator:
    """
    Service for generating professional wine descriptions using fine-tuned GPT model.
    Descriptions include: color, structural characteristics, organoleptic characteristics.
    """
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY', '')
        
        if not api_key or not api_key.strip():
            logger.error("OPENAI_API_KEY is not configured!")
            raise ValueError("OPENAI_API_KEY non configurata. Contatta l'amministratore del sistema.")
        
        try:
            self.client = OpenAI(api_key=api_key, timeout=60.0)
        except TypeError as e:
            import os
            os.environ['OPENAI_API_KEY'] = api_key
            self.client = OpenAI(timeout=60.0)
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise
        
        self.model = current_app.config.get('OPENAI_FINETUNED_MODEL', 'gpt-4o-mini')
        logger.info(f"WineDescriptionGenerator initialized with model: {self.model}")
    
    def generate_description(
        self,
        wine_name: str,
        wine_type: str,
        region: Optional[str] = None,
        grape_variety: Optional[str] = None,
        vintage: Optional[int] = None,
        producer: Optional[str] = None,
        price: Optional[float] = None
    ) -> str:
        """
        Generate professional wine description using fine-tuned model.
        
        Args:
            wine_name: Full name of the wine
            wine_type: Type of wine (red, white, rose, sparkling, dessert, fortified)
            region: Production region (optional)
            grape_variety: Main grape variety (optional)
            vintage: Vintage year (optional)
            producer: Producer name (optional)
            price: Price (optional, for context)
            
        Returns:
            Professional wine description string
        """
        
        # Build wine context
        wine_context_parts = [f"Vino: {wine_name}"]
        wine_context_parts.append(f"Tipo: {wine_type}")
        
        if region:
            wine_context_parts.append(f"Regione: {region}")
        if grape_variety:
            wine_context_parts.append(f"Vitigno: {grape_variety}")
        if vintage:
            wine_context_parts.append(f"Annata: {vintage}")
        if producer:
            wine_context_parts.append(f"Produttore: {producer}")
        if price:
            wine_context_parts.append(f"Prezzo: €{price:.2f}")
        
        wine_context = "\n".join(wine_context_parts)
        
        # Build system prompt for description generation with structured data
        system_prompt = """Sei un sommelier esperto e professionale. Il tuo compito è scrivere descrizioni specialistiche di vini per una carta vini di ristorante e fornire dati strutturati.

Rispondi SEMPRE in formato JSON con questa struttura:
{
  "description": "Descrizione professionale del vino (3-5 righe, 150-250 parole). Include: colore, caratteristiche strutturali (corpo, tannini se rosso, acidità), caratteristiche organolettiche (profumi, aromi, sapori, finale).",
  "color": "Descrizione precisa del colore (es. 'Rosso rubino intenso', 'Giallo paglierino brillante')",
  "aromas": "Lista di 3-5 aromi principali separati da virgola (es. 'Ciliegia matura, Tabacco, Spezie dolci, Cuoio')",
  "body": 7,  // Valore numerico da 1 (leggero) a 10 (pieno)
  "acidity": 6,  // Valore numerico da 1 (basso) a 10 (alto)
  "tannins": 8  // Valore numerico da 1 (morbidi) a 10 (potenti). Solo per vini rossi, per bianchi/rosati/spumanti usa null
}

IMPORTANTE:
- La descrizione deve essere professionale ma accessibile
- I valori numerici devono essere realistici (1-10)
- Per vini bianchi, rosati e spumanti, tannins deve essere null
- Gli aromi devono essere specifici e riconoscibili"""
        
        user_prompt = f"""Analizza questo vino e fornisci descrizione e dati strutturati:

{wine_context}

Rispondi in formato JSON:"""
        
        try:
            logger.info(f"Generating description for wine: {wine_name} ({wine_type})")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Slightly creative but consistent
                max_tokens=500,  # Increased for JSON response
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                import json
                data = json.loads(content)
                
                # Extract structured data
                description = data.get('description', '')
                color = data.get('color', '')
                aromas = data.get('aromas', '')
                body = data.get('body')
                acidity = data.get('acidity')
                tannins = data.get('tannins')
                
                # Validate and clamp numeric values to 1-10
                if body is not None:
                    body = max(1, min(10, int(body)))
                if acidity is not None:
                    acidity = max(1, min(10, int(acidity)))
                if tannins is not None:
                    tannins = max(1, min(10, int(tannins)))
                # For white/rose/sparkling wines, tannins should be null
                if wine_type in ['white', 'rose', 'sparkling']:
                    tannins = None
                
                # Return structured data
                result = {
                    'description': description,
                    'color': color,
                    'aromas': aromas,
                    'body': body,
                    'acidity_level': acidity,
                    'tannin_level': tannins
                }
                
                logger.info(f"Description and structured data generated successfully for {wine_name}")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON response, falling back to text: {e}")
                # Fallback: treat as plain description
                description = content
                if description.startswith('```'):
                    description = description.split('```')[1]
                    if description.startswith('json') or description.startswith('markdown') or description.startswith('text'):
                        description = description.split('\n', 1)[1] if '\n' in description else description
                    description = description.strip()
                
                return {
                    'description': description,
                    'color': None,
                    'aromas': None,
                    'body': None,
                    'acidity_level': None,
                    'tannin_level': None
                }
            
        except RateLimitError as e:
            logger.error(f"Rate limit error generating description: {e}")
            raise Exception("Limite di richieste raggiunto. Riprova tra qualche secondo.")
        except APIError as e:
            logger.error(f"OpenAI API error generating description: {e}")
            raise Exception(f"Errore API OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating description: {e}")
            raise Exception(f"Errore durante la generazione della descrizione: {str(e)}")
    
    def generate_descriptions_batch(
        self,
        wines: List[Dict]
    ) -> List[Dict]:
        """
        Generate descriptions for multiple wines in batch.
        
        Args:
            wines: List of wine dictionaries with at least 'name' and 'type'
            
        Returns:
            List of wines with 'description' and structured data fields added
        """
        results = []
        
        for idx, wine in enumerate(wines, 1):
            try:
                result = self.generate_description(
                    wine_name=wine.get('name', ''),
                    wine_type=wine.get('type', 'red'),
                    region=wine.get('region'),
                    grape_variety=wine.get('grape_variety'),
                    vintage=wine.get('vintage'),
                    producer=wine.get('producer'),
                    price=wine.get('price')
                )
                
                # result is now a dict with description and structured data
                wine_with_data = wine.copy()
                wine_with_data['description'] = result.get('description', '')
                wine_with_data['color'] = result.get('color')
                wine_with_data['aromas'] = result.get('aromas')
                wine_with_data['body'] = result.get('body')
                wine_with_data['acidity_level'] = result.get('acidity_level')
                wine_with_data['tannin_level'] = result.get('tannin_level')
                wine_with_data['description_status'] = 'completed'
                results.append(wine_with_data)
                
                logger.info(f"Generated description {idx}/{len(wines)}: {wine.get('name')}")
                
            except Exception as e:
                logger.error(f"Error generating description for wine {wine.get('name')}: {e}")
                wine_with_error = wine.copy()
                wine_with_error['description'] = None
                wine_with_error['color'] = None
                wine_with_error['aromas'] = None
                wine_with_error['body'] = None
                wine_with_error['acidity_level'] = None
                wine_with_error['tannin_level'] = None
                wine_with_error['description_status'] = 'error'
                wine_with_error['description_error'] = str(e)
                results.append(wine_with_error)
        
        return results

