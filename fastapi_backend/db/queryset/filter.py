from dataclasses import dataclass, field
from sqlalchemy import or_, and_, not_
from typing import Any, Mapping
from .lookups import apply_lookup, split_lookup
from .joins import resolve_attr_with_joins


@dataclass(frozen=True)
class Q:
    """
    Django-like composable filters.

    Q(a=1) & (Q(b=2) | ~Q(c=3))
    Q(user__email__icontains="gmail")
    You can also pass raw SQLAlchemy expressions inside: Q(User.id > 5)
    """

    children: tuple[Any, ...] = field(default_factory=tuple)
    connector: str = "AND"  # AND / OR
    negated: bool = False

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "children", (*args, kwargs))
        object.__setattr__(self, "connector", "AND")
        object.__setattr__(self, "negated", False)

    @classmethod
    def _new(cls, *, children: tuple[Any, ...], connector: str, negated: bool) -> "Q":
        q = cls.__new__(cls)
        object.__setattr__(q, "children", children)
        object.__setattr__(q, "connector", connector)
        object.__setattr__(q, "negated", negated)
        return q

    def _combine(self, other: "Q", connector: str) -> "Q":
        return Q._new(children=(self, other), connector=connector, negated=False)

    def __and__(self, other: "Q") -> "Q":
        return self._combine(other, "AND")

    def __or__(self, other: "Q") -> "Q":
        return self._combine(other, "OR")

    def __invert__(self) -> "Q":
        return Q._new(
            children=self.children, connector=self.connector, negated=not self.negated
        )


def compile_q(q: Q, model, stmt):
    """
    Convert Q tree into a SQLAlchemy boolean expression,
    mutating stmt by adding required JOINs for related paths.
    """
    expressions = []

    for child in q.children:
        # Nested Q
        if isinstance(child, Q):
            expr, stmt = compile_q(child, model, stmt)
            if expr is not None:
                expressions.append(expr)
            continue

        # kwargs dict
        if isinstance(child, Mapping):
            for key, value in child.items():
                path, lookup = split_lookup(key)
                col, stmt = resolve_attr_with_joins(model, stmt, path)
                expressions.append(apply_lookup(col, lookup, value))
            continue

        # raw SQLAlchemy expression
        expressions.append(child)

    if not expressions:
        expr = None
    elif q.connector == "AND":
        expr = and_(*expressions)
    else:
        expr = or_(*expressions)

    if expr is not None and q.negated:
        expr = not_(expr)

    return expr, stmt
