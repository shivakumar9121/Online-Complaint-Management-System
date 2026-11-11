import os
import csv
import io
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, Response, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Category, Complaint, ComplaintTimeline
from seed_data import seed_database

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please sign in to access this page."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# -------------------------------------------------------------------------
# Authorization Decorators
# -------------------------------------------------------------------------
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please sign in to access this page.", "info")
                return redirect(url_for('login', next=request.url))
            if current_user.role not in roles:
                flash("Access denied: You do not have permission to view this resource.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_complaint_id():
    now_str = datetime.now(timezone.utc).strftime("%Y%m")
    prefix = f"CMP-{now_str}-"
    # Find all complaints matching this prefix to extract highest sequence number
    existing = Complaint.query.filter(Complaint.complaint_id.like(f"{prefix}%")).all()
    max_num = 1000
    for c in existing:
        try:
            parts = c.complaint_id.split('-')
            if len(parts) >= 3 and parts[-1].isdigit():
                val = int(parts[-1])
                if val > max_num:
                    max_num = val
        except (ValueError, IndexError):
            pass
    next_num = max_num + 1
    uid = f"{prefix}{next_num:04d}"
    while Complaint.query.filter_by(complaint_id=uid).first():
        next_num += 1
        uid = f"{prefix}{next_num:04d}"
    return uid


# -------------------------------------------------------------------------
# Template Context Processor
# -------------------------------------------------------------------------
@app.context_processor
def inject_global_data():
    categories = Category.query.order_by(Category.name.asc()).all() if db.session else []
    return {
        'all_categories': categories,
        'current_year': datetime.now(timezone.utc).year,
        'project_meta': {
            'code': 'Problem 28',
            'group': 'Group 37',
            'institution': 'IIIT Vadodara',
            'subject': 'Software Project Management'
        }
    }


# -------------------------------------------------------------------------
# General & Auth Routes
# -------------------------------------------------------------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('auth/login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash("Please enter both email address and password.", "danger")
            return render_template('auth/login.html', email=email)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash("Your account has been deactivated. Please contact the administrator.", "danger")
                return render_template('auth/login.html', email=email)

            login_user(user, remember=remember)
            flash(f"Welcome back, {user.name}!", "success")

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password. Please verify and try again.", "danger")

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        roll_number = request.form.get('roll_number', '').strip()
        department = request.form.get('department', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validation
        if not name or not email or not password:
            flash("Name, email, and password are required.", "danger")
            return render_template('auth/register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('auth/register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists. Please login instead.", "warning")
            return redirect(url_for('login'))

        # Create user with role 'user'
        new_user = User(
            name=name,
            email=email,
            roll_number=roll_number,
            department=department or 'General',
            phone=phone,
            role='user',
            is_active=True
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'staff':
        return redirect(url_for('staff_dashboard'))
    else:
        return redirect(url_for('user_dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        if not name:
            flash("Name cannot be empty.", "danger")
            return redirect(url_for('profile'))

        current_user.name = name
        current_user.phone = phone
        current_user.department = department

        if new_password:
            if not current_user.check_password(current_password):
                flash("Current password is incorrect.", "danger")
                return redirect(url_for('profile'))
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return redirect(url_for('profile'))
            current_user.set_password(new_password)
            flash("Profile and password updated successfully!", "success")
        else:
            flash("Profile updated successfully!", "success")

        db.session.commit()
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)


# -------------------------------------------------------------------------
# User Module Routes
# -------------------------------------------------------------------------
@app.route('/user/dashboard')
@role_required('user')
def user_dashboard():
    user_complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    
    total = len(user_complaints)
    pending = sum(1 for c in user_complaints if c.status == 'Pending')
    assigned = sum(1 for c in user_complaints if c.status == 'Assigned')
    in_progress = sum(1 for c in user_complaints if c.status == 'In Progress')
    resolved = sum(1 for c in user_complaints if c.status == 'Resolved')

    recent_complaints = user_complaints[:5]

    return render_template(
        'user/dashboard.html',
        total=total,
        pending=pending,
        assigned=assigned,
        in_progress=in_progress,
        resolved=resolved,
        recent_complaints=recent_complaints
    )


@app.route('/user/complaints')
@role_required('user')
def user_complaints():
    status = request.args.get('status', '').strip()
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()

    query = Complaint.query.filter_by(user_id=current_user.id)

    if status:
        query = query.filter_by(status=status)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Complaint.complaint_id.ilike(search_filter)) |
            (Complaint.title.ilike(search_filter)) |
            (Complaint.description.ilike(search_filter)) |
            (Complaint.location.ilike(search_filter))
        )

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return render_template('user/my_complaints.html', complaints=complaints, selected_status=status, selected_category=category_id, search=search)


@app.route('/complaint/new', methods=['GET', 'POST'])
@role_required('user')
def submit_complaint():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id', type=int)
        priority = request.form.get('priority', 'Medium')
        location = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()

        # Server-side validation
        if not title or not category_id or not location or not description:
            flash("Please fill in all mandatory fields.", "danger")
            return redirect(url_for('submit_complaint'))

        category = db.session.get(Category, category_id)
        if not category:
            flash("Invalid category selected.", "danger")
            return redirect(url_for('submit_complaint'))

        # Handle optional attachment
        attachment_filename = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    safe_name = secure_filename(file.filename)
                    unique_prefix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S_")
                    attachment_filename = unique_prefix + safe_name
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename))
                else:
                    flash("Invalid file format. Allowed file formats are: PNG, JPG, JPEG, GIF, PDF, DOC, DOCX, TXT.", "danger")
                    return redirect(url_for('submit_complaint'))

        # Generate unique Complaint ID
        cid = generate_complaint_id()

        new_complaint = Complaint(
            complaint_id=cid,
            title=title,
            description=description,
            category_id=category_id,
            priority=priority,
            status='Pending',
            location=location,
            attachment=attachment_filename,
            user_id=current_user.id
        )
        db.session.add(new_complaint)
        db.session.flush()

        # Add initial timeline entry
        timeline_entry = ComplaintTimeline(
            complaint_id=new_complaint.id,
            updated_by_id=current_user.id,
            action="Complaint Submitted",
            status="Pending",
            remarks=f"Complaint lodged by {current_user.name}."
        )
        db.session.add(timeline_entry)
        db.session.commit()

        flash(f"Complaint {cid} submitted successfully! You can track its status here.", "success")
        return redirect(url_for('complaint_detail', complaint_id=cid))

    return render_template('user/submit_complaint.html')


@app.route('/complaint/<string:complaint_id>')
@login_required
def complaint_detail(complaint_id):
    complaint = Complaint.query.filter_by(complaint_id=complaint_id).first_or_404()

    # Permission check: regular users can only see their own complaints
    if current_user.role == 'user' and complaint.user_id != current_user.id:
        flash("You do not have permission to view this complaint.", "danger")
        return redirect(url_for('user_dashboard'))

    # Staff can only view assigned complaints unless they are admin
    if current_user.role == 'staff' and complaint.assigned_staff_id != current_user.id:
        flash("This complaint is not assigned to you.", "warning")
        return redirect(url_for('staff_dashboard'))

    staff_members = User.query.filter_by(role='staff', is_active=True).all() if current_user.role == 'admin' else []

    return render_template(
        'complaint_detail.html',
        complaint=complaint,
        staff_members=staff_members
    )


@app.route('/complaint/<string:complaint_id>/feedback', methods=['POST'])
@role_required('user')
def submit_feedback(complaint_id):
    complaint = Complaint.query.filter_by(complaint_id=complaint_id, user_id=current_user.id).first_or_404()

    if complaint.status != 'Resolved':
        flash("Feedback can only be submitted for resolved complaints.", "warning")
        return redirect(url_for('complaint_detail', complaint_id=complaint_id))

    rating = request.form.get('rating', type=int)
    feedback_text = request.form.get('feedback', '').strip()

    if not rating or rating < 1 or rating > 5:
        flash("Please provide a valid rating between 1 and 5.", "danger")
        return redirect(url_for('complaint_detail', complaint_id=complaint_id))

    complaint.user_rating = rating
    complaint.user_feedback = feedback_text

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        updated_by_id=current_user.id,
        action="User Feedback Provided",
        status=complaint.status,
        remarks=f"User rated resolution {rating}/5 stars. Feedback: {feedback_text if feedback_text else 'None provided'}"
    )
    db.session.add(timeline_entry)
    db.session.commit()

    flash("Thank you! Your feedback has been recorded.", "success")
    return redirect(url_for('complaint_detail', complaint_id=complaint_id))


# -------------------------------------------------------------------------
# Admin Module Routes
# -------------------------------------------------------------------------
@app.route('/admin/dashboard')
@role_required('admin')
def admin_dashboard():
    total_complaints = Complaint.query.count()
    pending_count = Complaint.query.filter_by(status='Pending').count()
    assigned_count = Complaint.query.filter_by(status='Assigned').count()
    in_progress_count = Complaint.query.filter_by(status='In Progress').count()
    resolved_count = Complaint.query.filter_by(status='Resolved').count()

    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()

    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(8).all()
    urgent_pending = Complaint.query.filter(
        Complaint.status.in_(['Pending', 'Assigned']),
        Complaint.priority.in_(['Urgent', 'High'])
    ).order_by(Complaint.created_at.asc()).limit(5).all()

    staff_members = User.query.filter_by(role='staff', is_active=True).all()

    return render_template(
        'admin/dashboard.html',
        total=total_complaints,
        pending=pending_count,
        assigned=assigned_count,
        in_progress=in_progress_count,
        resolved=resolved_count,
        total_users=total_users,
        total_staff=total_staff,
        recent_complaints=recent_complaints,
        urgent_pending=urgent_pending,
        staff_members=staff_members
    )


@app.route('/admin/complaints')
@role_required('admin')
def admin_complaints():
    status = request.args.get('status', '').strip()
    category_id = request.args.get('category_id', type=int)
    priority = request.args.get('priority', '').strip()
    staff_id = request.args.get('staff_id', type=int)
    search = request.args.get('search', '').strip()

    query = Complaint.query

    if status:
        query = query.filter(Complaint.status == status)
    if category_id:
        query = query.filter(Complaint.category_id == category_id)
    if priority:
        query = query.filter(Complaint.priority == priority)
    if staff_id == -1:
        query = query.filter(Complaint.assigned_staff_id.is_(None))
    elif staff_id:
        query = query.filter(Complaint.assigned_staff_id == staff_id)
    if search:
        search_filter = f"%{search}%"
        query = query.join(User, Complaint.user_id == User.id).filter(
            (Complaint.complaint_id.ilike(search_filter)) |
            (Complaint.title.ilike(search_filter)) |
            (Complaint.location.ilike(search_filter)) |
            (User.name.ilike(search_filter)) |
            (User.roll_number.ilike(search_filter))
        )

    complaints = query.order_by(Complaint.created_at.desc()).all()
    staff_members = User.query.filter_by(role='staff', is_active=True).all()

    return render_template(
        'admin/complaints.html',
        complaints=complaints,
        staff_members=staff_members,
        selected_status=status,
        selected_category=category_id,
        selected_priority=priority,
        selected_staff=staff_id,
        search=search
    )


@app.route('/admin/complaint/<string:complaint_id>/assign', methods=['POST'])
@role_required('admin')
def admin_assign_complaint(complaint_id):
    complaint = Complaint.query.filter_by(complaint_id=complaint_id).first_or_404()
    staff_id = request.form.get('staff_id', type=int)
    admin_remarks = request.form.get('remarks', '').strip()

    if not staff_id:
        flash("Please choose a valid staff member to assign.", "danger")
        return redirect(url_for('complaint_detail', complaint_id=complaint_id))

    staff = User.query.filter_by(id=staff_id, role='staff').first()
    if not staff:
        flash("Selected staff member not found.", "danger")
        return redirect(url_for('complaint_detail', complaint_id=complaint_id))

    complaint.assigned_staff_id = staff.id
    
    # If it was Pending, advance to Assigned
    if complaint.status == 'Pending':
        complaint.status = 'Assigned'

    action_text = f"Staff Assigned: {staff.name}"
    remarks_text = f"Assigned by Admin {current_user.name} to {staff.name} ({staff.department})."
    if admin_remarks:
        remarks_text += f" Instructions: {admin_remarks}"

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        updated_by_id=current_user.id,
        action=action_text,
        status=complaint.status,
        remarks=remarks_text
    )
    db.session.add(timeline_entry)
    db.session.commit()

    flash(f"Complaint {complaint.complaint_id} assigned to {staff.name} successfully.", "success")
    return redirect(url_for('complaint_detail', complaint_id=complaint_id))


@app.route('/admin/complaint/<string:complaint_id>/update-status', methods=['POST'])
@role_required('admin')
def admin_update_status(complaint_id):
    complaint = Complaint.query.filter_by(complaint_id=complaint_id).first_or_404()
    new_status = request.form.get('status', '').strip()
    priority = request.form.get('priority', '').strip()
    remarks = request.form.get('remarks', '').strip()

    valid_statuses = ['Pending', 'Assigned', 'In Progress', 'Resolved', 'Rejected']
    if new_status and new_status in valid_statuses:
        old_status = complaint.status
        complaint.status = new_status
        if new_status == 'Resolved':
            if not complaint.resolved_at:
                complaint.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if remarks:
                complaint.resolution_remarks = remarks
        elif old_status == 'Resolved' and new_status != 'Resolved':
            complaint.resolved_at = None

        if priority and priority in ['Low', 'Medium', 'High', 'Urgent']:
            complaint.priority = priority

        action_desc = f"Status changed to {new_status}"
        timeline_entry = ComplaintTimeline(
            complaint_id=complaint.id,
            updated_by_id=current_user.id,
            action=action_desc,
            status=new_status,
            remarks=remarks or f"Status updated from {old_status} to {new_status} by Admin."
        )
        db.session.add(timeline_entry)
        db.session.commit()

        flash(f"Complaint status updated to '{new_status}'.", "success")
    else:
        flash("Invalid status selected.", "danger")

    return redirect(url_for('complaint_detail', complaint_id=complaint_id))


@app.route('/admin/users')
@role_required('admin')
def admin_users():
    role_filter = request.args.get('role', '').strip()
    search = request.args.get('search', '').strip()

    query = User.query

    if role_filter:
        query = query.filter_by(role=role_filter)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.name.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (User.roll_number.ilike(search_filter)) |
            (User.department.ilike(search_filter))
        )

    users = query.order_by(User.role.asc(), User.name.asc()).all()
    return render_template('admin/users.html', users=users, selected_role=role_filter, search=search)


@app.route('/admin/staff/new', methods=['POST'])
@role_required('admin')
def admin_create_staff():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    staff_id = request.form.get('staff_id', '').strip()
    department = request.form.get('department', '').strip()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '')

    if not name or not email or not password:
        flash("Name, email, and password are required.", "danger")
        return redirect(url_for('admin_users'))

    if User.query.filter_by(email=email).first():
        flash("A user with this email address already exists.", "warning")
        return redirect(url_for('admin_users'))

    new_staff = User(
        name=name,
        email=email,
        roll_number=staff_id,
        department=department or 'Maintenance & Support',
        phone=phone,
        role='staff',
        is_active=True
    )
    new_staff.set_password(password)
    db.session.add(new_staff)
    db.session.commit()

    flash(f"Staff account for '{name}' created successfully!", "success")
    return redirect(url_for('admin_users'))


@app.route('/admin/user/<int:user_id>/toggle-status', methods=['POST'])
@role_required('admin')
def admin_toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrative account.", "danger")
        return redirect(url_for('admin_users'))

    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    flash(f"User {user.name} ({user.email}) has been {status_str}.", "info")
    return redirect(url_for('admin_users'))


@app.route('/admin/reports')
@role_required('admin')
def admin_reports():
    total_complaints = Complaint.query.count()
    resolved_complaints = Complaint.query.filter_by(status='Resolved').count()
    resolution_rate = round((resolved_complaints / total_complaints * 100), 1) if total_complaints > 0 else 0

    # Calculate average resolution time
    resolved_items = Complaint.query.filter(Complaint.status == 'Resolved', Complaint.resolved_at.isnot(None)).all()
    avg_hours = 0
    if resolved_items:
        total_time = sum((c.resolved_at - c.created_at).total_seconds() for c in resolved_items)
        avg_hours = round(total_time / len(resolved_items) / 3600, 1)

    # Category performance
    categories = Category.query.all()
    cat_stats = []
    for cat in categories:
        cat_total = Complaint.query.filter_by(category_id=cat.id).count()
        cat_resolved = Complaint.query.filter_by(category_id=cat.id, status='Resolved').count()
        cat_pending = Complaint.query.filter_by(category_id=cat.id, status='Pending').count()
        rate = round((cat_resolved / cat_total * 100), 1) if cat_total > 0 else 0
        cat_stats.append({
            'name': cat.name,
            'total': cat_total,
            'resolved': cat_resolved,
            'pending': cat_pending,
            'rate': rate
        })

    # Staff performance
    staff_users = User.query.filter_by(role='staff').all()
    staff_stats = []
    for staff in staff_users:
        assigned_c = Complaint.query.filter_by(assigned_staff_id=staff.id).count()
        resolved_c = Complaint.query.filter_by(assigned_staff_id=staff.id, status='Resolved').count()
        in_prog_c = Complaint.query.filter_by(assigned_staff_id=staff.id, status='In Progress').count()
        rate = round((resolved_c / assigned_c * 100), 1) if assigned_c > 0 else 0
        staff_stats.append({
            'name': staff.name,
            'department': staff.department,
            'assigned': assigned_c,
            'in_progress': in_prog_c,
            'resolved': resolved_c,
            'rate': rate
        })

    return render_template(
        'admin/reports.html',
        total=total_complaints,
        resolved=resolved_complaints,
        resolution_rate=resolution_rate,
        avg_hours=avg_hours,
        cat_stats=cat_stats,
        staff_stats=staff_stats
    )


@app.route('/admin/reports/export-csv')
@role_required('admin')
def export_complaints_csv():
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Complaint ID', 'Title', 'Category', 'Priority', 'Status',
        'Location', 'Submitted By', 'Student/Emp ID', 'Assigned Staff',
        'Created Date', 'Resolved Date', 'User Rating', 'Resolution Remarks'
    ])

    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()
    for c in complaints:
        writer.writerow([
            c.complaint_id,
            c.title,
            c.category.name if c.category else 'N/A',
            c.priority,
            c.status,
            c.location,
            c.submitter.name if c.submitter else 'N/A',
            c.submitter.roll_number if c.submitter else 'N/A',
            c.assigned_staff.name if c.assigned_staff else 'Unassigned',
            c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else '',
            c.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if c.resolved_at else '',
            f"{c.user_rating} / 5" if c.user_rating else 'Not Rated',
            c.resolution_remarks or ''
        ])

    output.seek(0)
    filename = f"OCMS_IIITV_Complaints_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# -------------------------------------------------------------------------
# Staff Module Routes
# -------------------------------------------------------------------------
@app.route('/staff/dashboard')
@role_required('staff')
def staff_dashboard():
    staff_complaints = Complaint.query.filter_by(assigned_staff_id=current_user.id).order_by(Complaint.created_at.desc()).all()

    total_assigned = len(staff_complaints)
    pending_action = sum(1 for c in staff_complaints if c.status == 'Assigned')
    in_progress = sum(1 for c in staff_complaints if c.status == 'In Progress')
    resolved = sum(1 for c in staff_complaints if c.status == 'Resolved')

    recent_tasks = staff_complaints[:6]

    return render_template(
        'staff/dashboard.html',
        total_assigned=total_assigned,
        pending_action=pending_action,
        in_progress=in_progress,
        resolved=resolved,
        recent_tasks=recent_tasks
    )


@app.route('/staff/complaints')
@role_required('staff')
def staff_complaints():
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    search = request.args.get('search', '').strip()

    query = Complaint.query.filter_by(assigned_staff_id=current_user.id)

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Complaint.complaint_id.ilike(search_filter)) |
            (Complaint.title.ilike(search_filter)) |
            (Complaint.location.ilike(search_filter))
        )

    complaints = query.order_by(Complaint.created_at.desc()).all()
    return render_template('staff/complaints.html', complaints=complaints, selected_status=status, selected_priority=priority, search=search)


@app.route('/staff/complaint/<string:complaint_id>/update-progress', methods=['POST'])
@role_required('staff')
def staff_update_progress(complaint_id):
    complaint = Complaint.query.filter_by(complaint_id=complaint_id, assigned_staff_id=current_user.id).first_or_404()
    remarks = request.form.get('remarks', '').strip()

    if not remarks:
        flash("Please provide progress details or action taken.", "danger")
        return redirect(url_for('complaint_detail', complaint_id=complaint_id))

    # Move status to 'In Progress' if it was 'Assigned'
    if complaint.status == 'Assigned':
        complaint.status = 'In Progress'

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        updated_by_id=current_user.id,
        action="Progress Update",
        status=complaint.status,
        remarks=f"{remarks} (Logged by {current_user.name})"
    )
    db.session.add(timeline_entry)
    db.session.commit()

    flash("Progress update recorded successfully.", "success")
    return redirect(url_for('complaint_detail', complaint_id=complaint_id))


@app.route('/staff/complaint/<string:complaint_id>/resolve', methods=['POST'])
@role_required('staff')
def staff_resolve_complaint(complaint_id):
    complaint = Complaint.query.filter_by(complaint_id=complaint_id, assigned_staff_id=current_user.id).first_or_404()
    resolution_notes = request.form.get('resolution_notes', '').strip()

    if not resolution_notes:
        flash("Please enter resolution remarks detailing the fix provided.", "danger")
        return redirect(url_for('complaint_detail', complaint_id=complaint_id))

    complaint.status = 'Resolved'
    complaint.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
    complaint.resolution_remarks = resolution_notes

    timeline_entry = ComplaintTimeline(
        complaint_id=complaint.id,
        updated_by_id=current_user.id,
        action="Resolved",
        status="Resolved",
        remarks=f"Complaint marked as resolved: {resolution_notes}"
    )
    db.session.add(timeline_entry)
    db.session.commit()

    flash(f"Complaint {complaint.complaint_id} marked as resolved successfully!", "success")
    return redirect(url_for('complaint_detail', complaint_id=complaint_id))


# -------------------------------------------------------------------------
# Analytics & Chart.js API
# -------------------------------------------------------------------------
@app.route('/api/admin/chart-data')
@role_required('admin')
def admin_chart_data():
    # 1. Complaints by Status
    statuses = ['Pending', 'Assigned', 'In Progress', 'Resolved', 'Rejected']
    status_counts = [Complaint.query.filter_by(status=s).count() for s in statuses]

    # 2. Complaints by Category
    categories = Category.query.all()
    cat_labels = [c.name for c in categories]
    cat_counts = [Complaint.query.filter_by(category_id=c.id).count() for c in categories]

    # 3. Priority Breakdown
    priorities = ['Low', 'Medium', 'High', 'Urgent']
    priority_counts = [Complaint.query.filter_by(priority=p).count() for p in priorities]

    # 4. Weekly/Trend Data (last 7 days)
    today = datetime.now(timezone.utc).date()
    trend_labels = []
    trend_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())
        cnt = Complaint.query.filter(Complaint.created_at >= day_start, Complaint.created_at <= day_end).count()
        trend_labels.append(day.strftime("%b %d"))
        trend_counts.append(cnt)

    return jsonify({
        'status': {
            'labels': statuses,
            'counts': status_counts
        },
        'category': {
            'labels': cat_labels,
            'counts': cat_counts
        },
        'priority': {
            'labels': priorities,
            'counts': priority_counts
        },
        'trend': {
            'labels': trend_labels,
            'counts': trend_counts
        }
    })


# -------------------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


# -------------------------------------------------------------------------
# Initialization
# -------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    seed_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host='0.0.0.0', port=port, debug=debug)
