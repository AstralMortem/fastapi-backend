import operator as op
from typing import Any
from sqlalchemy import func


def _iexact(a, b):
    return op.eq(func.lower(a), str(b).lower)


def _contains(a, b):
    return a.contains(b)


def _icontains(a, b):
    return _contains(func.lower(a), str(b).lower())


def _in(a, b):
    if b is None:
        return a.in_([])
    return a.in_(list(b))


def _isnull(a, b):
    return op.is_(a, None) if b else op.is_not(a, None)


_LOOKUP_SUFFIXES: dict[str, callable] = {
    "exact": op.eq,
    "iexact": _iexact,
    "contains": _contains,
    "icontains": _icontains,
    "in": _in,
    "lt": op.lt,
    "lte": op.le,
    "gt": op.gt,
    "gte": op.ge,
    "isnull": _isnull,
}


def split_lookup(key: str) -> tuple[list[str], str]:
    """
    "user__email__icontains" -> (["user", "email"], "icontains")
    "name" -> (["name"], "exact")
    """
    parts = key.split("__")
    if parts[-1] in _LOOKUP_SUFFIXES:
        return parts[:-1], parts[-1]
    return parts, "exact"


def apply_lookup(col, lookup: str, value: Any):
    func = _LOOKUP_SUFFIXES.get(lookup, None)
    if func is None:
        raise ValueError(f"Unsupported lookup: {lookup}")
    try:
        return func(col, value)
    except Exception as e:
        raise ValueError(f"Invalid lookup value: {e}")
