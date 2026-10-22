"""Complete bounded permutations of uploaded files, without omission or repetition."""

import re


def single_line(value):
    if isinstance(value, str) and any(char in value for char in "\r\n\u2028\u2029"):
        raise ValueError("upload order must be one line")
    return value


def ordered_indices(value, count):
    """Read an already whitespace-normalized optional field from a strict input model."""
    if type(count) is not int or not 1 <= count <= 5:
        raise ValueError("upload count limit")
    expected = list(range(1, count + 1))
    if value is None:
        return expected
    if not isinstance(value, str) or not 1 <= len(value) <= 32:
        raise ValueError("invalid upload order")
    single_line(value)
    if not re.fullmatch(r"\d(?:[ \t]*[,،][ \t]*\d|[ \t]+\d)*", value):
        raise ValueError("list upload numbers separated by commas or spaces")
    result = [int(number) for number in re.split(r"[,، \t]+", value)]
    if sorted(result) != expected:
        raise ValueError("use each upload exactly once")
    return result
