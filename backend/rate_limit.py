"""
Rate Limiting Utilities
Implements rate limiting for sensitive endpoints (OTP, login, etc.)
Uses in-memory store for development; Redis recommended for production
"""

import os
import logging
import time
from typing import Dict, Tuple
from threading import Lock

# Configure logger
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter for development.
    For production, use Flask-Limiter with Redis backend.
    """
    
    def __init__(self):
        self._attempts: Dict[str, list] = {}  # {key: [timestamp, timestamp, ...]}
        self._lock = Lock()
    
    def is_allowed(self, key: str, max_attempts: int = 5, window_seconds: int = 300) -> Tuple[bool, Dict]:
        """
        Check if an action is allowed for the given key within rate limit.
        
        Args:
            key: Unique identifier (e.g., email, IP address)
            max_attempts: Maximum attempts allowed in window
            window_seconds: Time window in seconds
        
        Returns:
            (is_allowed: bool, info: dict)
            info contains: remaining, reset_time_seconds
        """
        with self._lock:
            now = time.time()
            
            # Clean up old attempts outside the window
            if key in self._attempts:
                self._attempts[key] = [t for t in self._attempts[key] if now - t < window_seconds]
            else:
                self._attempts[key] = []
            
            attempt_count = len(self._attempts[key])
            remaining = max(0, max_attempts - attempt_count)
            
            if attempt_count < max_attempts:
                # Add new attempt timestamp
                self._attempts[key].append(now)
                
                return True, {
                    'remaining': remaining - 1,
                    'reset_time_seconds': window_seconds,
                    'limit': max_attempts
                }
            else:
                # Rate limit exceeded
                oldest_attempt = self._attempts[key][0]
                reset_time = max(0, window_seconds - (now - oldest_attempt))
                
                return False, {
                    'remaining': 0,
                    'reset_time_seconds': int(reset_time) + 1,
                    'limit': max_attempts,
                    'retry_after': int(reset_time) + 1
                }
    
    def reset(self, key: str):
        """Reset rate limit for a specific key"""
        with self._lock:
            if key in self._attempts:
                del self._attempts[key]
                logger.info(f"Rate limit reset for key: {key}")


# Global rate limiter instance
_rate_limiter = RateLimiter()


def check_rate_limit(key: str, limit_type: str = 'otp') -> Tuple[bool, Dict]:
    """
    Check if request is within rate limit.
    Different limits for different endpoint types.
    
    Args:
        key: Unique identifier (email, phone, IP)
        limit_type: Type of limit ('otp', 'login', 'register', 'default')
    
    Returns:
        (is_allowed, rate_limit_info)
    """
    limits = {
        'otp': (5, 300),           # 5 attempts per 5 minutes
        'login': (10, 600),        # 10 attempts per 10 minutes
        'register': (3, 3600),     # 3 registrations per hour per IP
        'password_reset': (3, 900), # 3 attempts per 15 minutes
        'default': (20, 60),       # Generic 20 per minute
    }
    
    max_attempts, window = limits.get(limit_type, limits['default'])
    allowed, info = _rate_limiter.is_allowed(key, max_attempts, window)
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {limit_type}: {key}")
    
    return allowed, info


def reset_rate_limit(key: str):
    """Reset rate limit for a key (e.g., after successful auth)"""
    _rate_limiter.reset(key)


def get_rate_limit_headers(rate_info: Dict) -> Dict[str, str]:
    """
    Generate HTTP headers for rate limit information.
    
    Returns:
        Dict of headers to add to response
    """
    return {
        'X-RateLimit-Limit': str(rate_info.get('limit', 'N/A')),
        'X-RateLimit-Remaining': str(rate_info.get('remaining', 0)),
        'X-RateLimit-Reset': str(int(time.time()) + rate_info.get('reset_time_seconds', 0))
    }
