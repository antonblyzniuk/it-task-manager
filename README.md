# 🚀 IT-task-manager

## 📝 Description

### ❓ Why?
This project was created to build a practical and elegant task management tool while learning and demonstrating core Django web development skills. It addresses the need for a lightweight, easily extendable, and beginner-friendly platform for managing projects and tasks—especially for small startups, indie developers, and student teams.

### ⚙️ How?

The solution works by combining Django’s robust backend capabilities with a clean and responsive frontend enhanced by modern animations and intuitive design patterns. It uses Django, HTML/CSS, and JavaScript to achieve a seamless task management experience with features like task creation, project organization, and user-friendly navigation.

### 👥 For Who?

This project is designed for:
- 👨‍💻 Small startups, indie developers, and student teams
- 🎓 Students learning how to structure Django projects and implement CRUD features
- 🔍 Anyone looking for examples of a clean, responsive, and open-source task management system built with Django

## 🔗 See in Action

You can try the live demo here: https://it-task-manager-nws5.onrender.com/

## ✨ Features

- 🔐 User Authentication: Secure login and logout system
- 🧑 Worker Management: Create, update, and view worker details
- 📋 Task Management: Assign, update, and track tasks easily
- ✅ Status Tracking: Visual indicators for task completion and progress
- 💅 Responsive UI with Animations: Clean design with smooth transitions
- 🔍 Debug Toolbar: Built-in dev tools for inspecting queries and performance

## 🧰 Tech Stack

**🖥️ Frontend:**
- Django Templates
- Crispy Forms
- Bootstrap 5

**🗄️ Backend:**
- Python 3.12+
- Django 5.2.1
- PostgreSQL

**🛠️ Tools & Others:**
- black, ruff – Code formatting and linting
- django-debug-toolbar – Debugging and query inspection
- python-decouple – Environment variable management
- coverage – Test coverage reporting
- Deployed on Render

## 💻 Local Installation

### 1. Clone the repository
```bash
git clone https://github.com/AntonBliznuk/it-task-manager
cd it-task-manager
```

### 2. Set up a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: env\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```bash
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/dbname
ADMIN_SECRET_CODE=your-admin-secret   # optional, enables /admin-register/
DEBUG=True
```

### 5. Apply migrations
```bash
python manage.py migrate
```

### 6. Run the development server
```bash
python manage.py runserver
```

## 🏞️ UI Preview

- YouTube: https://youtu.be/G8KSHCtaGm4

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📬 Contact

- **Author**: Anton Bliznuk
- **Email**: bliznukantonmain@gmail.com
- **GitHub**: https://github.com/AntonBliznuk
- **LinkedIn**: https://www.linkedin.com/in/anton-bliznuk-3499b234b
