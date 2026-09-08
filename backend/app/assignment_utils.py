from app.models import Assignment, RubricCriterion, RubricItem
from app.schemas import RubricCriterionOut, RubricItemOut


def criterion_to_out(c: RubricCriterion) -> RubricCriterionOut:
    return RubricCriterionOut(
        id=c.id,
        title=c.title,
        description=c.description,
        order=c.order,
        items=[
            RubricItemOut(id=i.id, label=i.label, points=i.points, order=i.order)
            for i in sorted(c.items, key=lambda i: i.order)
        ],
    )


def max_score(assignment: Assignment) -> int:
    """Each criterion contributes its highest-value item — the grader picks
    one tier per criterion, not a sum of checked conditions."""
    return sum(max((i.points for i in c.items), default=0) for c in assignment.criteria)


def resolve_selection(assignment: Assignment, selected_ids: list[str]) -> tuple[list[str], int]:
    """Picks at most one item per criterion from the given ids (the last
    matching item wins if more than one was sent for the same criterion) and
    returns the cleaned id list plus the resulting total score."""
    selected_set = set(selected_ids)
    resolved: list[str] = []
    total = 0
    for c in sorted(assignment.criteria, key=lambda c: c.order):
        chosen: RubricItem | None = None
        for i in sorted(c.items, key=lambda i: i.order):
            if i.id in selected_set:
                chosen = i
        if chosen:
            resolved.append(chosen.id)
            total += chosen.points
    return resolved, total


def selected_item_by_criterion(assignment: Assignment, selected_ids: list[str]) -> dict:
    """Maps criterion id -> selected RubricItem for the given selection."""
    selected_set = set(selected_ids)
    result = {}
    for c in assignment.criteria:
        for i in c.items:
            if i.id in selected_set:
                result[c.id] = i
    return result
