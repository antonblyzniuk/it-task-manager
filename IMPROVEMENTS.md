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

**5. UI Redesign**
The current UI uses generic Bootstrap 5 defaults. A polished, distinctive design makes the project visually memorable and shows frontend awareness.
- Replace Bootstrap CDN with a custom design system (Tailwind CSS or a customized Bootstrap theme)
- Redesign the task list as a Kanban-style board with columns: To Do, In Progress, Done
- Add a proper sidebar navigation instead of the top navbar (standard in modern dashboards)
- Improve empty states — each empty list should show an icon and a helpful call-to-action
- Add skeleton loaders instead of blank page on load
- Make priority and status indicators more prominent (colored left border on task cards, not just a badge)
- Improve the task detail page layout: two-column with task info on the left and assignees/activity on the right
- Ensure full mobile responsiveness on all list and form pages


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
| 7 | UI Redesign | Done after features stabilize so the design isn't rebuilt twice; new layout wraps all existing views |

