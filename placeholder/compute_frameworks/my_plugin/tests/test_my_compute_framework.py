"""Tests for MyComputeFramework."""

from uuid import uuid4

from placeholder.compute_frameworks.my_plugin import MyComputeFramework
from mloda.provider import ComputeFramework


def test_extends_base() -> None:
    """MyComputeFramework should extend ComputeFramework."""
    assert issubclass(MyComputeFramework, ComputeFramework)


def test_instantiation() -> None:
    """MyComputeFramework should instantiate with no arguments."""
    instance = MyComputeFramework()
    assert instance is not None


def test_default_uuid_is_per_instance() -> None:
    """Each instance gets its own uuid; a uuid4() default would be shared by all."""
    assert MyComputeFramework().uuid != MyComputeFramework().uuid


def test_explicit_uuid_is_respected() -> None:
    """An explicitly passed uuid is not overwritten."""
    given = uuid4()
    assert MyComputeFramework(uuid=given).uuid == given
