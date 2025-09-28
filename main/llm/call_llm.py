"""
Retry mechanism for LLM calls with exponential backoff.

This module provides retry functionality for OpenRouter LLM calls to handle rate limiting
with exponential backoff delays of 3s, 6s, 9s, and 12s.

Using the call_llm_with_retry function:
   ```python
   from main.llm.call_llm import call_llm_with_retry
   
   # Instead of: result = agent.run_sync(prompt)
   result = call_llm_with_retry(agent.run_sync, prompt)
   llm_output = result.output
   ```

The retry mechanism automatically handles RateLimitError exceptions and retries with
the specified backoff delays. Other exceptions are raised immediately without retry.
"""

import time
from typing import Callable, TypeVar
import logging
from openai import RateLimitError

# Set up logging
logger = logging.getLogger(__name__)

T = TypeVar('T')


def call_llm_with_retry(
    agent_run_func: Callable[..., T],
    *args,
    max_retries: int = 4,
    backoff_delays: list[float] = [3.0, 6.0, 9.0, 12.0],
    **kwargs
) -> T:
    """
    Call an LLM agent with retry logic and exponential backoff.
    
    Args:
        agent_run_func: The agent.run_sync or agent.run function to call
        *args: Arguments to pass to the agent run function
        max_retries: Maximum number of retry attempts (default: 4)
        backoff_delays: List of delays in seconds for each retry attempt (default: [3, 6, 9, 12])
        **kwargs: Keyword arguments to pass to the agent run function
    
    Returns:
        The result of the agent run function
    
    Raises:
        RateLimitError: If max retries are exceeded
        Other exceptions: Any non-rate-limit errors are raised immediately
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return agent_run_func(*args, **kwargs)
        except RateLimitError as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for LLM call")
                raise e
            
            delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
            logger.warning(
                f"Rate limit error (attempt {attempt + 1}/{max_retries + 1}). "
                f"Retrying in {delay} seconds..."
            )
            time.sleep(delay)
        except Exception as e:
            # Don't retry for non-rate-limit errors
            logger.error(f"Non-retryable error in LLM call: {e}")
            raise e
    
    # This should never be reached, but just in case
    raise last_exception

