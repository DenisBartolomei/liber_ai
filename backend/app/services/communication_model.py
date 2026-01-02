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
            gathered_info: Preferences (wine_type, journey_preference, budget)
            history: Conversation history
            user_message: Current user message
            
        Returns:
            Natural language message string
        """
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
            # Call communication model - concise responses only
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=200  # Concise responses: only wine names + brief reasons
            )
            
            message = response.choices[0].message.content
            
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

