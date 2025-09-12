import argparse
import os
import re


def to_snake_case(name):
    """Converts CamelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def generate_boilerplate(model_name_camel):
    """Generates boilerplate files for a new model."""
    model_name_snake = to_snake_case(model_name_camel)
    plural_snake = model_name_snake + "s"

    # --- File Paths ---
    base_path = "harbinger/src/harbinger"
    paths = {
        "model": f"{base_path}/models/{model_name_snake}.py",
        "schema": f"{base_path}/schemas/{model_name_snake}.py",
        "crud": f"{base_path}/crud/{model_name_snake}.py",
        "filter": f"{base_path}/filters/{model_name_snake}.py",
        "endpoint": f"{base_path}/api/v1/endpoints/{plural_snake}.py",
    }

    # --- Templates ---
    templates = {
        "model": f"""from sqlalchemy.orm import Mapped
from harbinger.database.database import Base
from harbinger.database.types import HarbingerUUID, UserForeignKey, now, int_pk, uuid_pk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User

class {model_name_camel}(Base):
    id: Mapped[uuid_pk]
    # TODO: Define your model columns here
    # example: name: Mapped[str]
""",
        "schema": f"""from pydantic import BaseModel, ConfigDict, UUID4
from typing import List, Optional

class {model_name_camel}Base(BaseModel):
    # TODO: Define your base schema fields here
    # example: name: str | None = None
    pass

class {model_name_camel}Create({model_name_camel}Base):
    pass

class {model_name_camel}Update({model_name_camel}Base):
    pass

class {model_name_camel}Created({model_name_camel}Base):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

class {model_name_camel}({model_name_camel}Base):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    # TODO: Add any relationships here
    # labels: List["Label"] | None = None
""",
        "crud": f"""from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.sql import func
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from typing import Tuple, Optional, Iterable
from pydantic import UUID4
import uuid

from harbinger import models, schemas, filters

# TODO: Implement your CRUD functions here.
# The following are examples and may need to be adjusted.

async def get_{plural_snake}_paged(
    db: AsyncSession,
    filters: filters.{model_name_camel}Filter
) -> Page[models.{model_name_camel}]:
    q = select(models.{model_name_camel})
    # Add any necessary joins here
    # q = q.outerjoin(models.{model_name_camel}.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    return await paginate(db, q)

async def get_{model_name_snake}(db: AsyncSession, id: UUID4) -> Optional[models.{model_name_camel}]:
    return await db.get(models.{model_name_camel}, id)

async def create_{model_name_snake}(db: AsyncSession, {model_name_snake}: schemas.{model_name_camel}Create) -> models.{model_name_camel}:
    db_{model_name_snake} = models.{model_name_camel}(**{model_name_snake}.model_dump())
    db.add(db_{model_name_snake})
    await db.commit()
    await db.refresh(db_{model_name_snake})
    return db_{model_name_snake}
""",
        "filter": f"""from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter

class {model_name_camel}Filter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    # TODO: Define your filter fields here
    # example: name__in: list[str] | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.{model_name_camel}
        # TODO: Define your search fields here
        # search_model_fields = ["name", "description"]
""",
        "endpoint": f"""from typing import Optional
from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas, filters
from harbinger.config.dependencies import current_active_user, get_db

router = APIRouter()

@router.get("/", response_model=Page[schemas.{model_name_camel}])
async def list_{plural_snake}(
    filters: filters.{model_name_camel}Filter = FilterDepends(filters.{model_name_camel}Filter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_{plural_snake}_paged(db, filters)

@router.get("/{{id}}", response_model=Optional[schemas.{model_name_camel}])
async def get_{model_name_snake}(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_{model_name_snake}(db, id)

@router.post("/", response_model=schemas.{model_name_camel})
async def create_{model_name_snake}(
    {model_name_snake}: schemas.{model_name_camel}Create,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_{model_name_snake}(db, {model_name_snake})
""",
    }

    # --- Create Files ---
    for file_type, path in paths.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(templates[file_type])
        print(f"Created: {path}")

    # --- Print Instructions ---
    print("\n--- BOILERPLATE GENERATION COMPLETE ---")
    print("\nNext steps:")
    print("\n1. Define your columns in the new model file:")
    print(f"   - {paths['model']}")
    print("\n2. Define your fields in the new schema file:")
    print(f"   - {paths['schema']}")
    print("\n3. Implement the CRUD functions for your new model:")
    print(f"   - {paths['crud']}")
    print("\n4. Define your filter fields in the new filter file:")
    print(f"   - {paths['filter']}")
    print("\n5. Add the new modules to their respective __init__.py files:")
    print(
        f"   - In harbinger/src/harbinger/models/__init__.py: from .{model_name_snake} import {model_name_camel}",
    )
    print(
        f"   - In harbinger/src/harbinger/schemas/__init__.py: from .{model_name_snake} import {model_name_camel}, {model_name_camel}Create, {model_name_camel}Update, {model_name_camel}Created",
    )
    print(
        f"   - In harbinger/src/harbinger/crud/__init__.py: from .{model_name_snake} import get_{plural_snake}_paged, get_{model_name_snake}, create_{model_name_snake}",
    )
    print(
        f"   - In harbinger/src/harbinger/filters/__init__.py: from .{model_name_snake} import {model_name_camel}Filter",
    )
    print("\n6. Add the new router to the main application:")
    print("   - In harbinger/src/harbinger/config/app.py:")
    print(
        f"     - Add the import: from harbinger.api.v1.endpoints import {plural_snake}",
    )
    print(
        f"     - Include the router: app.include_router({plural_snake}.router, prefix='/{plural_snake}', tags=['{plural_snake}'])",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate boilerplate files for a new Harbinger model.",
    )
    parser.add_argument(
        "model_name",
        help="The name of the model in CamelCase (e.g., NewFeature).",
    )
    args = parser.parse_args()

    generate_boilerplate(args.model_name)
