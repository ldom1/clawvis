"""Role-Based Access Control (RBAC) for LabOS agent capabilities."""

import logging
from functools import wraps
from typing import Any, Callable, Optional

from fastapi import HTTPException, status

from .identity import AgentIdentity, current_identity

logger = logging.getLogger(__name__)


class UnauthorizedError(Exception):
    def __init__(self, agent: AgentIdentity, required: str):
        self.agent = agent
        self.required = required
        super().__init__(f"Agent {agent.agent_id} lacks capability: {required}")


def require_capability(capability: str):
    """Decorator: raise UnauthorizedError if agent lacks capability."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            identity = current_identity()
            if not identity.has_capability(capability):
                logger.warning(f"Access denied: {identity.agent_id} tried {capability}")
                raise UnauthorizedError(identity, capability)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_capability(capabilities: list):
    """Decorator: raise UnauthorizedError if agent lacks all listed capabilities."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            identity = current_identity()
            if not any(identity.has_capability(c) for c in capabilities):
                logger.warning(f"Access denied: {identity.agent_id} lacks any of {capabilities}")
                raise UnauthorizedError(identity, f"any of {capabilities}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def fastapi_require_capability(capability: str):
    """Decorator for FastAPI routes: returns HTTP 403 on access denied."""
    def decorator(func: Callable) -> Callable:
        import asyncio

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            identity = current_identity()
            if not identity.has_capability(capability):
                logger.warning(f"HTTP 403: {identity.agent_id} tried {capability}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing capability: {capability}")
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            identity = current_identity()
            if not identity.has_capability(capability):
                logger.warning(f"HTTP 403: {identity.agent_id} tried {capability}")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing capability: {capability}")
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class RBACContext:
    """Context manager for temporary capability override (testing only)."""

    def __init__(self, override_identity: Optional[AgentIdentity] = None):
        self.override_identity = override_identity
        self.original_identity = None

    def __enter__(self):
        import hub_core.security.identity as ai
        self.original_identity = ai._current_identity
        if self.override_identity:
            ai._current_identity = self.override_identity

    def __exit__(self, exc_type, exc_val, exc_tb):
        import hub_core.security.identity as ai
        ai._current_identity = self.original_identity
