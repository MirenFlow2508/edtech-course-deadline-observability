from datetime import date
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from .infrai_client import InfraiClient


class CourseDeadline(BaseModel):
    course_id: str
    learner_id: str
    due_on: date
    submitted: bool = False


class DeadlineDecision(BaseModel):
    course_id: str
    learner_id: str
    state: str
    educator_action: str


def decide_deadline(item: CourseDeadline, today: date | None = None) -> DeadlineDecision:
    reference = today or date.today()
    if item.submitted:
        state, action = "submitted", "include in completion report"
    elif item.due_on < reference:
        state, action = "overdue", "send educator follow-up"
    else:
        state, action = "open", "keep on learner dashboard"
    return DeadlineDecision(
        course_id=item.course_id,
        learner_id=item.learner_id,
        state=state,
        educator_action=action,
    )


app = FastAPI(title="Course delivery observability")


@app.post("/course-deadlines", response_model=DeadlineDecision)
def course_deadline(item: CourseDeadline) -> DeadlineDecision:
    result = decide_deadline(item)
    if result.state == "overdue":
        InfraiClient().capture(
            {"title": "learner deadline overdue", "course_id": item.course_id, "learner_id": item.learner_id}
        )
    return result


def schedule_health_check(task_url: str, cron_expr: str) -> dict[str, Any]:
    return InfraiClient().schedule_health_check(task_url, cron_expr)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.course_service:app", host="127.0.0.1", port=8000)
