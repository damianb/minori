''' database connection management '''

from contextlib import asynccontextmanager
import os
from typing import Annotated, Optional

from fastapi import Depends, Request
from sqlalchemy import inspect, Connection
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession as _AsyncSession
from starlette.types import ASGIApp, Receive, Scope, Send

from minori.db.models import Base
from minori.util import get_env_secret

class DbConnection:
    ''' Database connection management '''

    def __init__(self):
        ''' Constructor '''

        self.engine: Optional[AsyncEngine] = None
        self.session: Optional[async_sessionmaker[_AsyncSession]] = None

        self.connection_string: str = self._build_connection_string(
            db_username=os.environ.get('DB_USERNAME', 'minori'),
            db_password=get_env_secret('DB_PASSWORD', ''), # type: ignore
            db_host=os.environ.get('DB_HOST', 'localhost'),
            db_name=os.environ.get('DB_NAME', 'minori')
        )

    def _build_connection_string(self, db_username: str, db_password: str, db_host: str, db_name: str) -> str:
        ''' Build a connection string for a MySQL / MariaDB instance'''

        dialect = 'mariadb'
        driver = 'asyncmy'
        charset = 'utf8mb4'

        return f'{dialect}+{driver}://{db_username}:{db_password}@{db_host}/{db_name}?charset={charset}'

    def check_if_created(self, conn: Connection) -> bool:
        ''' Check if the database been initially created (at the very least) '''

        inspector = inspect(conn)
        return inspector.has_table('Image')

    async def create_all(self):
        ''' Create clean database '''

        if not self.engine:
            return

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def start(self) -> async_sessionmaker[_AsyncSession]:
        ''' Start the DB connection for the application '''

        self.engine = create_async_engine(
            self.connection_string,
            # echo=True,
            future=True,
            pool_recycle=3600,
            pool_pre_ping=True
        )

        async with self.engine.connect() as conn:
            created = await conn.run_sync(self.check_if_created)

        if not created:
            await self.create_all()

        self.session = async_sessionmaker(bind=self.engine, expire_on_commit=False) # pylint: disable=invalid-name

        return self.session

    @asynccontextmanager
    async def get_session(self):
        ''' Gets a new database session for use (made for the db injector middleware) '''
        if not self.session:
            raise RuntimeError('Engine not yet started, cannot retrieve session.')

        async with self.session() as session:
            yield session

    async def stop(self):
        ''' Stop the DB connection '''

        if not self.engine:
            return

        await self.engine.dispose(close=True)
        self.engine = None
        self.session = None

class AsyncSessionDbInjectorMiddleware:
    ''' middleware that injects the db session into the request state '''
    _ASYNC_SESSION_REQUEST_STATE_KEY = 'dbsession'

    def __init__(self, app: ASGIApp) -> None:
        ''' middleware init '''
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        ''' injects a db session into the request state '''
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async with dbconn.get_session() as session:
            request = Request(scope=scope, receive=receive, send=send)
            setattr(request.state, self._ASYNC_SESSION_REQUEST_STATE_KEY, session)

            await self.app(scope, receive, send)

class AsyncSessionDependency:
    ''' async session dependency injector '''
    def __call__(self, request: Request) -> _AsyncSession:
        ''' retrieve the async session from request state '''
        return getattr(request.state, AsyncSessionDbInjectorMiddleware._ASYNC_SESSION_REQUEST_STATE_KEY)

dbconn = DbConnection()
_async_session_dep = AsyncSessionDependency() # pylint: disable=invalid-name
AsyncSession = Annotated[_AsyncSession, Depends(_async_session_dep)]
