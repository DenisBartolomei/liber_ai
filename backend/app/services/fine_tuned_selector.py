"""
Fine-Tuned Wine Selector Service
Uses fine-tuned model to select wines based on context and return structured JSON
"""
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI, APIError, AuthenticationError, RateLimitError
from flask import current_app
from app.prompts.b2c_system import get_finetuned_selection_prompt

logger = logging.getLogger(__name__)


class FineTunedWineSelector:
    """
    Service that uses fine-tuned model to select wines and return structured JSON.
    """
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY', '')
        
        if not api_key or not api_key.strip():
            logger.error("OPENAI_API_KEY is not configured!")
            raise ValueError("OPENAI_API_KEY non configurata. Contatta l'amministratore del sistema.")
        
        try:
            self.client = OpenAI(api_key=api_key, timeout=60.0)  # 60 second timeout for fine-tuned
        except TypeError as e:
            import os
            os.environ['OPENAI_API_KEY'] = api_key
            self.client = OpenAI(timeout=60.0)
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise
        
        self.model = current_app.config.get('OPENAI_FINETUNED_MODEL', 'gpt-4o-mini')
        logger.info(f"FineTunedWineSelector initialized with model: {self.model} (from OPENAI_FINETUNED_MODEL)")
    
    def select_wines(
        self,
        venue_name: str,
        venue_id: int,
        context: Dict,
        gathered_info: Dict,
        all_wines: List[Dict],
        history: List[Dict],
        user_message: str,
        featured_wines: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Select wines using fine-tuned model and return structured JSON.
        
        Args:
            venue_name: Name of the venue
            venue_id: ID of the venue
            context: Context with dishes, guest_count
            gathered_info: Preferences (wine_type, journey_preference, budget)
            all_wines: Complete list of wines from DB
            history: Conversation history
            user_message: Current user message
            featured_wines: Optional list of product IDs that should be prioritized (max 2)
            
        Returns:
            Dict with 'wines' (for single mode) or 'journeys' (for journey mode)
        """
        if not all_wines:
            logger.warning("No wines available for selection")
            return {'wines': [], 'journeys': []}
        
        # Build prompt for fine-tuned model
        system_prompt = get_finetuned_selection_prompt(
            venue_name=venue_name,
            context=context,
            gathered_info=gathered_info,
            all_wines=all_wines,
            featured_wines=featured_wines or []
        )
        
        # Build conversation context for the model - limit history for speed
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 3 messages only for faster processing)
        for msg in history[-3:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Call fine-tuned model with JSON response format
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent selections
                max_completion_tokens=4000,  # Increased to support ranking of all wines in large catalogs
                response_format={"type": "json_object"}
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse JSON response with robust error handling
            try:
                # Try to extract JSON from response (might have extra text)
                ai_response_clean = ai_response.strip()
                # Try to find JSON object in response
                if ai_response_clean.startswith('{'):
                    # Response starts with JSON
                    result_json = json.loads(ai_response_clean)
                elif '{' in ai_response_clean and '}' in ai_response_clean:
                    # Find JSON object in response
                    start_idx = ai_response_clean.find('{')
                    end_idx = ai_response_clean.rfind('}') + 1
                    json_str = ai_response_clean[start_idx:end_idx]
                    result_json = json.loads(json_str)
                else:
                    logger.error(f"Fine-tuned model response does not contain valid JSON: {ai_response_clean[:200]}")
                    return {'wines': [], 'journeys': []}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from fine-tuned model: {e}")
                logger.error(f"Response was: {ai_response[:500]}")
                return {'wines': [], 'journeys': []}
            except Exception as e:
                logger.error(f"Unexpected error parsing JSON: {e}")
                return {'wines': [], 'journeys': []}
            
            # Validate and enrich the JSON with DB data
            validated_result = self._validate_and_enrich_result(
                result_json,
                all_wines,
                gathered_info.get('journey_preference', 'single'),
                gathered_info,
                featured_wines=featured_wines or []
            )
            
            return validated_result
            
        except AuthenticationError as e:
            logger.error(f"OpenAI Authentication Error: {e}")
            raise ValueError("Errore di autenticazione con il servizio AI. Verifica la configurazione API.")
        
        except RateLimitError as e:
            logger.error(f"OpenAI Rate Limit Error: {e}")
            raise ValueError("Servizio AI momentaneamente sovraccarico. Riprova tra qualche secondo.")
        
        except APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            raise ValueError(f"Errore del servizio AI: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error in select_wines: {e}")
            raise ValueError(f"Si è verificato un errore imprevisto. Riprova.")
    
    def _validate_and_enrich_result(
        self,
        result_json: Dict,
        all_wines: List[Dict],
        journey_preference: str,
        gathered_info: Optional[Dict] = None,
        featured_wines: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Validate JSON result and enrich with full wine data from DB.
        
        Args:
            result_json: JSON from fine-tuned model
            all_wines: Complete list of wines from DB
            journey_preference: 'single' or 'journey'
            gathered_info: Preferences dict with budget info
            
        Returns:
            Validated and enriched result
        """
        # Create wine lookup by ID and name
        wine_by_id = {w.get('id'): w for w in all_wines if w.get('id')}
        wine_by_name = {w.get('name', '').lower().strip(): w for w in all_wines if w.get('name')}
        
        validated = {'wines': [], 'journeys': []}
        
        if journey_preference == 'journey':
            # Validate journeys - must have exactly 2-3 journeys
            journeys = result_json.get('journeys', [])
            if not isinstance(journeys, list):
                journeys = []
            
            bottles_count = gathered_info.get('bottles_count') if gathered_info else None
            
            for journey in journeys:
                if not isinstance(journey, dict):
                    continue
                
                journey_wines = []
                wines_data = journey.get('wines', [])
                
                if not isinstance(wines_data, list):
                    continue
                
                for wine_data in wines_data:
                    wine_id = wine_data.get('id') if isinstance(wine_data, dict) else None
                    wine_name = wine_data.get('name') if isinstance(wine_data, dict) else None
                    
                    # Find wine by ID or name
                    wine = None
                    if wine_id and wine_id in wine_by_id:
                        wine = wine_by_id[wine_id]
                    elif wine_name:
                        wine = wine_by_name.get(wine_name.lower().strip())
                    
                    if wine:
                        # Enrich with full wine data
                        enriched_wine = {
                            'id': wine.get('id'),
                            'name': wine.get('name'),
                            'price': wine.get('price'),
                            'type': wine.get('type'),
                            'region': wine.get('region'),
                            'grape_variety': wine.get('grape_variety'),
                            'vintage': wine.get('vintage'),
                            'description': wine.get('description'),
                            'tasting_notes': wine.get('tasting_notes')
                        }
                        journey_wines.append(enriched_wine)
                
                # Only add journey if it has the correct number of wines
                if journey_wines:
                    # Validate bottles_count if specified
                    if bottles_count and len(journey_wines) != bottles_count:
                        logger.warning(
                            f"Journey {journey.get('id')} has {len(journey_wines)} wines, expected {bottles_count}. "
                            f"Skipping this journey."
                        )
                        continue
                    
                    validated['journeys'].append({
                        'id': journey.get('id', len(validated['journeys']) + 1),
                        'name': journey.get('name', 'Percorso di Degustazione'),
                        'reason': journey.get('reason', ''),
                        'wines': journey_wines
                    })
            
            # Validate we have exactly 2-3 journeys
            if len(validated['journeys']) < 2:
                logger.warning(
                    f"Journey mode: Only {len(validated['journeys'])} valid journeys found, expected 2-3. "
                    f"Returning what we have."
                )
            elif len(validated['journeys']) > 3:
                logger.warning(
                    f"Journey mode: {len(validated['journeys'])} journeys found, expected max 3. "
                    f"Taking only first 3."
                )
                validated['journeys'] = validated['journeys'][:3]
        
        else:
            # Validate single mode wines - rank ALL wines
            wines = result_json.get('wines', [])
            if not isinstance(wines, list):
                wines = []
            
            for wine_data in wines:
                if not isinstance(wine_data, dict):
                    continue
                
                wine_id = wine_data.get('id')
                wine_name = wine_data.get('name')
                
                # Find wine by ID or name
                wine = None
                if wine_id and wine_id in wine_by_id:
                    wine = wine_by_id[wine_id]
                elif wine_name:
                    wine = wine_by_name.get(wine_name.lower().strip())
                
                if wine:
                    # Get rank from JSON, or use position as fallback
                    rank = wine_data.get('rank')
                    if rank is None:
                        # If rank not provided, use position in array (1-indexed)
                        rank = len(validated['wines']) + 1
                    
                    # Enrich with full wine data + add reason, best, and rank from JSON
                    enriched_wine = {
                        'id': wine.get('id'),
                        'name': wine.get('name'),
                        'price': wine.get('price'),
                        'type': wine.get('type'),
                        'region': wine.get('region'),
                        'grape_variety': wine.get('grape_variety'),
                        'vintage': wine.get('vintage'),
                        'description': wine.get('description'),
                        'tasting_notes': wine.get('tasting_notes'),
                        'reason': wine_data.get('reason', ''),
                        'rank': int(rank) if rank is not None else len(validated['wines']) + 1,
                        'best': wine_data.get('best', False)
                    }
                    validated['wines'].append(enriched_wine)
            
            # Sort wines by rank (1, 2, 3, ...) to ensure correct order
            validated['wines'].sort(key=lambda w: w.get('rank', 999))
            
            # Remove duplicates by ID (keep first occurrence with lower rank)
            seen_ids = set()
            unique_wines = []
            for wine in validated['wines']:
                wine_id = wine.get('id')
                if wine_id and wine_id not in seen_ids:
                    seen_ids.add(wine_id)
                    unique_wines.append(wine)
            validated['wines'] = unique_wines
            
            # Log how many wines were ranked
            if len(validated['wines']) > 0:
                logger.info(f"Single mode: Ranked {len(validated['wines'])} wines (rank 1 to {len(validated['wines'])})")
            else:
                logger.warning("Single mode: No wines found in model response")
            
            # Validate and prioritize featured wines if appropriate (SINGLE MODE ONLY)
            # Note: With full ranking, featured wines should already be included by the model if valid
            # We only ensure that if they're included, they have appropriate priority
            if featured_wines and journey_preference == 'single':
                validated_wine_ids = [w.get('id') for w in validated['wines']]
                
                # Check which featured wines are already in the ranking
                for featured_id in featured_wines:
                    if featured_id in validated_wine_ids:
                        # Featured wine already included - if it has rank 1, ensure it has best=true
                        featured_wine = next((w for w in validated['wines'] if w.get('id') == featured_id), None)
                        if featured_wine:
                            featured_rank = featured_wine.get('rank', 999)
                            # If featured wine is rank 1, ensure it has best=true
                            if featured_rank == 1 and not featured_wine.get('best'):
                                # Remove best from all wines
                                for w in validated['wines']:
                                    if w.get('best'):
                                        w['best'] = False
                                featured_wine['best'] = True
                                logger.info(f"Featured wine {featured_id} is rank 1, setting as best=true")
                            elif featured_rank == 1 and featured_wine.get('best'):
                                # Already correct, just log
                                logger.info(f"Featured wine {featured_id} is rank 1 with best=true (correct)")
                    else:
                        # Featured wine not included - the model didn't rank it, likely because it doesn't fit parameters
                        # We don't force it into the ranking to maintain model integrity
                        logger.info(f"Featured wine {featured_id} not included in ranking (model decision - likely doesn't fit parameters)")
            
            # Ensure exactly one wine has best=true (the one with rank 1)
            wines_with_best = [w for w in validated['wines'] if w.get('best') is True]
            rank_1_wine = next((w for w in validated['wines'] if w.get('rank') == 1), None)
            
            if rank_1_wine:
                # Ensure rank 1 wine has best=true
                if not rank_1_wine.get('best'):
                    # Remove best from all wines first
                    for w in validated['wines']:
                        w['best'] = False
                    rank_1_wine['best'] = True
                    logger.info("Single mode: Set rank 1 wine as best=true")
            elif len(wines_with_best) == 0:
                # If no wine marked as best, mark the first one (rank 1 or first in list)
                if validated['wines']:
                    validated['wines'][0]['best'] = True
                    logger.info("Single mode: No wine marked as best, marking first wine as best")
            elif len(wines_with_best) > 1:
                # If multiple wines marked as best, keep only rank 1 (or first featured)
                featured_with_best = [w for w in validated['wines'] if w.get('best') and w.get('id') in (featured_wines or [])]
                if featured_with_best:
                    # Keep only the first featured wine as best
                    for wine in validated['wines']:
                        if wine.get('best') and wine.get('id') != featured_with_best[0].get('id'):
                            wine['best'] = False
                elif rank_1_wine:
                    # Keep only rank 1 as best
                    for wine in validated['wines']:
                        if wine.get('best') and wine.get('rank') != 1:
                            wine['best'] = False
                else:
                    # Keep only the first wine as best
                    for i, wine in enumerate(validated['wines']):
                        if wine.get('best') and i > 0:
                            wine['best'] = False
                logger.warning("Single mode: Multiple wines marked as best, keeping only rank 1 or first featured")
            
        # Final validation: ensure we have minimum required proposals
        if journey_preference == 'journey':
            if len(validated['journeys']) < 2:
                logger.warning(
                    f"Journey mode: Only {len(validated['journeys'])} journeys validated, minimum 2 required. "
                    f"Returning empty to trigger fallback."
                )
                return {'wines': [], 'journeys': []}
        else:
            # Accept any number of wines (even 0 or 1) - don't reject based on count
            if len(validated['wines']) == 0:
                # If model returned 0 wines but we have wines in DB, create fallback ranking
                if all_wines:
                    logger.warning(
                        f"Single mode: Model returned 0 wines but {len(all_wines)} wines available in DB. "
                        f"Creating fallback ranking."
                    )
                    # Create fallback ranking: order by price (ascending) and assign ranks
                    sorted_wines = sorted(all_wines, key=lambda w: float(w.get('price', 0)))
                    for idx, wine in enumerate(sorted_wines):
                        validated['wines'].append({
                            'id': wine.get('id'),
                            'name': wine.get('name'),
                            'price': wine.get('price'),
                            'type': wine.get('type'),
                            'region': wine.get('region'),
                            'grape_variety': wine.get('grape_variety'),
                            'vintage': wine.get('vintage'),
                            'description': wine.get('description'),
                            'tasting_notes': wine.get('tasting_notes'),
                            'reason': 'Vino disponibile nella carta.',
                            'rank': idx + 1,
                            'best': idx == 0  # First wine is best
                        })
                    logger.info(f"Created fallback ranking with {len(validated['wines'])} wines")
                else:
                    logger.warning("Single mode: No wines validated and no wines available in DB")
                    return {'wines': [], 'journeys': []}
            elif len(validated['wines']) == 1:
                # Accept single wine - it's valid
                logger.info("Single mode: Only 1 wine ranked, accepting it")
        
        # If no wines found but we have wines in DB, log warning
        if not validated['wines'] and not validated['journeys'] and all_wines:
            logger.warning("Fine-tuned model returned no valid wines, but wines are available in DB")
        
        return validated

