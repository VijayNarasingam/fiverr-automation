from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine = None
async_session = None


def init_db(database_url: str):
    global engine, async_session
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


# Import all models so that Base.metadata includes every table.
from app.models import base  # noqa: F401  (noqa: E402)
from app.models import gig    # noqa: F401  (noqa: E402)
from app.models import order  # noqa: F401  (noqa: E402)
from app.models import message  # noqa: F401  (noqa: E402)
from app.models import audit_log  # noqa: F401  (noqa: E402)
from app.models import session  # noqa: F401  (noqa: E402)
