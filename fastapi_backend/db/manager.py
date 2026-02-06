from typing import TYPE_CHECKING, Generic
from .queryset.queryset import QuerySet, M
from .session import async_session_context, sync_session_context


class Manager(Generic[M]):
    def __init__(self, model: type[M]):
        self.model = model
        self.stmt = None

    def get_queryset(self):
        return QuerySet(self.model)

    def filter(self, *args, **kwargs) -> "QuerySet[M]":
        return self.get_queryset().filter(*args, **kwargs)

    def prefetch_related(self, *rels) -> "QuerySet[M]":
        return self.get_queryset().prefetch_related(*rels)

    def select_related(self, *rels) -> "QuerySet[M]":
        return self.get_queryset().select_related(*rels)

    def all(self) -> "list[M]":
        return self.get_queryset().all()

    def get(self, **lookups) -> "M":
        return self.get_queryset().get(**lookups)

    def get_or_none(self, **lookups) -> "M | None":
        return self.get_queryset().get_or_none(**lookups)

    def create(self, **payload) -> "M":
        with sync_session_context() as session:
            instance = self.model(**payload)
            session.add(instance)
            session.commit()
            session.flush()
            return instance

    async def aall(self) -> list["M"]:
        return await self.get_queryset().aall()

    async def aget(self, **lookups) -> "M":
        return await self.get_queryset().aget(**lookups)

    async def aget_or_none(self, **lookups) -> "M | None":
        return await self.get_queryset().aget_or_none(**lookups)

    async def acreate(self, **payload) -> "M":
        async with async_session_context() as session:
            instance = self.model(**payload)
            session.add(instance)
            await session.commit()
            await session.flush()
            return instance
