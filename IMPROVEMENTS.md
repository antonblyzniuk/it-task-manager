# IT Task Manager — Improvement Roadmap

## Current State

The project is a working Django 5.2 task management app with:
- Full CRUD for Tasks, Workers, Positions, and Task Types
- Custom `Worker` model extending `AbstractUser`
- M2M task assignments, priority levels, search, pagination
- Bootstrap 5 UI with animations, deployed on Railway with Docker

It demonstrates core Django skills well. The improvements below will push it from a junior-level CRUD app to a portfolio-ready project that shows architectural thinking, security awareness, and full-stack depth.

---

## Improvements

### Phase 1 — Foundation (fix what's broken or weak)

**1. Role-based permissions**
Right now any logged-in user can edit or delete any other user's data. There are no ownership checks anywhere.
- Add a `role` field to `Worker`: `ADMIN`, `MANAGER`, `DEVELOPER`
- Managers can create/assign tasks; only admins can manage Positions and Task Types
- Workers can only edit/delete objects they own or are assigned to
- Use `UserPassesTestMixin` on views that need ownership checks

**2. Timestamps on all models**
Tasks, Positions, and Task Types have no `created_at` or `updated_at`. These are basic fields expected in any real app and unlock sorting, filtering, and audit features.
- Add `created_at = models.DateTimeField(auto_now_add=True)` and `updated_at = models.DateTimeField(auto_now=True)` to `Task`, `Position`, `TaskType`

**3. "My Tasks" view**
There is no way for a user to see only their own assigned tasks. Every user sees the full task list.
- Add `/tasks/my/` view filtered by `assignees=request.user`
- Add it to the navbar

**4. Advanced task filtering**
The current search is a single text input. There is no way to filter by priority, status, assignee, deadline range, or task type.
- Extend `TaskListView` with URL query params: `?priority=HIGH&is_completed=false&assignee=3`
- Add a filter sidebar or inline filter bar to `task_list.html`

**5. CI/CD with GitHub Actions**
There is no automated testing pipeline. Every push to `main` should run tests and linting.
- Add `.github/workflows/ci.yml` that runs `python manage.py test` and `ruff check .` on every push and pull request
- Add a test coverage badge to the README

---

### Phase 2 — Features that make it feel real

**6. Task comments**
Tasks have no discussion. Comments are the single most-used feature in any real task tracker (GitHub Issues, Jira, Linear all have them).
- Add a `Comment` model: `task` (FK), `author` (FK Worker), `body` (TextField), `created_at`
- Add comment form and list to `task_detail.html`
- Authors can delete their own comments; admins can delete any

**7. Activity log / audit trail**
There is no history of who changed what or when. This is critical for a team tool and impressive technically.
- Add a `TaskActivity` model: `task` (FK), `actor` (FK Worker), `action` (CharField: assigned, completed, commented, updated), `timestamp`
- Log an entry on: task create, complete, assign, unassign, comment
- Show the activity timeline on the task detail page

**8. File attachments on tasks**
Tasks can only have text descriptions. Real work involves screenshots, specs, and documents.
- Add a `TaskAttachment` model: `task` (FK), `file` (FileField), `uploaded_by` (FK), `uploaded_at`
- Use `django-storages` with an S3-compatible bucket (Cloudflare R2 or AWS S3) for production file storage
- Show attachments on task detail with download links

**9. Email notifications**
Nothing happens when you assign someone to a task or when a deadline approaches.
- Integrate Django's email backend (SendGrid or Resend)
- Send email on: task assigned to you, task completed, deadline within 24 hours
- Use Celery + Redis for async email delivery so requests don't block

**10. REST API with Django REST Framework**
The app is web-only with no API. A public REST API shows backend maturity and makes the project usable by other clients (mobile, CLI, integrations).
- Add DRF: `/api/v1/tasks/`, `/api/v1/workers/`, `/api/v1/positions/`
- Token authentication (DRF `TokenAuthentication`)
- Proper serializers with nested relationships (task shows assignee usernames, not just IDs)
- Pagination, filtering, ordering at API level
- Auto-generated API docs with `drf-spectacular` (OpenAPI/Swagger UI at `/api/docs/`)

---

### Phase 3 — Polish that impresses

**11. Analytics dashboard**
The current homepage shows three counters. A real analytics page shows trends and is the kind of thing that makes a project feel alive.
- Dedicated `/dashboard/` view for logged-in users
- Charts using Chart.js (no extra backend dependency):
  - Tasks completed per week (line chart)
  - Task distribution by priority (doughnut chart)
  - Worker workload: number of open tasks per person (bar chart)
  - Overdue task count over time
- All data computed server-side and passed as JSON to the template

**12. Expanded test suite**
The current suite has 25 tests. A resume-worthy project should hit 80%+ coverage with meaningful tests, not just status-code checks.
- Test search and filter logic
- Test permission rules (user A cannot delete user B's task)
- Test all API endpoints (authentication, pagination, validation)
- Test the activity log is written correctly
- Add `coverage` report to CI and fail the build under 80%

**13. Health check endpoint**
Production apps need a `/health/` endpoint that monitoring tools and Railway's healthcheck can ping.
- Return `{"status": "ok", "db": "ok"}` — actually queries the DB to confirm connectivity
- No authentication required

**14. `created_by` field on Task**
Track who created each task so ownership-based permissions and the activity log work cleanly.
- Add `created_by = models.ForeignKey(Worker, on_delete=models.SET_NULL, null=True, related_name="created_tasks")`
- Auto-set in `TaskCreateView.form_valid()`

---

## Implementation Plan

### Phase 1 — 1–2 weeks

| Order | Task | Why first |
|-------|------|-----------|
| 1 | Timestamps on all models | Zero-risk migration; unlocks everything that needs ordering by date |
| 2 | `created_by` on Task | Needed before permissions can reference ownership |
| 3 | Role-based permissions | Fixes a real security hole; touches views and models cleanly |
| 4 | "My Tasks" view | Small, high-value, builds on the permission work |
| 5 | Advanced task filtering | Builds on existing `TaskListView`; no new models |
| 6 | GitHub Actions CI | Catches regressions from all future changes automatically |

### Phase 2 — 2–3 weeks

| Order | Task | Why this order |
|-------|------|----------------|
| 7 | Task comments | New model + form + template; self-contained |
| 8 | Activity log | Depends on comments being done so comment events can also be logged |
| 9 | File attachments | New model + storage config; independent of comments/activity |
| 10 | REST API | Best done after models stabilize; serializers reflect final model shape |
| 11 | Email notifications | Last because it depends on Celery setup which is infrastructure work |

### Phase 3 — 1–2 weeks

| Order | Task | Why this order |
|-------|------|----------------|
| 12 | Analytics dashboard | All data is available once Phase 2 models exist |
| 13 | Expanded test suite | Written last so tests cover the final feature set, not intermediate states |
| 14 | Health check endpoint | Quick win, do it alongside testing |

---

## What Each Phase Demonstrates on a Resume

**After Phase 1:**
Django fundamentals done right — custom permissions, data modeling with relationships, automated testing pipeline, search and filtering.

**After Phase 2:**
Full-stack feature development — REST API design, async task queues (Celery), file storage (S3), DRF serializers with nested data, OpenAPI documentation.

**After Phase 3:**
Production-grade thinking — observability (health checks), analytics with chart rendering, high test coverage with CI enforcement.
