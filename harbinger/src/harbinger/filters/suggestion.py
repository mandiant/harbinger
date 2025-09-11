from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter
from .plan_step import PlanStepFilter


class SuggestionFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    reason: str | None = None
    playbook_template_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    plan_step: PlanStepFilter | None = FilterDepends(with_prefix("plan_step", PlanStepFilter))
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Suggestion
        search_model_fields = ['name', 'reason']

