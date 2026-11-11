from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user', 'staff', 'admin'
    roll_number = db.Column(db.String(50), nullable=True)  # Student Roll Number or Employee ID
    department = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Relationships
    complaints = db.relationship('Complaint', backref='submitter', lazy=True, foreign_keys='Complaint.user_id')
    assigned_complaints = db.relationship('Complaint', backref='assigned_staff', lazy=True, foreign_keys='Complaint.assigned_staff_id')
    timeline_logs = db.relationship('ComplaintTimeline', backref='updater', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff(self):
        return self.role == 'staff'

    @property
    def is_user(self):
        return self.role == 'user'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    icon = db.Column(db.String(50), default='bi-folder')
    color = db.Column(db.String(20), default='primary')

    complaints = db.relationship('Complaint', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(30), unique=True, nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='Medium')  # 'Low', 'Medium', 'High', 'Urgent'
    status = db.Column(db.String(30), nullable=False, default='Pending')    # 'Pending', 'Assigned', 'In Progress', 'Resolved', 'Rejected'
    location = db.Column(db.String(150), nullable=False)
    attachment = db.Column(db.String(255), nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_remarks = db.Column(db.Text, nullable=True)
    
    # User feedback upon resolution
    user_rating = db.Column(db.Integer, nullable=True)
    user_feedback = db.Column(db.Text, nullable=True)

    # Status & action history timeline
    timeline = db.relationship('ComplaintTimeline', backref='complaint', lazy=True, cascade='all, delete-orphan', order_by='ComplaintTimeline.created_at.asc()')

    @property
    def status_badge_class(self):
        badges = {
            'Pending': 'bg-warning text-dark',
            'Assigned': 'bg-info text-dark',
            'In Progress': 'bg-primary text-white',
            'Resolved': 'bg-success text-white',
            'Rejected': 'bg-danger text-white'
        }
        return badges.get(self.status, 'bg-secondary text-white')

    @property
    def priority_badge_class(self):
        badges = {
            'Low': 'badge-priority-low',
            'Medium': 'badge-priority-medium',
            'High': 'badge-priority-high',
            'Urgent': 'badge-priority-urgent'
        }
        return badges.get(self.priority, 'badge-priority-medium')

    @property
    def progress_percentage(self):
        steps = {
            'Pending': 25,
            'Assigned': 50,
            'In Progress': 75,
            'Resolved': 100,
            'Rejected': 100
        }
        return steps.get(self.status, 25)

    def __repr__(self):
        return f'<Complaint {self.complaint_id} - {self.status}>'


class ComplaintTimeline(db.Model):
    __tablename__ = 'complaint_timelines'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 'Complaint Submitted', 'Staff Assigned', 'Progress Note', 'Resolved', etc.
    status = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    @property
    def status_badge_class(self):
        badges = {
            'Pending': 'bg-warning text-dark',
            'Assigned': 'bg-info text-dark',
            'In Progress': 'bg-primary text-white',
            'Resolved': 'bg-success text-white',
            'Rejected': 'bg-danger text-white'
        }
        return badges.get(self.status, 'bg-secondary text-white')

    def __repr__(self):
        return f'<ComplaintTimeline {self.complaint_id} - {self.action}>'
