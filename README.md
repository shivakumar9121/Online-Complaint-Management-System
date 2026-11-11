# Online Complaint Management System (OCMS)

> **Software Project Management (SPM) Submission**  
> **Course Project:** Problem 28  
> **Group:** 37  
> **Institution:** Indian Institute of Information Technology Vadodara (IIIT Vadodara)

---

## 👥 Project Team (Group 37)

| S.No | Student Name | Student Roll Number | Role |
| :--- | :--- | :--- | :--- |
| **1** | **Pathlavath Shiva Kumar** | `202351099` | Team Lead / Backend Architect |
| **2** | **Gugulothu Ganesh** | `202351042` | Frontend & UI/UX Developer |
| **3** | **Spandana Vanam** | `202351139` | Database & Models Engineer |
| **4** | **Jay Banoth** | `202351170` | QA, Testing & Documentation |

---

## 📖 Executive Summary & Aim

### What is OCMS?
The **Online Complaint Management System (OCMS)** is a centralized web portal designed for institutional campus environments (IIIT Vadodara) to streamline the process of lodging, reviewing, assigning, tracking, and resolving technical, hostel, academic, and facility complaints.

### The Problem
Traditional manual or email-based complaint handling suffers from:
* Lost or overlooked complaints
* Delayed processing and lack of accountability
* Inability for students to track complaint progress in real-time
* Scattered records and cumbersome manual report generation

### The Solution & Objectives
1. **Centralized Submission:** Direct web portal to lodge complaints with category, location, priority, and optional attachments.
2. **Automated Tracking:** Instant generation of unique tracking identifiers (e.g., `CMP-YYYYMM-XXXX`).
3. **Role-Based Workflows:** Distinct interfaces for **Students/Users**, **Central Administration**, and **Technical Staff**.
4. **Transparent Audit Logs:** Complete status history recording every transition, remark, and timestamp.
5. **Analytics & Reports:** Real-time data visualization via **Chart.js** and one-click **CSV export** for administrative audits.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Backend** | Python 3.10+, Flask 3.x, Gunicorn 21.x+ (WSGI Production Server) |
| **Database** | SQLite (development/demo) / PostgreSQL (production-ready via `DATABASE_URL`), Flask-SQLAlchemy ORM |
| **Authentication** | Flask-Login, Werkzeug Password Hashing (`scrypt`/`pbkdf2`) |
| **Frontend** | HTML5, Modern CSS3, Bootstrap 5.3, Bootstrap Icons |
| **Visualization** | Chart.js 4.x (Doughnut, Bar, Trend Line, and Pie charts) |
| **Testing** | Python `unittest` automated test suite (`test_app.py`, `audit_test.py`) |
| **Deployment** | Render, Gunicorn, Git, GitHub |

---

## 🔑 Demo Accounts & Preloaded Credentials

The database comes pre-seeded with realistic campus accounts across all three roles. The sign-in page includes **1-click autofill buttons** for rapid testing:

| Role | Name & Designation | Email Address | Password |
| :--- | :--- | :--- | :--- |
| **Admin** | Dr. Karan Verma | `admin@iiitv.ac.in` | `admin123` |
| **Staff (IT)** | Vikas Sharma (IT Support Lead) | `staff.sharma@iiitv.ac.in` | `staff123` |
| **Staff (Hostel)** | Ramesh Verma (Hostel Supervisor) | `staff.verma@iiitv.ac.in` | `staff123` |
| **Staff (Mess)** | Sunil Patel (Sanitation Caretaker) | `staff.patel@iiitv.ac.in` | `staff123` |
| **User (Student 1)** | Pathlavath Shiva Kumar (`202351099`) | `student1@iiitv.ac.in` | `student123` |
| **User (Student 2)** | Gugulothu Ganesh (`202351042`) | `student2@iiitv.ac.in` | `student123` |
| **User (Student 3)** | Spandana Vanam (`202351139`) | `student3@iiitv.ac.in` | `student123` |
| **User (Student 4)** | Jay Banoth (`202351170`) | `student4@iiitv.ac.in` | `student123` |

> 💡 **Quick Login Feature:** The login page includes **one-click autofill buttons** for instant testing without manual typing.

---

## 🔄 Lifecycle & Workflow Architecture

```
[Student / User]                     [Central Admin]                     [Technical Staff]
       │                                    │                                    │
       ├─► Lodges Complaint (ID Generated) ─┼────────────────────────────────────┤
       │   Status: [Pending]                │                                    │
       │                                    ├─► Reviews ticket details           │
       │                                    ├─► Assigns Staff & adds note        │
       │                                    │   Status: [Assigned] ─────────────►│
       │                                    │                                    ├─► Inspects site & updates work
       │◄─ Real-time Timeline update ───────┼────────────────────────────────────┤   Status: [In Progress]
       │                                    │                                    │
       │                                    │                                    ├─► Finishes repair & adds remarks
       │◄─ Status: [Resolved] ──────────────┼────────────────────────────────────┤   Status: [Resolved]
       │                                    │                                    │
       ├─► Rates Resolution (1-5 Stars) ────┼────────────────────────────────────┤
       │   & Submits Satisfaction Feedback  │                                    │
```

---

## 📁 System Modules

### 1. User (Student) Module
* **Registration & Secure Login:** Institute email validation, department selection, student roll number capture.
* **Lodge Complaint:**
  * Title and detailed description
  * Category picker (IT & Wi-Fi, Hostel, Academic, Mess & Canteen, Sanitation, Electricity & Water, Library, Sports)
  * Priority level (Low, Medium, High, Urgent)
  * Exact campus location (e.g., *Hostel Block B, Room 304*)
  * Optional file attachment support (PNG, JPG, PDF)
  * Automatic generation of unique complaint UID (`CMP-YYYYMM-XXXX`)
* **Live Status Tracking:** 4-step progress stepper and real-time timeline audit trail.
* **Student Feedback:** Rate resolution 1–5 stars and submit satisfaction feedback.

### 2. Admin Module
* **Executive Dashboard:**
  * Key performance counters: Total, Pending, Assigned, In Progress, Resolved.
  * Urgent/High-priority queue needing immediate attention.
* **Interactive Chart.js Visualizations:**
  * Status Distribution (Doughnut chart)
  * Category & Department Volume (Horizontal bar chart)
  * Daily Inflow Trend (7-day line chart)
  * Priority Breakdown (Pie chart)
* **All Complaints Management:** Multi-criteria search and filter by Status, Category, Priority, and Staff.
* **Staff Assignment:** Assign or reassign tickets to specialized staff with custom instructions.
* **Status Override:** Direct status modifications with audit log remarks.
* **User & Staff Management:**
  * View roster of students, staff, and administrators.
  * Register new technical staff members with department specializations.
  * Activate / Deactivate user accounts.
* **Reports & Data Export:**
  * Summary metrics (Resolution Rate %, Average turnaround time in hours).
  * Category resolution efficiency table.
  * Staff workload and completion rate table.
  * **Export to CSV:** Instant download formatted for Excel/audits.

### 3. Staff Module
* **Staff Dashboard:** Assigned work order counts, pending actions, and active tasks.
* **Assigned Queue:** Filtered list of tickets assigned specifically to the logged-in staff member.
* **Progress Logging:** Add on-site inspection notes, updates status to `In Progress`.
* **Issue Resolution:** Submit official resolution notes (action taken, parts replaced) and mark ticket as `Resolved`.

---

## 🗄️ Database Architecture & Storage on Render

### Schema Overview:
* **`users` Table:** `id` (PK), `email` (Unique), `password_hash`, `name`, `role` (`user`/`staff`/`admin`), `roll_number`, `department`, `phone`, `is_active`, `created_at`
* **`categories` Table:** `id` (PK), `name` (Unique), `description`, `icon`, `color`
* **`complaints` Table:** `id` (PK), `complaint_id` (Unique, e.g. `CMP-202611-1001`), `title`, `description`, `category_id` (FK), `priority`, `status`, `location`, `attachment`, `user_id` (FK), `assigned_staff_id` (FK), `created_at`, `updated_at`, `resolved_at`, `resolution_remarks`, `user_rating`, `user_feedback`
* **`complaint_timelines` Table:** `id` (PK), `complaint_id` (FK), `updated_by_id` (FK), `action`, `status`, `remarks`, `created_at`

### ⚠️ Storage on Render (Important Production Note):
Render Web Services have an **ephemeral disk**. When a web service redeploys, restarts, or wakes from sleep (on free instances), the container's disk is reset to the latest Git commit:
1. **SQLite Database (`ocms.db`):** 
   * On Render free tier, the SQLite file resets to the pre-seeded state upon server restart.
   * **For Persistent Production Storage on Render:**
     * **Recommended:** Use a managed **Render PostgreSQL** database. Set the `DATABASE_URL` environment variable in Render's dashboard. The application automatically detects `DATABASE_URL` and converts `postgres://` to `postgresql://` for SQLAlchemy 2.0.
     * **Alternative:** Attach a **Render Persistent Disk** (mounted e.g. at `/var/data`) and set `DATABASE_URL=sqlite:////var/data/ocms.db`.
2. **User Uploads (`static/uploads/`):**
   * Uploaded documents are kept in `static/uploads/`.
   * **For Persistent File Storage:** Set `UPLOAD_FOLDER=/var/data/uploads` if using a Render disk, or integrate cloud object storage (such as AWS S3 or Cloudinary) for large-scale multi-instance deployments.

---

## 🚀 How to Run Locally

### 1. Prerequisites
Ensure you have **Python 3.10+** installed:
```bash
python --version
```

### 2. Navigate to Project Directory
```bash
cd "c:\Users\pathl\OneDrive\New folder\Documents\Desktop\OCMS"
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application Locally
```bash
python app.py
```
*(The database `ocms.db` will automatically initialize with all tables and realistic demo data on first launch)*

### 5. Access the Web Portal
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
Use the demo quick-login buttons on the sign-in screen to explore the portal as an **Admin**, **Staff**, or **Student**.

---

## 🌐 Deploying to Render

Follow these exact steps to deploy OCMS to Render:

### Step 1: Push Code to GitHub
Ensure you have committed your changes and pushed to your GitHub repository (see [GitHub Instructions](#-github-upload-instructions)).

### Step 2: Create a Web Service on Render
1. Log in to [Render.com](https://render.com).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository (`OCMS`).
4. Configure the Web Service settings:
   * **Name:** `iiitv-ocms` (or your choice)
   * **Region:** Any (e.g., Singapore or Frankfurt)
   * **Branch:** `main`
   * **Runtime:** `Python 3`
   * **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   * **Start Command:**
     ```bash
     gunicorn app:app
     ```

### Step 3: Configure Environment Variables on Render
In the **Environment** section of your Render Web Service dashboard, add:

| Key | Suggested Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(Click "Generate" or set a long random string)* | Used for cryptographic session signing |
| `FLASK_DEBUG` | `false` | Disables debug mode in production |
| `PYTHON_VERSION` | `3.11.9` | Sets standard Python runtime version |
| `DATABASE_URL` | *(Optional)* `postgresql://...` | Set only if using Render PostgreSQL |

Click **Create Web Service**. Render will automatically build the dependencies, start Gunicorn, initialize the database tables with demo data, and assign a live HTTPS URL (e.g. `https://iiitv-ocms.onrender.com`).

---

## 📤 GitHub Upload Instructions

Run these exact commands in your terminal to initialize and push your project to a new GitHub repository:

```bash
# 1. Navigate to the project root
cd "c:\Users\pathl\OneDrive\New folder\Documents\Desktop\OCMS"

# 2. Stage all project files (safe exclusions are handled automatically by .gitignore)
git add .

# 3. Create your initial commit
git commit -m "Initial commit: Complete OCMS project ready for Render deployment"

# 4. Set branch to main
git branch -M main

# 5. Add your GitHub remote repository (replace with your GitHub repository URL)
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>.git

# 6. Push to GitHub
git push -u origin main
```

*(Note: `.gitignore` automatically prevents `ocms.db`, private file uploads, cache files, and virtual environments from being committed to GitHub)*

---

## 🧪 Running Automated Tests & Verification

The project includes two automated test suites:

### 1. Core Test Suite (`test_app.py`)
Covers baseline models, routing, authentication, and database operations:
```bash
python test_app.py
```

### 2. Full 10-Point Functional Audit Suite (`audit_test.py`)
Performs an end-to-end audit of all 10 core requirements:
```bash
python audit_test.py
```

Expected output:
```
Ran 6 tests in 3.1s

OK
```

---

## 🏛️ Academic Submission Details
* **Course:** Software Project Management (SPM)
* **Institution:** Indian Institute of Information Technology Vadodara (IIITV)
* **Problem Number:** 28
* **Group:** 37
* **Academic Year:** 2026
