from datetime import date

from src.course_service import CourseDeadline, decide_deadline


def test_past_unsubmitted_deadline_needs_educator_follow_up():
    item = CourseDeadline(
        course_id="checkout-python",
        learner_id="learner-17",
        due_on=date(2026, 10, 20),
    )

    result = decide_deadline(item, today=date(2026, 10, 24))

    assert result.state == "overdue"
    assert result.educator_action == "send educator follow-up"
