"""
Token counting utilities for LLM integration.

This module provides functions for estimating token counts
for text using various encoding schemes used by LLMs.
"""

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

def estimate_tokens(text, encoding_name="cl100k_base"):
    """
    Estimate the number of tokens in a text string.
    
    Args:
        text (str): The text to estimate tokens for
        encoding_name (str): The encoding to use (default: cl100k_base for GPT-4/ChatGPT)
        
    Returns:
        int: The estimated number of tokens, or None if estimation failed
    """
    if not TIKTOKEN_AVAILABLE:
        # Fallback to character-based approximation when tiktoken not available
        if text:
            # Rough approximation: ~4 characters per token for English text
            return len(text) // 4
        return 0
        
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(text))
        return num_tokens
    except Exception:
        # If encoding fails, fall back to character-based approximation
        if text:
            return len(text) // 4
        return 0

def get_available_encodings():
    """
    Get a list of available tiktoken encodings.
    
    Returns:
        list: Available encoding names, or empty list if tiktoken not available
    """
    if not TIKTOKEN_AVAILABLE:
        return []
        
    try:
        return tiktoken.list_encoding_names()
    except Exception:
        return []
        
def format_token_count(count):
    """
    Format token count for display with appropriate units.
    
    Args:
        count (int): The token count to format
        
    Returns:
        str: Formatted token count (e.g., "1.5K tokens")
    """
    if count is None:
        return "Unknown"
        
    if count < 1000:
        return f"{count} tokens"
    elif count < 10000:
        return f"{count/1000:.1f}K tokens"
    else:
        return f"{count/1000:.0f}K tokens"

def get_model_context_limits():
    """
    Return a dictionary of context limits for common LLM models.
    
    Returns:
        dict: Model names mapped to their token limits
    """
    return {
        "GPT-3.5": 16384,
        "GPT-4": 8192,
        "GPT-4-32K": 32768,
        "Claude-2": 100000,
        "Claude-Instant": 100000,
        "Gemini-Pro": 32768,
    }
