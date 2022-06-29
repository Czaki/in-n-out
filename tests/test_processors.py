from typing import Optional, Sequence

import pytest

from in_n_out import get_processor, processor, set_processors
from in_n_out._processors import clear_processor
from in_n_out._store import _STORE


@pytest.mark.parametrize(
    "type, provide, ask_type, expect",
    [
        (int, lambda: 1, int, 1),  # processor can be a function
        (int, 1, int, 1),  # or a constant value
        (Sequence, [], list, []),  # we can ask for a subclass of a provided types
    ],
)
def test_set_processors(type, provide, ask_type, expect):
    """Test that we can set processor as function or constant, and get it back."""
    assert not get_processor(ask_type)
    with set_processors({type: provide}):
        assert get_processor(ask_type)() == expect
    assert not get_processor(ask_type)  # make sure context manager cleaned up


def test_set_processors_cleanup():
    """Test that we can set processors in contexts, and cleanup"""
    assert not get_processor(int)

    with set_processors({int: 1}):
        assert get_processor(int)() == 1
        with pytest.raises(ValueError, match="already has a processor and clobber is"):
            set_processors({int: 2})
        with set_processors({int: 2}, clobber=True):
            assert get_processor(int)() == 2
        assert get_processor(int)() == 1

    assert not get_processor(int)


def test_processor_decorator():
    """Test the @processor decorator."""
    assert not get_processor(int)

    @processor
    def processes_int(x: int):
        ...

    assert get_processor(int) is processes_int

    clear_processor(int)
    assert not get_processor(int)

    with pytest.warns(UserWarning, match="No processor was registered"):
        clear_processor(int, warn_missing=True)


def test_optional_processors():
    """Test providing & getting Optional[type]."""
    assert not get_processor(Optional[int])
    assert not get_processor(str)

    @processor
    def processes_int(x: int):
        return 1

    @processor
    def processes_string(x: str):
        ...

    # we don't have a processor guaranteed to take an int
    # assert not get_processor(int)
    # just an optional one
    assert get_processor(Optional[int]) is processes_int

    # but processes_string takes a string
    assert get_processor(str) is processes_string
    # which means it also provides an Optional[str]
    assert get_processor(Optional[str]) is processes_string

    assert get_processor(int) is processes_int
    # the definite processor takes precedence
    # TODO: consider this...
    assert get_processor(Optional[int]) is processes_int

    # TODO: consider this
    # when clearing `int` would get rid of `processes_int` AND `processes_int`
    # but clearing Optional[int] would only get rid of `processes_int`
    assert clear_processor(int) is processes_int
    assert clear_processor(str) is processes_string

    # all clear
    assert not _STORE.processors


def test_unlikely_processor():
    with pytest.warns(UserWarning, match="has no argument type hints"):

        @processor
        def provides_int():
            ...
