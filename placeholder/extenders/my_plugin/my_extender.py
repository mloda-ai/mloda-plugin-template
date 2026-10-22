"""Example Extender implementation."""

from typing import Any

from mloda.steward import Extender, ExtenderHook


class MyExtender(Extender):
    """Example Extender - rename and customize for your use case.

    For lifecycle hooks (on_plan_start, on_plan_complete, on_run_start, on_run_complete) see
    https://github.com/mloda-ai/mloda-registry/blob/main/docs/guides/11-create-extender.md
    """

    def wraps(self) -> set[ExtenderHook]:
        """Return the set of hooks this extender wraps."""
        return set()

    def __call__(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute the wrapped function without modification."""
        return func(*args, **kwargs)
