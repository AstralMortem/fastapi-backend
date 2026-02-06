from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi_backend.conf import settings
from contextvars import ContextVar
from contextlib import contextmanager, asynccontextmanager
from fastapi import Depends
from typing import Annotated

sync_engine = create_engine(str(settings.DATABASE_URL), pool_pre_ping=True)
async_engine = create_async_engine(str(settings.DATABASE_ASYNC_URL), pool_pre_ping=True)

SyncSessionFactory = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autoflush=False,
)

AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autoflush=False,
)

_sync_session_ctx: ContextVar[Session | None] = ContextVar("sync_session", default=None)

_async_session_ctx: ContextVar[AsyncSession | None] = ContextVar(
    "async_session", default=None
)


def get_sync_session(**local_kw) -> Session:
    session = _sync_session_ctx.get()
    if session is None:
        session = SyncSessionFactory(**local_kw)
        _sync_session_ctx.set(session)
    return session


async def get_async_session(**local_kw) -> AsyncSession:
    session = _async_session_ctx.get()
    if session is None:
        session = AsyncSessionFactory(**local_kw)
        _async_session_ctx.set(session)
    return session


@contextmanager
def sync_session_context(atomic: bool = True, autocommit: bool = False, **local_kw):
    token = _sync_session_ctx.set(None)
    session = get_sync_session(**local_kw)
    try:
        yield session
        if autocommit:
            session.commit()
    except Exception as e:
        if atomic:
            session.rollback()
        raise e
    finally:
        session.close()
        _sync_session_ctx.reset(token)


@asynccontextmanager
async def async_session_context(
    atomic: bool = True, autocommit: bool = False, **local_kw
):
    token = _async_session_ctx.set(None)
    session = await get_async_session(**local_kw)
    try:
        yield session
        if autocommit:
            await session.commit()
    except Exception as e:
        if atomic:
            await session.rollback()
        raise e
    finally:
        await session.close()
        _async_session_ctx.reset(token)


SyncSessionDep = Annotated[Session, Depends(sync_session_context)]
AsyncSessionDep = Annotated[AsyncSession, Depends(async_session_context)]
