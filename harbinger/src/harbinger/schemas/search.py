from pydantic import UUID4, BaseModel


class SearchResultItem(BaseModel):
    """Represents a single item in the global search results."""

    id: UUID4
    type: str  # e.g., "Host", "File", "Credential"
    name: str  # The primary display field, e.g., a hostname or filename
    context: str | None = None  # Secondary context, e.g., an IP address or file path
    url: str  # The frontend URL to the object's detail page

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """The complete response for a search query."""

    results: list[SearchResultItem]
