# 📝 Django To-Do App

A clean and responsive to-do list application built with Django and Bootstrap.  
It allows users to create, edit, delete, and filter tasks using intuitive modal interfaces — no clutter, just productivity.

---

## 🚀 Features Implemented

### ✅ Core Functionality

- **Task Model**  
  Each task has a:
  - `Title` (required)
  - `Description` (optional)
  - `Due Date` (required)
  - `Priority` (High, Medium, Low)
  - `Status` (defaults to Ongoing)

- **Task List Homepage**  
  - Displays all tasks in a table, sorted by due date (default).
  - Includes a sort dropdown to order by:  
    🔹 Due Date  
    🔹 Priority  
    🔹 Status  

- **Create New Task**  
  - Modal opens on clicking "Add Task" button.  
  - Fields are validated inline.  
  - Errors are shown without leaving the page.
  - Default status is automatically set to **Ongoing**.
  - Tasks are color-coded by priority.

- **Edit Task**  
  - Opens a modal pre-filled with task data.
  - Allows editing title, description, due date, priority, and status.
  - Errors are shown inline in the modal.

- **Delete Task**  
  - Opens a confirmation modal.
  - One-click delete with cancel option.

- **Mark as Completed**  
  - Checkbox toggle next to each task.
  - Updates the `status` and visually refreshes the task row.

- **Filter by Status**  
  - Option to filter tasks on the homepage by:
    - ✅ All Tasks
    - 🕐 Ongoing
    - ✔️ Completed

- ⚡ **AJAX Integration**  
  Add/delete/edit tasks without full page reload.

- **Priority Colors**  
  - 🔴 High = Red background  
  - 🟡 Medium = Yellow-ish background  
  - 🟢 Low = Green-ish background

- **Bootstrap Theme & Styling**  
  - All modals, buttons, and inputs follow a consistent, minimal Bootstrap aesthetic.
  - Fonts and colors are inspired by [psiris.co](https://psiris.co) for a clean and modern vibe.

---

## 🛠️ Upcoming Features

These are planned for future commits:

- 📋 **Multiple Task Lists**  
  Allow users to manage more than one list.

---

## 🧪 Tech Stack

- **Python 3.10+**
- **Django 4.x**
- **SQLite** (default, no setup needed)
- **Bootstrap 5**
- **HTML + CSS + JS (Vanilla)**

---
