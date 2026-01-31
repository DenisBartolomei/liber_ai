"""
Resilience Service for LIBER
Implements circuit breakers, health checks, and caching utilities
"""
import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from pybreaker import CircuitBreaker, CircuitBreakerError
from flask import current_app

logger = logging.getLogger(__name__)


# Circuit Breakers for external services
# fail_max: number of failures before opening the circuit
# reset_timeout: seconds to wait before trying again

openai_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name="openai"
)

qdrant_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="qdrant"
)

supabase_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=30,
    name="supabase"
)


def with_circuit_breaker(breaker: CircuitBreaker, fallback_value: Any = None):
    """
    Decorator to wrap a function with circuit breaker protection.

    Args:
        breaker: The circuit breaker instance to use
        fallback_value: Value to return when circuit is open (optional)

    Usage:
        @with_circuit_breaker(openai_breaker)
        def call_openai(prompt):
            return client.chat.completions.create(...)
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except CircuitBreakerError as e:
                logger.warning(
                    f"Circuit breaker '{breaker.name}' is OPEN. "
                    f"Service unavailable. Failures: {breaker.fail_counter}"
                )
                if fallback_value is not None:
                    return fallback_value
                raise ServiceUnavailableError(
                    f"Service '{breaker.name}' is temporarily unavailable. Please try again later."
                ) from e
        return wrapper
    return decorator


class ServiceUnavailableError(Exception):
    """Raised when a service is unavailable due to circuit breaker"""
    pass


class HealthCheckService:
    """
    Service for checking health of all external dependencies.
    """

    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check PostgreSQL database connectivity."""
        start_time = time.time()
        try:
            from app import db
            # Execute a simple query to verify connection
            db.session.execute(db.text('SELECT 1'))
            latency_ms = (time.time() - start_time) * 1000
            return {
                'status': 'healthy',
                'latency_ms': round(latency_ms, 2)
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'latency_ms': round(latency_ms, 2)
            }

    @staticmethod
    def check_qdrant() -> Dict[str, Any]:
        """Check Qdrant vector database connectivity."""
        start_time = time.time()
        try:
            from qdrant_client import QdrantClient

            host = current_app.config.get('QDRANT_HOST', 'localhost')
            port = current_app.config.get('QDRANT_PORT', 6333)
            api_key = current_app.config.get('QDRANT_API_KEY')

            # Build client kwargs
            client_kwargs = {'host': host, 'port': port, 'timeout': 5}
            if api_key:
                client_kwargs['api_key'] = api_key

            client = QdrantClient(**client_kwargs)
            # Get collections to verify connection
            collections = client.get_collections()
            latency_ms = (time.time() - start_time) * 1000
            return {
                'status': 'healthy',
                'collections_count': len(collections.collections),
                'latency_ms': round(latency_ms, 2)
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Qdrant health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'latency_ms': round(latency_ms, 2)
            }

    @staticmethod
    def check_openai() -> Dict[str, Any]:
        """Check OpenAI API key validity (lightweight check)."""
        start_time = time.time()
        try:
            api_key = current_app.config.get('OPENAI_API_KEY', '')
            if not api_key or not api_key.strip():
                return {
                    'status': 'unhealthy',
                    'error': 'API key not configured'
                }

            # Validate key format (sk-... or sk-proj-...)
            if not api_key.startswith('sk-'):
                return {
                    'status': 'unhealthy',
                    'error': 'Invalid API key format'
                }

            latency_ms = (time.time() - start_time) * 1000
            return {
                'status': 'healthy',
                'key_configured': True,
                'latency_ms': round(latency_ms, 2)
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"OpenAI health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'latency_ms': round(latency_ms, 2)
            }

    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity (if configured)."""
        start_time = time.time()
        try:
            redis_url = current_app.config.get('REDIS_URL')
            if not redis_url:
                return {
                    'status': 'skipped',
                    'message': 'Redis not configured'
                }

            import redis
            client = redis.from_url(redis_url, socket_timeout=2)
            client.ping()
            latency_ms = (time.time() - start_time) * 1000
            return {
                'status': 'healthy',
                'latency_ms': round(latency_ms, 2)
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"Redis health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'latency_ms': round(latency_ms, 2)
            }

    @staticmethod
    def check_circuit_breakers() -> Dict[str, Any]:
        """Check status of all circuit breakers."""
        return {
            'openai': {
                'state': openai_breaker.current_state,
                'fail_counter': openai_breaker.fail_counter
            },
            'qdrant': {
                'state': qdrant_breaker.current_state,
                'fail_counter': qdrant_breaker.fail_counter
            },
            'supabase': {
                'state': supabase_breaker.current_state,
                'fail_counter': supabase_breaker.fail_counter
            }
        }

    @classmethod
    def get_full_health(cls) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all services.

        Returns:
            Dict with overall status and individual service checks
        """
        checks = {
            'database': cls.check_database(),
            'qdrant': cls.check_qdrant(),
            'openai': cls.check_openai(),
            'redis': cls.check_redis(),
            'circuit_breakers': cls.check_circuit_breakers()
        }

        # Determine overall status
        critical_services = ['database', 'qdrant', 'openai']
        all_critical_healthy = all(
            checks[svc].get('status') == 'healthy'
            for svc in critical_services
        )

        # Check if any circuit breaker is open
        any_circuit_open = any(
            cb.get('state') == 'open'
            for cb in checks['circuit_breakers'].values()
        )

        if all_critical_healthy and not any_circuit_open:
            overall_status = 'healthy'
        elif all_critical_healthy:
            overall_status = 'degraded'  # Circuit breaker open but services responding
        else:
            overall_status = 'unhealthy'

        return {
            'status': overall_status,
            'timestamp': time.time(),
            'checks': checks
        }


class CacheService:
    """
    Utility service for application-level caching.
    Falls back to in-memory cache if Redis is not available.
    """

    _memory_cache: Dict[str, Any] = {}
    _cache_expiry: Dict[str, float] = {}

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get a value from cache."""
        try:
            cache = current_app.extensions.get('cache')
            if cache:
                return cache.get(key)
        except Exception:
            pass

        # Fallback to memory cache
        if key in cls._memory_cache:
            if time.time() < cls._cache_expiry.get(key, 0):
                return cls._memory_cache[key]
            else:
                # Expired
                del cls._memory_cache[key]
                del cls._cache_expiry[key]
        return None

    @classmethod
    def set(cls, key: str, value: Any, timeout: int = 300) -> bool:
        """Set a value in cache with timeout (default 5 minutes)."""
        try:
            cache = current_app.extensions.get('cache')
            if cache:
                cache.set(key, value, timeout=timeout)
                return True
        except Exception:
            pass

        # Fallback to memory cache
        cls._memory_cache[key] = value
        cls._cache_expiry[key] = time.time() + timeout
        return True

    @classmethod
    def delete(cls, key: str) -> bool:
        """Delete a value from cache."""
        try:
            cache = current_app.extensions.get('cache')
            if cache:
                cache.delete(key)
        except Exception:
            pass

        # Also clear from memory cache
        cls._memory_cache.pop(key, None)
        cls._cache_expiry.pop(key, None)
        return True

    @classmethod
    def clear_pattern(cls, pattern: str) -> int:
        """Clear all cache keys matching a pattern (e.g., 'venue:*')."""
        cleared = 0

        # Clear from memory cache
        keys_to_delete = [
            k for k in cls._memory_cache.keys()
            if k.startswith(pattern.replace('*', ''))
        ]
        for key in keys_to_delete:
            cls.delete(key)
            cleared += 1

        return cleared
