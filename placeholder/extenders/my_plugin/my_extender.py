"""Example Extender implementation."""

from typing import Any

from mloda.core.abstract_plugins.function_extender import Extender, ExtenderHook


class MyExtender(Extender):
    """Example Extender. Observability extenders can pass False for warning-only failures."""

    def __init__(self, raise_on_error: bool = True) -> None:
        self.raise_on_error = raise_on_error

    def wraps(self) -> set[ExtenderHook]:
        """Return the set of hooks this extender wraps."""
        return set()

    def __call__(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute the wrapped function without modification."""
        return func(*args, **kwargs)
