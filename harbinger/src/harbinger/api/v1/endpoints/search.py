from fastapi import APIRouter, Depends, Query
from harbinger import models
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.crud import search as search_crud
from harbinger.schemas.search import SearchResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=SearchResponse, tags=["search"])
async def global_search(
    db: AsyncSession = Depends(get_db),
    q: str = Query(..., description="The search term."),
    user: models.User = Depends(current_active_user),
):
    """
    Performs a global search across multiple database models.
    """
    search_results = await search_crud.perform_global_search(db=db, query=q)
    return {"results": search_results}
