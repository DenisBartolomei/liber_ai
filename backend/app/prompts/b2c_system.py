"""
B2C System Prompt Router
Routes to language-specific prompt modules based on the language parameter.
"""
from app.prompts import b2c_system_it, b2c_system_en


def get_b2c_opening_prompt(language='it', **kwargs):
    """
    Route to language-specific opening prompt.

    Args:
        language: 'it' for Italian, 'en' for English (default: 'it')
        **kwargs: Additional arguments passed to the prompt function

    Returns:
        str: The opening prompt in the specified language
    """
    module = b2c_system_it if language == 'it' else b2c_system_en
    return module.get_b2c_opening_prompt(**kwargs)


def get_b2c_system_prompt(language='it', **kwargs):
    """
    Route to language-specific system prompt.

    Args:
        language: 'it' for Italian, 'en' for English (default: 'it')
        **kwargs: Additional arguments passed to the prompt function

    Returns:
        str: The system prompt in the specified language
    """
    module = b2c_system_it if language == 'it' else b2c_system_en
    return module.get_b2c_system_prompt(**kwargs)


def get_finetuned_selection_prompt(language='it', **kwargs):
    """
    Route to language-specific fine-tuned selection prompt.

    Args:
        language: 'it' for Italian, 'en' for English (default: 'it')
        **kwargs: Additional arguments passed to the prompt function

    Returns:
        str: The fine-tuned selection prompt in the specified language
    """
    module = b2c_system_it if language == 'it' else b2c_system_en
    return module.get_finetuned_selection_prompt(**kwargs)


def get_communication_prompt(language='it', **kwargs):
    """
    Route to language-specific communication prompt.

    Args:
        language: 'it' for Italian, 'en' for English (default: 'it')
        **kwargs: Additional arguments passed to the prompt function

    Returns:
        str: The communication prompt in the specified language
    """
    module = b2c_system_it if language == 'it' else b2c_system_en
    return module.get_communication_prompt(**kwargs)


def get_b2c_clarification_prompt(language='it', **kwargs):
    """
    Route to language-specific clarification prompt.

    Args:
        language: 'it' for Italian, 'en' for English (default: 'it')
        **kwargs: Additional arguments passed to the prompt function

    Returns:
        str: The clarification prompt in the specified language
    """
    module = b2c_system_it if language == 'it' else b2c_system_en
    return module.get_b2c_clarification_prompt(**kwargs)


# Re-export the calculate_bottles_needed function from Italian module (language-independent logic)
from app.prompts.b2c_system_it import calculate_bottles_needed

__all__ = [
    'get_b2c_opening_prompt',
    'get_b2c_system_prompt',
    'get_finetuned_selection_prompt',
    'get_communication_prompt',
    'get_b2c_clarification_prompt',
    'calculate_bottles_needed'
]
