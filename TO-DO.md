# Implementation TO-DO for AI

This file contains precise implementation instructions. Follow every step exactly. Do not skip steps, do not add unrequested features, do not leave placeholders.

---

## 1. Dashboard Redesign — More Statistics

### Context
- Dashboard view: `main/views.py` → `index()` function (around line 79)
- Dashboard template: `templates/main/index.html`
- Models available: `Task`, `Worker`, `Position`, `TaskType` in `main/models.py`
- Task has fields: `priority` (choices: LOW, MEDIUM, HIGH, URGENT), `is_completed` (bool), `deadline` (DateField), `assignees` (M2M to Worker), `task_type` (FK to TaskType), `created_by` (FK to Worker)
- Worker has `role` (ADMIN, MANAGER, DEVELOPER)

### Step 1 — Extend the view context

In `main/views.py`, update the `index()` function to pass additional stats. Use `django.utils.timezone.now().date()` for today's date. Import `Count`, `Q` from `django.db.models`. Add all of the following to the context dict:

```python
from django.utils import timezone
from django.db.models import Count, Q

today = timezone.now().date()

context = {
    # Existing
    "num_of_workers": Worker.objects.count(),
    "num_of_tasks": Task.objects.count(),
    "num_of_positions": Position.objects.count(),

    # New stats
    "num_of_task_types": TaskType.objects.count(),
    "num_completed_tasks": Task.objects.filter(is_completed=True).count(),
    "num_open_tasks": Task.objects.filter(is_completed=False).count(),
    "num_overdue_tasks": Task.objects.filter(is_completed=False, deadline__lt=today).count(),
    "num_urgent_tasks": Task.objects.filter(priority="urgent", is_completed=False).count(),
    "num_high_tasks": Task.objects.filter(priority="high", is_completed=False).count(),
    "num_admins": Worker.objects.filter(role="admin").count(),
    "num_managers": Worker.objects.filter(role="manager").count(),
    "num_developers": Worker.objects.filter(role="developer").count(),
    "recent_tasks": Task.objects.select_related("task_type", "created_by")
                        .prefetch_related("assignees")
                        .order_by("-id")[:5],
    "completion_rate": round(
        Task.objects.filter(is_completed=True).count() /
        max(Task.objects.count(), 1) * 100
    ),
}
```

Make sure `TaskType` is imported at the top of `views.py` (check existing imports first).

### Step 2 — Redesign `templates/main/index.html`

Replace the entire file content with a new layout. Keep the `{% extends "base.html" %}` and `{% load static %}` at the top.

**Layout structure (in order):**

#### A. Page Header
A simple header row with title "Dashboard" and subtitle showing today's date using `{{ now|date:"F j, Y" }}`. Pass `now` in context (`"now": timezone.now()`). No hero image — the dashboard is for authenticated users.

#### B. Primary Stats Row — 4 cards
Use Bootstrap `row g-3` with `col-sm-6 col-xl-3` columns. Each card uses the existing card hover effect from `styles.css` (class `stat-card` if present, or add a simple card with `shadow-sm rounded-3 p-4`). Cards:

1. **Total Tasks** — `bi-list-task` icon, blue (`text-primary`), value: `{{ num_of_tasks }}`
2. **Completed** — `bi-check-circle-fill` icon, green (`text-success`), value: `{{ num_completed_tasks }}`
3. **Open Tasks** — `bi-hourglass-split` icon, amber/warning (`text-warning`), value: `{{ num_open_tasks }}`
4. **Overdue** — `bi-exclamation-triangle-fill` icon, red (`text-danger`), value: `{{ num_overdue_tasks }}`

Each card should have a counter animation (copy the existing counter JS pattern from the current `index.html` — look for the `animateCounter` or similar function).

#### C. Secondary Stats Row — 3 cards
`col-sm-6 col-xl-4` columns:

1. **Total Workers** — `bi-people-fill`, blue, value: `{{ num_of_workers }}`
2. **Positions** — `bi-diagram-3-fill`, cyan (`text-info`), value: `{{ num_of_positions }}`
3. **Task Types** — `bi-tags-fill`, purple (`text-purple` — use inline style `color:#8b5cf6`), value: `{{ num_of_task_types }}`

#### D. Priority Breakdown & Team Composition — 2-column row
`col-lg-6` each.

**Left card — Priority Breakdown:**
Title: "Open Tasks by Priority". Show four horizontal progress-style rows (no actual `<progress>` tag — use Bootstrap `progress` bars):
- Urgent: `{{ num_urgent_tasks }}` tasks — red (`bg-danger`)
- High: `{{ num_high_tasks }}` tasks — amber (`bg-warning`)
- Remaining medium/low: derive as `{{ num_open_tasks }} - num_urgent_tasks - num_high_tasks` — pass `num_medium_low_tasks` in context for this.
  - Add to view: `"num_medium_low_tasks": Task.objects.filter(is_completed=False, priority__in=["medium","low"]).count()`
- Each bar: label on left, count badge on right, bar below. Bar width % = count / max(num_open_tasks, 1) * 100. Pass `"open_tasks_max": max(num_open_tasks, 1)` in context and compute in template with `widthratio` tag.

**Right card — Team Composition:**
Title: "Team by Role". Three role rows with icon, label, count, and a progress bar:
- Admin: `bi-shield-fill`, blue, `{{ num_admins }}`
- Manager: `bi-person-badge-fill`, green, `{{ num_managers }}`
- Developer: `bi-code-slash`, purple, `{{ num_developers }}`
- Bar width = role_count / max(num_of_workers, 1) * 100. Use `widthratio` tag.

#### E. Completion Rate Card — full width
A single wide card. Title: "Overall Task Completion". Show a large centered percentage `{{ completion_rate }}%` with an animated circular or thick Bootstrap progress bar. Use Bootstrap's `progress` with `style="height:12px"`. Bar width = `{{ completion_rate }}`. Color: green if >70, amber if >40, red otherwise — use template `{% if %}` to set class.

#### F. Recent Tasks Table — full width
Title: "Recently Added Tasks". A `table table-hover table-sm` inside a card. Columns: Task name (link to task detail if detail view exists, otherwise plain text), Type, Priority (badge with color), Status (badge), Deadline. Loop `{% for task in recent_tasks %}`. If `recent_tasks` is empty show a muted "No tasks yet." row. Priority badge colors: urgent=`bg-danger`, high=`bg-warning text-dark`, medium=`bg-primary`, low=`bg-secondary`.

#### Animations
- Wrap each major card/row in `data-aos="fade-up"` with staggered `data-aos-delay` (0, 100, 200, 300…).
- Counter animation must trigger after AOS reveals the element — use `AOS.init` callback or `IntersectionObserver`. The safest approach: run counters after `DOMContentLoaded` with a small 300ms delay so AOS has shown the cards.

---

## 2. About Page

### Step 1 — Create the template

Create `templates/main/about.html`. Extend `base.html`. Load static.

**Layout:**

#### Hero Section
Full-width section with a soft gradient background (use inline style: `background: linear-gradient(135deg, #1e3a5f 0%, #3b82f6 100%); min-height: 340px;`). Center-aligned. White text.
- Large heading: "IT Task Manager"
- Subheading: "A modern project management tool built with Django"
- Small paragraph (3-4 sentences): describe what the app does. Example text:

> IT Task Manager is a full-stack web application designed to help development teams organize and track their work efficiently. It supports role-based access control with Admin, Manager, and Developer roles, a Kanban board view, task priorities, deadlines, and team management. Built as a portfolio project to demonstrate real-world Django development skills including authentication, permissions, and responsive UI design.

Use `data-aos="fade-down"` on the hero text block.

#### About the Project — feature list
A card with two Bootstrap columns (`col-md-6`). Left column title "Key Features", right column title "Tech Stack".

Key Features (use `bi-check-circle-fill text-success` icon prefix):
- Role-based access control (Admin / Manager / Developer)
- Kanban board with drag-ready card layout
- Task priorities: Urgent, High, Medium, Low
- Deadline tracking and overdue detection
- My Tasks personal view
- Full CRUD for tasks, workers, positions, and task types

Tech Stack (use `bi-dot` icon prefix):
- Python & Django
- PostgreSQL
- Bootstrap 5 + Bootstrap Icons
- AOS animations
- GitHub Actions CI

Apply `data-aos="fade-up"` with delay 100.

#### Links / Buttons Section
A centered section. Title: "Find Me Online". Two large buttons side by side (centered, gap-3, flex-wrap):

**Button 1 — GitHub:**
```html
<a href="https://github.com/antonblyzniuk/it-task-manager"
   target="_blank" rel="noopener noreferrer"
   class="btn btn-dark btn-lg px-4 py-3 d-inline-flex align-items-center gap-2">
  <i class="bi bi-github fs-5"></i>
  View on GitHub
</a>
```

**Button 2 — Personal Website:**
```html
<a href="https://www.antonblyzniuk.com"
   target="_blank" rel="noopener noreferrer"
   class="btn btn-outline-primary btn-lg px-4 py-3 d-inline-flex align-items-center gap-2">
  <i class="bi bi-globe2 fs-5"></i>
  My Website
</a>
```

Apply `data-aos="zoom-in"` with delay 200 on the buttons container.

#### Developer card
A small centered card below the buttons (max-width 480px, `mx-auto`). Avatar placeholder: a rounded circle `div` with gradient background (`background: linear-gradient(135deg, #3b82f6, #8b5cf6)`) displaying initials "AB" in white, 80px × 80px. Name: "Anton Blyzniuk". Role: "Full Stack Developer". No photo — just the gradient initials circle (same pattern as the sidebar user avatar in `base.html`).

Apply `data-aos="fade-up"` delay 300.

### Step 2 — Create the view

In `main/views.py` add:
```python
def about(request: HttpRequest) -> HttpResponse:
    return render(request, "main/about.html")
```

No login required — this page is public.

### Step 3 — Add URL

In `main/urls.py` add:
```python
path("about/", views.about, name="about"),
```

### Step 4 — Add to navigation

In `templates/base.html`, in the authenticated sidebar navigation (the section with "Main" links), add an About link after the Dashboard link:
```html
<a href="{% url 'main:about' %}"
   class="nav-link {% if request.path == '/about/' %}active{% endif %}">
  <i class="bi bi-info-circle"></i>
  <span>About</span>
</a>
```

Also add About to the **public navbar** (the unauthenticated layout at the bottom of base.html) between the brand and the Login button:
```html
<a class="nav-link" href="{% url 'main:about' %}">About</a>
```

---

## 3. Favicon

### Step 1 — Create the SVG favicon

Create `static/images/favicon.svg` with this content — a simple kanban-style icon matching the project theme (blue tones):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#3b82f6"/>
  <rect x="4" y="6" width="7" height="10" rx="2" fill="white" opacity="0.95"/>
  <rect x="13" y="6" width="7" height="14" rx="2" fill="white" opacity="0.95"/>
  <rect x="22" y="6" width="7" height="7" rx="2" fill="white" opacity="0.95"/>
  <rect x="4" y="19" width="7" height="7" rx="2" fill="white" opacity="0.6"/>
  <rect x="22" y="16" width="7" height="10" rx="2" fill="white" opacity="0.6"/>
</svg>
```

This represents a kanban board column layout on a blue rounded square.

### Step 2 — Add favicon links to `templates/base.html`

Inside `<head>`, after the existing CSS links, add:
```html
<link rel="icon" type="image/svg+xml" href="{% static 'images/favicon.svg' %}">
<link rel="icon" type="image/x-icon" href="{% static 'images/favicon.svg' %}">
```

Make sure `{% load static %}` is already at the top of `base.html` (verify before adding — it should be there).

Verify `static/images/` directory exists; create it if not.

---

## 4. Animations — Enhance & Standardize

### Context
AOS (Animate On Scroll) and Animate.css are already loaded via CDN in `base.html`. AOS is already initialized in the base template's inline `<script>` block.

### Step 1 — AOS config update

In `base.html`, find the `AOS.init({...})` call and update it to:
```javascript
AOS.init({
  duration: 600,
  easing: 'ease-out-cubic',
  once: true,
  offset: 60,
});
```

### Step 2 — Sidebar entrance animation

In `base.html`, add `class="animate__animated animate__fadeInLeft"` to the sidebar `<nav>` or `<aside>` element (whichever is the top-level sidebar container). Only add this once. This fires on every page load since it uses Animate.css (not scroll-triggered).

### Step 3 — Page content fade-in

In `base.html`, wrap the main content area `<main>` (or whatever the content wrapper div is) with an additional class: add `animate__animated animate__fadeIn animate__faster` to the content container that holds `{% block content %}`. The `animate__faster` class makes it 500ms. This gives every page a smooth fade-in.

### Step 4 — Sidebar link hover animation

In `static/css/styles.css`, find the sidebar nav link rules. Add a transition for transform so links slide slightly right on hover:
```css
/* Add to or update the existing sidebar .nav-link rule */
.sidebar .nav-link {
  transition: background 0.2s ease, color 0.2s ease, transform 0.15s ease;
}
.sidebar .nav-link:hover {
  transform: translateX(4px);
}
```
If a rule already exists for `.sidebar .nav-link`, extend it — do not duplicate the selector.

### Step 5 — Card hover lift effect (global)

In `static/css/styles.css`, add a reusable utility that can be applied on any card:
```css
.card-hover {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.12) !important;
}
```
Apply `card-hover` class to all stat cards in the new dashboard and the about page's feature card.

### Step 6 — Button ripple/pulse on About page

On the About page's GitHub and Website buttons, add Bootstrap's built-in focus-visible ring by ensuring the buttons do NOT have `outline: none`. No custom JS needed — Bootstrap handles focus states. Additionally add `transition: transform 0.15s ease` to the anchor elements via a small CSS block in the About template's `{% block extra_css %}` or inline `<style>` tag:
```css
.about-btn {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.about-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.35);
}
```
Add class `about-btn` to both buttons.

---

## Checklist — Verify before finishing

- [ ] `python manage.py check` produces no errors
- [ ] Dashboard page loads with all new stat cards visible and counters animating
- [ ] `/about/` URL resolves and shows both buttons with correct external links
- [ ] Both external links open in a new tab (`target="_blank"`)
- [ ] Favicon SVG file exists at `static/images/favicon.svg`
- [ ] Browser tab shows the kanban icon (test with `python manage.py collectstatic --noinput` then run dev server)
- [ ] AOS animations trigger on scroll on the dashboard and about page
- [ ] Sidebar links slide on hover
- [ ] No `TemplateDoesNotExist`, `NoReverseMatch`, or `FieldError` exceptions
- [ ] About page is accessible without login
- [ ] Navigation sidebar includes the About link
- [ ] `widthratio` template tag is used correctly (it takes: value, max_value, multiplier — e.g., `{% widthratio num_urgent_tasks num_open_tasks 100 %}`)
