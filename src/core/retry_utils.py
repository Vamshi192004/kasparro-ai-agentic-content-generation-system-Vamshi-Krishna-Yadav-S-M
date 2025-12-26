"""
Retry utilities for robust error handling with exponential backoff.
"""
import time
import functools
from typing import Callable, Type, Tuple, Optional
from core.logger import get_logger

logger = get_logger(__name__)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""
    pass


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator that retries a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to prevent thundering herd
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import random
            
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries. "
                            f"Last error: {str(e)}"
                        )
                        raise RetryExhaustedError(
                            f"Function {func.__name__} failed after {max_retries} retries"
                        ) from e
                    
                    # Calculate delay with exponential backoff
                    delay = initial_delay * (exponential_base ** attempt)
                    
                    # Add jitter to prevent thundering herd problem
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay:.2f}s. Error: {str(e)}"
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


def is_retryable_error(exception: Exception) -> bool:
    """
    Determine if an error is retryable.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the error should be retried, False otherwise
    """
    # Network/API errors that should be retried
    retryable_messages = [
        "rate limit",
        "timeout",
        "connection",
        "network",
        "503",
        "502",
        "500",
        "429",
        "quota exceeded"
    ]
    
    error_message = str(exception).lower()
    return any(msg in error_message for msg in retryable_messages)


class RetryConfig:
    """Configuration for retry behavior."""
    
    # Default retry settings
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_INITIAL_DELAY = 1.0
    DEFAULT_EXPONENTIAL_BASE = 2.0
    
    # Agent-specific retry settings
    PARSER_MAX_RETRIES = 3
    QGEN_MAX_RETRIES = 5  # Question generation may need more retries
    PAGE_AGENT_MAX_RETRIES = 3
    REVIEWER_MAX_RETRIES = 2
    
    @classmethod
    def get_agent_config(cls, agent_name: str) -> dict:
        """
        Get retry configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary with retry configuration
        """
        configs = {
            "parser": {
                "max_retries": cls.PARSER_MAX_RETRIES,
                "initial_delay": 1.0,
                "exponential_base": 2.0
            },
            "qgen": {
                "max_retries": cls.QGEN_MAX_RETRIES,
                "initial_delay": 1.0,
                "exponential_base": 2.0
            },
            "page_agent": {
                "max_retries": cls.PAGE_AGENT_MAX_RETRIES,
                "initial_delay": 1.0,
                "exponential_base": 2.0
            },
            "reviewer": {
                "max_retries": cls.REVIEWER_MAX_RETRIES,
                "initial_delay": 0.5,
                "exponential_base": 2.0
            }
        }
        
        return configs.get(agent_name, {
            "max_retries": cls.DEFAULT_MAX_RETRIES,
            "initial_delay": cls.DEFAULT_INITIAL_DELAY,
            "exponential_base": cls.DEFAULT_EXPONENTIAL_BASE
        })
