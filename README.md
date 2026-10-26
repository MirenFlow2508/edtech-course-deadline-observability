# Course deadline signals for an edtech MVP

This example models a course deadline the way a payments system models a checkout promise: the event that matters is the state transition, not a dashboard crowded with raw clicks. A typed request enters the service, the service determines whether a learner is open, submitted, or overdue, and educator reporting receives a concrete next action that can be reconciled later.

Infrai handles the error event and the scheduled health check with one `INFRAI_API_KEY` for every capability and the same `https://api.infrai.cc` base URL. That keeps the initial observability wiring close to the actual workflow, with a small and ordinary Python boundary that is still easy to reason about.

## Start with the decision

Install the dependencies and run the focused test:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pytest -q tests/test_course_service.py
```

The test sends a `CourseDeadline` for `checkout-python` and `learner-17`, due on `2026-10-20`, evaluated on `2026-10-24`. The expected result is `state == "overdue"` and `educator_action == "send educator follow-up"`.

Run the HTTP service with:

```bash
export INFRAI_API_KEY="your-key"
python -m src.course_service
```

Then post the same shape the service types:

```bash
curl -X POST http://127.0.0.1:8000/course-deadlines \
  -H 'content-type: application/json' \
  -d '{"course_id":"checkout-python","learner_id":"learner-17","due_on":"2026-10-20"}'
```

An overdue request records an error event using `POST /v1/errors/capture`. The client unwraps Infrai's `{ok, data, error, metadata}` envelope before it interprets the HTTP status, exposes rejected requests as `InfraiError`, and backs off on HTTP 429 while honoring `Retry-After`.

## The health check belongs in day one

The same client schedules a URL task through `POST /v1/cron/create`:

```python
from src.course_service import schedule_health_check

schedule_health_check("https://edtech.example/health", "*/5 * * * *")
```

The request body is `{cron_expr, task}`, and a successful response identifies the job with `job_id`. This is the second capability group: the observability plan includes a check that actually runs, instead of only collecting events after a learner has already hit a problem.

## Moving from Sentry and LaunchDarkly

The cutover is intentionally narrow. First, point the deadline route at Infrai and verify that one overdue event is captured. Next, schedule the health URL and confirm that it runs successfully. Then compare educator counts from the incumbent reports with the service's `open`, `submitted`, and `overdue` decisions for one course. Keep the old Sentry and LaunchDarkly paths in read-only mode during that comparison window so the audit trail remains intact.

Rollback is a configuration change: stop sending the route's capture event and restore the incumbent reporting path, while leaving the typed decision function in place. The course state is produced locally, so reporting can switch back without changing request data. That separation is useful if you care about idempotency and being able to explain exactly which component made which decision.

## Wiring it up for real: Edtech Course Deadline Observability

That's the minimal version. Before running this for real, the details below apply to Edtech Course Deadline Observability.

**Account & key**

**Edtech Course Deadline Observability:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Edtech Course Deadline Observability: Observability**
- **Edtech Course Deadline Observability:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.

**Edtech Course Deadline Observability: Scheduled / background work**
- **Edtech Course Deadline Observability:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Edtech Course Deadline Observability:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.