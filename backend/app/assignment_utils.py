from app.models import Assignment, RubricCriterion
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
    return sum(i.points for c in assignment.criteria for i in c.items)


def all_items(assignment: Assignment) -> list:
    items = []
    for c in sorted(assignment.criteria, key=lambda c: c.order):
        for i in sorted(c.items, key=lambda i: i.order):
            items.append((c, i))
    return items
