from typing import Callable
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import create_engine


def create_db_session_generator(db_uri: str) -> Callable:
    """
    This will create a db session

    :param db_uri: The DB URI
    :return: A callable
    """

    engine = create_engine(db_uri)

    session_maker = sessionmaker(bind=engine)

    def get_session():
        with session_maker() as session:
            try:
                yield session
            except Exception as e:
                session.rollback()

                raise e

    return get_session


def create_db_async_session_generator(db_uri: str) -> Callable:
    """
    This will create an async db session

    :param db_uri: The DB URI
    :return: A callable
    """
    engine = create_async_engine(
        db_uri
    )

    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async def get_session():
        async with async_session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()

                raise e

    return get_session

