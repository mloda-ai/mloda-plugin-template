"""Tests for the MyExtender example plugin."""

from placeholder.extenders.my_plugin.my_extender import MyExtender


def test_my_extender_is_an_extender() -> None:
    """The example class participates in the Extender plugin hierarchy."""
    assert any(base.__name__ == "Extender" for base in MyExtender.__mro__)


def test_my_extender_instantiates() -> None:
    """The example extender can be instantiated without arguments."""
    extender = MyExtender()
    assert extender is not None


def test_wraps_returns_set_of_hooks() -> None:
    """wraps() returns the hook values this extender intercepts."""
    extender = MyExtender()

    hooks = extender.wraps()

    assert isinstance(hooks, set)
    # The template extender wraps nothing by default. A real extender
    # should return the ExtenderHook values it intercepts.
    assert hooks == set()


def test_call_invokes_wrapped_callable_and_returns_result() -> None:
    """__call__ passes through to the wrapped callable and result."""
    extender = MyExtender()
    observed_calls = []

    def wrapped(*args, **kwargs):
        observed_calls.append((args, kwargs))
        return "sentinel-result"

    result = extender(wrapped, 1, 2, option=True)

    assert result == "sentinel-result"
    assert observed_calls == [((1, 2), {"option": True})]
