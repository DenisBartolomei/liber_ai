"""
Wine Parser Service for LIBER
Uses AI to extract structured wine information from wine list text or images
"""
import json
import re
import base64
import logging
from typing import List, Dict, Any
from flask import current_app
from openai import OpenAI

logger = logging.getLogger(__name__)


class WineParserService:
    """
    Service for parsing wine list text/images and extracting structured wine information.
    Uses GPT to intelligently identify wines, regions, vintages, etc.
    Supports both text input and image OCR via GPT-4 Vision.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
        self.model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
        self.vision_model = 'gpt-4o'  # GPT-4 Vision for image parsing
    
    def parse_wine_images(self, base64_images: List[str]) -> List[Dict[str, Any]]:
        """
        Parse wine list images using GPT-4 Vision and extract structured wine data.
        
        Args:
            base64_images: List of base64-encoded images (with or without data URL prefix)
            
        Returns:
            List of wine dictionaries with structured info
        """
        if not base64_images:
            return []
        
        logger.info(f"Parsing {len(base64_images)} wine list images")
        
        system_prompt = """Sei un sommelier esperto. Analizza le immagini della carta dei vini e estrai TUTTI i vini visibili in formato JSON strutturato.

Per ogni vino estrai:
- name: nome completo del vino (includi denominazione se presente, es. "Brunello di Montalcino DOCG")
- type: tipo (red, white, rose, sparkling, dessert, fortified) - deducilo dal nome/sezione
- region: regione di produzione (es. "Toscana", "Piemonte", "Veneto")
- country: paese (default "Italia" se italiano, altrimenti specifica)
- grape_variety: vitigni principali se identificabili
- vintage: annata come numero (es. 2019, null se non specificato o NV)
- producer: produttore/cantina se indicato
- price: prezzo numerico (null se non visibile)
- description: descrizione se presente

IMPORTANTE:
- Estrai TUTTI i vini che riesci a leggere
- Se un testo non è leggibile, salta quel vino
- Deduci il tipo di vino dalla sezione della carta (es. "Vini Rossi" = type "red")
- Mantieni i nomi in italiano dove possibile

Rispondi SOLO con un array JSON valido. Nessun altro testo."""

        # Build content with images
        content = [{"type": "text", "text": "Estrai tutti i vini da queste immagini della carta dei vini:"}]
        
        for img_data in base64_images:
            # Handle both raw base64 and data URL format
            if img_data.startswith('data:'):
                image_url = img_data
            else:
                image_url = f"data:image/jpeg;base64,{img_data}"
            
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": "high"  # High detail for better text recognition
                }
            })
        
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.2,
                max_tokens=4096
            )
            
            result = response.choices[0].message.content.strip()
            logger.debug(f"Vision API response: {result[:500]}...")
            
            # Clean up response (sometimes GPT adds markdown)
            if result.startswith('```'):
                result = re.sub(r'^```json?\n?', '', result)
                result = re.sub(r'\n?```$', '', result)
            
            items = json.loads(result)
            
            # Validate and clean items
            validated = []
            for item in items:
                if isinstance(item, dict) and item.get('name'):
                    validated.append({
                        'name': str(item.get('name', '')).strip(),
                        'type': self._normalize_wine_type(item.get('type')),
                        'region': str(item.get('region', '')).strip() if item.get('region') else None,
                        'country': str(item.get('country', 'Italia')).strip(),
                        'grape_variety': str(item.get('grape_variety', '')).strip() if item.get('grape_variety') else None,
                        'vintage': self._parse_vintage(item.get('vintage')),
                        'producer': str(item.get('producer', '')).strip() if item.get('producer') else None,
                        'price': self._parse_price(item.get('price')),
                        'description': str(item.get('description', '')).strip() if item.get('description') else None,
                        'tasting_notes': None,
                        'food_pairings': None
                    })
            
            logger.info(f"Extracted {len(validated)} wines from images")
            return validated
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error from Vision API: {e}")
            return []
        except Exception as e:
            logger.error(f"Wine image parsing error: {e}")
            return []
    
    def parse_wine_list(self, wine_text: str) -> List[Dict[str, Any]]:
        """
        Parse raw wine list text and extract structured wine data.
        
        Args:
            wine_text: Raw text of the wine list (copy-pasted or OCR'd)
            
        Returns:
            List of wine dictionaries with structured info
        """
        if not wine_text.strip():
            return []
        
        system_prompt = """Sei un sommelier esperto. Analizza il testo della carta dei vini e estrai ogni vino in formato JSON strutturato.

Per ogni vino estrai:
- name: nome completo del vino (includi denominazione se presente, es. "Brunello di Montalcino DOCG")
- type: tipo (red, white, rose, sparkling, dessert, fortified)
- region: regione di produzione (es. "Toscana", "Piemonte", "Veneto")
- country: paese (default "Italia" se non specificato)
- grape_variety: vitigni principali (es. "Sangiovese", "Nebbiolo, Barbera")
- vintage: annata come numero (es. 2019, null se non specificato o NV)
- producer: produttore/cantina (se identificabile)
- price: prezzo numerico (null se non presente)
- description: descrizione breve se presente
- tasting_notes: note degustative se presenti
- food_pairings: array di abbinamenti consigliati se presenti

Rispondi SOLO con un array JSON valido. Nessun altro testo.

Esempio output:
[
  {
    "name": "Barolo DOCG",
    "type": "red",
    "region": "Piemonte",
    "country": "Italia",
    "grape_variety": "Nebbiolo",
    "vintage": 2018,
    "producer": "Marchesi di Barolo",
    "price": 75.00,
    "description": "Barolo classico dalle Langhe",
    "tasting_notes": "Note di rosa, catrame e frutti rossi",
    "food_pairings": ["brasato", "tartufo", "formaggi stagionati"]
  }
]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Estrai i vini da questa carta:\n\n{wine_text}"}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up response (sometimes GPT adds markdown)
            if content.startswith('```'):
                content = re.sub(r'^```json?\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            
            items = json.loads(content)
            
            # Validate and clean items
            validated = []
            for item in items:
                if isinstance(item, dict) and item.get('name'):
                    validated.append({
                        'name': str(item.get('name', '')).strip(),
                        'type': self._normalize_wine_type(item.get('type')),
                        'region': str(item.get('region', '')).strip() if item.get('region') else None,
                        'country': str(item.get('country', 'Italia')).strip(),
                        'grape_variety': str(item.get('grape_variety', '')).strip() if item.get('grape_variety') else None,
                        'vintage': self._parse_vintage(item.get('vintage')),
                        'producer': str(item.get('producer', '')).strip() if item.get('producer') else None,
                        'price': self._parse_price(item.get('price')),
                        'description': str(item.get('description', '')).strip() if item.get('description') else None,
                        'tasting_notes': str(item.get('tasting_notes', '')).strip() if item.get('tasting_notes') else None,
                        'food_pairings': item.get('food_pairings') if isinstance(item.get('food_pairings'), list) else None
                    })
            
            return validated
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # Fallback: try simple line-by-line parsing
            return self._simple_parse(wine_text)
        except Exception as e:
            print(f"Wine parsing error: {e}")
            return self._simple_parse(wine_text)
    
    def _normalize_wine_type(self, wine_type: str) -> str:
        """Normalize wine type to standard values."""
        if not wine_type:
            return 'red'
        
        wine_type = wine_type.lower().strip()
        
        mappings = {
            'red': 'red',
            'rosso': 'red',
            'rouge': 'red',
            'white': 'white',
            'bianco': 'white',
            'blanc': 'white',
            'rose': 'rose',
            'rosato': 'rose',
            'rosé': 'rose',
            'sparkling': 'sparkling',
            'spumante': 'sparkling',
            'champagne': 'sparkling',
            'prosecco': 'sparkling',
            'franciacorta': 'sparkling',
            'metodo classico': 'sparkling',
            'dessert': 'dessert',
            'dolce': 'dessert',
            'passito': 'dessert',
            'vin santo': 'dessert',
            'fortified': 'fortified',
            'fortificato': 'fortified',
            'marsala': 'fortified',
            'porto': 'fortified',
            'sherry': 'fortified'
        }
        
        return mappings.get(wine_type, 'red')
    
    def _parse_vintage(self, vintage) -> int:
        """Parse vintage to integer."""
        if vintage is None:
            return None
        if isinstance(vintage, int):
            return vintage if 1900 <= vintage <= 2030 else None
        if isinstance(vintage, str):
            # Handle "NV" (non-vintage)
            if vintage.upper() in ['NV', 'N.V.', 'NON VINTAGE', 'S.A.']:
                return None
            # Extract year from string
            match = re.search(r'(19|20)\d{2}', vintage)
            if match:
                return int(match.group())
        return None
    
    def _parse_price(self, price) -> float:
        """Parse price to float."""
        if price is None:
            return None
        if isinstance(price, (int, float)):
            return float(price)
        if isinstance(price, str):
            # Extract number from string like "€45" or "45.00"
            match = re.search(r'[\d.,]+', price.replace(',', '.'))
            if match:
                try:
                    return float(match.group())
                except:
                    return None
        return None
    
    def _simple_parse(self, wine_text: str) -> List[Dict[str, Any]]:
        """
        Simple fallback parser when AI fails.
        Extracts lines that look like wine names.
        """
        items = []
        lines = wine_text.strip().split('\n')
        
        current_type = 'red'
        
        # Type detection patterns
        type_patterns = {
            'red': ['rosso', 'rossi', 'red', 'rouge'],
            'white': ['bianco', 'bianchi', 'white', 'blanc'],
            'rose': ['rosato', 'rosati', 'rose', 'rosé'],
            'sparkling': ['spumante', 'spumanti', 'sparkling', 'bollicine', 'champagne', 'prosecco', 'franciacorta']
        }
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            lower = line.lower()
            
            # Check if it's a type header
            for wine_type, patterns in type_patterns.items():
                if any(pat in lower for pat in patterns):
                    if len(line) < 30:
                        current_type = wine_type
                        continue
            
            # Skip very short lines or lines that are just prices
            if len(line) < 3 or re.match(r'^[€$\d.,\s]+$', line):
                continue
            
            # Extract price if present
            price = None
            price_match = re.search(r'[€$]\s*(\d+[.,]?\d*)', line)
            if price_match:
                price = float(price_match.group(1).replace(',', '.'))
                line = re.sub(r'[€$]\s*\d+[.,]?\d*', '', line).strip()
            
            # Extract vintage if present
            vintage = None
            vintage_match = re.search(r'\b(19|20)(\d{2})\b', line)
            if vintage_match:
                vintage = int(vintage_match.group())
            
            # Clean up the name
            name = re.sub(r'[-–—•·]\s*', '', line).strip()
            if name and len(name) > 2:
                items.append({
                    'name': name,
                    'type': current_type,
                    'region': None,
                    'country': 'Italia',
                    'grape_variety': None,
                    'vintage': vintage,
                    'producer': None,
                    'price': price,
                    'description': None,
                    'tasting_notes': None,
                    'food_pairings': None
                })
        
        return items

