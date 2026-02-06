from typing import TYPE_CHECKING, Generic, TypeVar
from sqlalchemy import select, not_, and_, func
from sqlalchemy.orm import joinedload, selectinload
from .filter import Q, compile_q
from .lookups import split_lookup, apply_lookup
from .joins import resolve_attr_with_joins
from ..session import sync_session_context, async_session_context
from contextlib import contextmanager, asynccontextmanager

M = TypeVar("M")

class QuerySet(Generic[M]):
    def __init__(self, model: type[M], stmt=None):
        self.model = model
        self.stmt = stmt if stmt is not None else select(model)

    def _clone(self, stmt) -> "QuerySet[M]":
        return QuerySet(self.model, stmt)

    def filter(self, /, *args, **lookups) -> "QuerySet[M]":
        stmt = self.stmt
        expressions = []

        # positional args: Q or SQLAlchemy expressions
        for arg in args:
            if isinstance(arg, Q):
                expr, stmt = compile_q(arg, self.model, stmt)
                if expr is not None:
                    expressions.append(expr)
            else:
                expressions.append(arg)

        # kwargs lookups
        for key, value in lookups.items():
            path, lookup = split_lookup(key)
            col, stmt = resolve_attr_with_joins(self.model, stmt, path)
            expressions.append(apply_lookup(col, lookup, value))

        if expressions:
            stmt = stmt.where(and_(*expressions))
        return self._clone(stmt)

    def exclude(self, /, *args, **lookups) -> "QuerySet[M]":
        stmt = self.stmt
        expressions = []

        for arg in args:
            if isinstance(arg, Q):
                expr, stmt = compile_q(arg, self.model, stmt)
                if expr is not None:
                    expressions.append(expr)
            else:
                expressions.append(arg)

        for key, value in lookups.items():
            path, lookup = split_lookup(key)
            col, stmt = resolve_attr_with_joins(self.model, stmt, path)
            expressions.append(apply_lookup(col, lookup, value))

        if expressions:
            stmt = stmt.where(not_(and_(*expressions)))
        return self._clone(stmt)

    def order_by(self, *fields: str) -> "QuerySet[M]":
        stmt = self.stmt
        clauses = []
        for f in fields:
            desc = f.startswith("-")
            name = f[1:] if desc else f
            col = getattr(self.model, name)
            clauses.append(col.desc() if desc else col.asc())
        return self._clone(stmt.order_by(*clauses))

    def distinct(self) -> "QuerySet[M]":
        return self._clone(self.stmt.distinct())

    def select_related(self, *rels: str) -> "QuerySet[M]":
        """
        Django select_related -> joinedload
        rels: "user", "user.profile" etc.
        """
        opts = []
        for r in rels:
            parts = r.split(".")
            opt = joinedload(getattr(self.model, parts[0]))
            for p in parts[1:]:
                opt = opt.joinedload(p)
            opts.append(opt)
        return self._clone(self.stmt.options(*opts))

    def prefetch_related(self, *rels: str) -> "QuerySet[M]":
        """
        Django prefetch_related -> selectinload
        """
        opts = []
        for r in rels:
            parts = r.split(".")
            opt = selectinload(getattr(self.model, parts[0]))
            for p in parts[1:]:
                opt = opt.selectinload(p)
            opts.append(opt)
        return self._clone(self.stmt.options(*opts))

    # Sync execution

    @contextmanager
    def _sync_execute(self, stmt=None, **opt):
        with sync_session_context(**opt) as session:
            if stmt is None:
                stmt = self.stmt
            yield session.execute(stmt)

    def all(self, **opt) -> list[M]:
        with self._sync_execute(**opt) as res:
            return res.scalars().one()

    def first(self, **opt) -> M | None:
        with self._sync_execute(self.stmt.limit(1), **opt) as res:
            return res.scalars().first()

    def one(self, **opt) -> M:
        with self._sync_execute(**opt) as res:
            return res.scalar_one()

    def get(self, **lookups) -> M:
        with self.filter(**lookups)._sync_execute() as res:
            return res.scalar_one()

    def get_or_none(self, **lookups) -> M | None:
        with self.filter(**lookups)._sync_execute() as res:
            return res.scalar_one_or_none()

    def count(self) -> int:
        with self._sync_execute(self.stmt.with_only_columns(func.count()).order_by(None)) as res:
            return int(res.scalar_one())
        
    def exists(self) -> bool:
        return self.count() > 0

    # Async execution
    @asynccontextmanager
    async def _async_execute(self, stmt=None, **opt):
        async with async_session_context(**opt) as session:
            if stmt is None:
                stmt = self.stmt
            yield await session.execute(stmt)

    async def aall(self, **opt) -> list[M]:
        async with self._async_execute(**opt) as res:
            return res.scalars().all()

    async def afirst(self, **opt) -> M | None:
        async with self._async_execute(self.stmt.limit(1), **opt) as res:
            return res.scalars().first()

    async def aone(self, **opt) -> M:
        async with self._async_execute(**opt) as res:
            return res.scalar_one()

    async def aget(self, **lookups) -> M | None:
        async with self.filter(**lookups)._async_execute() as res:
            return res.scalar_one()

    async def aget_or_none(self, **lookups) -> M | None:
        async with self.filter(**lookups)._async_execute() as res:
            return res.scalar_one_or_none()

    async def acount(self) -> int:
        async with self._async_execute(self.stmt.with_only_columns(func.count()).order_by(None)) as res:
            return int(res.scalar_one())

    async def aexists(self) -> bool:
        return await self.acount() > 0
