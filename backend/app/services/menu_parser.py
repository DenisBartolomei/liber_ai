"""
Menu Parser Service for LIBER
Uses AI to extract structured dish information from menu text
"""
import json
import re
from typing import List, Dict, Any
from flask import current_app
from openai import OpenAI


class MenuParserService:
    """
    Service for parsing menu text and extracting structured dish information.
    Uses GPT to intelligently identify dishes, categories, ingredients, etc.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))
        self.model = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini')
    
    def parse_menu_text(self, menu_text: str) -> List[Dict[str, Any]]:
        """
        Parse raw menu text and extract structured dish data.
        
        Args:
            menu_text: Raw text of the menu (copy-pasted or OCR'd)
            
        Returns:
            List of dish dictionaries with structured info
        """
        if not menu_text.strip():
            return []
        
        system_prompt = """Sei un esperto di gastronomia italiana. Analizza il testo del menù e estrai ogni piatto in formato JSON strutturato.

Per ogni piatto estrai:
- name: nome del piatto
- description: descrizione (se presente)
- category: categoria (antipasto, primo, secondo, contorno, dolce, bevanda)
- main_ingredient: ingrediente principale (pesce, carne_rossa, carne_bianca, verdure, formaggio, pasta, riso, uova, salumi)
- cooking_method: metodo cottura (crudo, grigliato, fritto, al_forno, brasato, bollito, saltato, arrosto)
- flavor_profile: array di caratteristiche ["grasso", "leggero", "speziato", "delicato", "affumicato", "piccante", "dolce", "acido", "umami"]
- price: prezzo numerico (null se non presente)

Rispondi SOLO con un array JSON valido. Nessun altro testo.

Esempio output:
[
  {
    "name": "Carpaccio di manzo",
    "description": "Con rucola e grana",
    "category": "antipasto",
    "main_ingredient": "carne_rossa",
    "cooking_method": "crudo",
    "flavor_profile": ["delicato", "umami"],
    "price": 14.00
  }
]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Estrai i piatti da questo menù:\n\n{menu_text}"}
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
                        'description': str(item.get('description', '')).strip() if item.get('description') else None,
                        'category': self._normalize_category(item.get('category')),
                        'main_ingredient': self._normalize_ingredient(item.get('main_ingredient')),
                        'cooking_method': item.get('cooking_method'),
                        'flavor_profile': item.get('flavor_profile') if isinstance(item.get('flavor_profile'), list) else None,
                        'price': self._parse_price(item.get('price'))
                    })
            
            return validated
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            # Fallback: try simple line-by-line parsing
            return self._simple_parse(menu_text)
        except Exception as e:
            print(f"Menu parsing error: {e}")
            return self._simple_parse(menu_text)
    
    def _normalize_category(self, category: str) -> str:
        """Normalize category to standard values."""
        if not category:
            return 'altro'
        
        category = category.lower().strip()
        
        mappings = {
            'antipasto': 'antipasto',
            'antipasti': 'antipasto',
            'starter': 'antipasto',
            'starters': 'antipasto',
            'primo': 'primo',
            'primi': 'primo',
            'primo piatto': 'primo',
            'pasta': 'primo',
            'risotto': 'primo',
            'secondo': 'secondo',
            'secondi': 'secondo',
            'secondo piatto': 'secondo',
            'carne': 'secondo',
            'pesce': 'secondo',
            'contorno': 'contorno',
            'contorni': 'contorno',
            'side': 'contorno',
            'dolce': 'dolce',
            'dolci': 'dolce',
            'dessert': 'dolce',
            'desserts': 'dolce',
            'bevanda': 'bevanda',
            'bevande': 'bevanda',
            'drink': 'bevanda',
            'drinks': 'bevanda'
        }
        
        return mappings.get(category, 'altro')
    
    def _normalize_ingredient(self, ingredient: str) -> str:
        """Normalize main ingredient to standard values."""
        if not ingredient:
            return None
        
        ingredient = ingredient.lower().strip().replace(' ', '_')
        
        valid = ['pesce', 'carne_rossa', 'carne_bianca', 'verdure', 
                 'formaggio', 'pasta', 'riso', 'uova', 'salumi', 'frutti_mare']
        
        if ingredient in valid:
            return ingredient
        
        # Try to map common variations
        if 'pesce' in ingredient or 'fish' in ingredient:
            return 'pesce'
        if 'manzo' in ingredient or 'agnello' in ingredient or 'maiale' in ingredient:
            return 'carne_rossa'
        if 'pollo' in ingredient or 'tacchino' in ingredient or 'coniglio' in ingredient:
            return 'carne_bianca'
        if 'verdur' in ingredient or 'vegetable' in ingredient:
            return 'verdure'
        
        return ingredient if len(ingredient) < 50 else None
    
    def _parse_price(self, price) -> float:
        """Parse price to float."""
        if price is None:
            return None
        if isinstance(price, (int, float)):
            return float(price)
        if isinstance(price, str):
            # Extract number from string like "€14" or "14.50"
            match = re.search(r'[\d.,]+', price.replace(',', '.'))
            if match:
                try:
                    return float(match.group())
                except:
                    return None
        return None
    
    def _simple_parse(self, menu_text: str) -> List[Dict[str, Any]]:
        """
        Simple fallback parser when AI fails.
        Just extracts lines that look like dish names.
        """
        items = []
        lines = menu_text.strip().split('\n')
        
        current_category = 'altro'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a category header
            lower = line.lower()
            if any(cat in lower for cat in ['antipast', 'prim', 'second', 'contorn', 'dolc', 'dessert']):
                if len(line) < 30 and ':' in line or line.isupper():
                    current_category = self._normalize_category(line.rstrip(':'))
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
            
            # Clean up the name
            name = re.sub(r'[-–—•·]\s*', '', line).strip()
            if name and len(name) > 2:
                items.append({
                    'name': name,
                    'description': None,
                    'category': current_category,
                    'main_ingredient': None,
                    'cooking_method': None,
                    'flavor_profile': None,
                    'price': price
                })
        
        return items

