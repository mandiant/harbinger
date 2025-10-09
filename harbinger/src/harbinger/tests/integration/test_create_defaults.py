import pytest
from harbinger.config.create_defaults import create_all
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_all_idempotency(db_session: AsyncSession):
    """
    Tests that the create_all function can be run multiple times without error.
    """
    # Run the function for the first time
    await create_all(db_session)

    # Run the function for the second time
    await create_all(db_session)
