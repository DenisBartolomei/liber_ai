"""
Communication Model Service
Generates natural language message from structured wine selection JSON
"""
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI, APIError, AuthenticationError, RateLimitError
from flask import current_app
from app.prompts.b2c_system import get_communication_prompt

logger = logging.getLogger(__name__)


class CommunicationModelService:
    """
    Service that generates natural language message from structured wine selection.
    """
    
    def __init__(self):
        api_key = current_app.config.get('OPENAI_API_KEY', '')
        
        if not api_key or not api_key.strip():
            logger.error("OPENAI_API_KEY is not configured!")
            raise ValueError("OPENAI_API_KEY non configurata. Contatta l'amministratore del sistema.")
        
        try:
            self.client = OpenAI(api_key=api_key, timeout=30.0)  # 30 second timeout
        except TypeError as e:
            import os
            os.environ['OPENAI_API_KEY'] = api_key
            self.client = OpenAI(timeout=30.0)
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            raise
        
        self.model = current_app.config.get('OPENAI_COMMUNICATION_MODEL', 'gpt-4o-mini')
        self.reasoning_effort = current_app.config.get('OPENAI_REASONING_EFFORT', 'low')
        logger.info(f"CommunicationModelService initialized with model: {self.model}")
    
    def generate_message(
        self,
        venue_name: str,
        sommelier_style: str,
        wine_selection: Dict[str, Any],
        context: Dict,
        gathered_info: Dict,
        history: List[Dict],
        user_message: str
    ) -> str:
        """
        Generate natural language message from structured wine selection.
        
        Args:
            venue_name: Name of the venue
            sommelier_style: Style of sommelier (professional, friendly, expert, playful)
            wine_selection: JSON from FineTunedWineSelector with 'wines' or 'journeys'
            context: Context with dishes, guest_count
            gathered_info: Preferences (wine_type, journey_preference) - budget is NOT included
            history: Conversation history
            user_message: Current user message
            
        Returns:
            Natural language message string
        """
        # Safety check: remove budget if present (wines are already filtered by budget)
        if 'budget' in gathered_info:
            logger.warning("Budget found in gathered_info - removing it (wines already filtered by budget)")
            gathered_info = {k: v for k, v in gathered_info.items() if k != 'budget'}
        
        # Build communication prompt
        system_prompt = get_communication_prompt(
            venue_name=venue_name,
            sommelier_style=sommelier_style,
            wine_selection=wine_selection,
            context=context,
            gathered_info=gathered_info
        )
        
        # Build messages - limit history for speed
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 2 messages only for faster processing)
        for msg in history[-2:]:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Determine max tokens based on mode (journeys need slightly more for 3 paths)
            is_journey_mode = wine_selection.get('journeys') and len(wine_selection.get('journeys', [])) > 0
            max_tokens = 2000 if is_journey_mode else 600
            
            # Detect if model is a reasoning model (gpt-5.x, o1, o3, etc.)
            is_reasoning_model = any(x in self.model.lower() for x in ['gpt-5', 'o1', 'o3'])
            
            # #region agent log
            logger.warning(f"[DEBUG-D] COMM: Calling model={self.model}, is_reasoning={is_reasoning_model}, wines_count={len(wine_selection.get('wines', []))}, journeys_count={len(wine_selection.get('journeys', []))}, max_tokens={max_tokens}, messages_count={len(messages)}")
            # #endregion
            
            # Call communication model - concise responses only
            if is_reasoning_model:
                # Reasoning models (gpt-5.x, o1, o3):
                # - Use max_completion_tokens (not max_tokens)
                # - Use reasoning_effort
                # - No temperature (not supported or not needed)
                # - They use LOTS of tokens for internal "thinking", so increase significantly
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    reasoning_effort=self.reasoning_effort,
                    max_completion_tokens=2000  # Reasoning models need much more for thinking+output
                )
            else:
                # Non-reasoning models (GPT-4.1, gpt-4o-mini, etc.):
                # - Use max_tokens (NOT max_completion_tokens)
                # - Use temperature for natural, engaging communication (0.7 = creative but consistent)
                # - No reasoning_effort (not supported)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7  # Natural, engaging sommelier tone (not too cold, not too random)
                )
            
            message = response.choices[0].message.content
            
            # #region agent log
            logger.warning(f"[DEBUG-D] COMM: Response message_length={len(message) if message else 0}, message_preview={repr(message[:100]) if message else 'None'}, finish_reason={response.choices[0].finish_reason if response.choices else 'N/A'}")
            # #endregion
            
            # Ensure message is not empty or None
            if not message or not message.strip():
                logger.warning("Communication model returned empty message")
                return None  # Return None to trigger fallback
            
            return message.strip()
            
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
            logger.error(f"Unexpected error in generate_message: {e}")
            raise ValueError(f"Si è verificato un errore imprevisto. Riprova.")

