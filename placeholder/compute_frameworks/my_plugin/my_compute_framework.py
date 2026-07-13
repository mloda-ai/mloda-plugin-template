"""Example ComputeFramework implementation."""

from uuid import UUID, uuid4

from mloda.core.abstract_plugins.components.parallelization_modes import ParallelizationMode
from mloda.core.abstract_plugins.function_extender import Extender
from mloda.provider import ComputeFramework


class MyComputeFramework(ComputeFramework):
    """Example ComputeFramework - rename and customize for your use case."""

    def __init__(
        self,
        mode: ParallelizationMode = ParallelizationMode.SYNC,
        children_if_root: frozenset[UUID] = frozenset(),
        uuid: UUID | None = None,
        function_extender: set[Extender] | None = None,
    ) -> None:
        """Initialize with default values for minimal instantiation."""
        # uuid defaults to None, not uuid4(): a default is evaluated once, so every
        # instance would otherwise share one id.
        super().__init__(mode, children_if_root, uuid or uuid4(), function_extender)
