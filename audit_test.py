import os
import unittest
import io
from datetime import datetime, timezone
from app import app, db, generate_complaint_id
from models import User, Category, Complaint, ComplaintTimeline

class FunctionalAuditTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()

    def setUp(self):
        # Ensure clean session before each test
        self.client.get('/logout', follow_redirects=True)

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    # -------------------------------------------------------------------------
    # Audit 1: User Registration and Login
    # -------------------------------------------------------------------------
    def test_01_user_registration_and_login(self):
        print("\n[AUDIT 1] Testing User Registration and Login...")
        # 1.1 Form validations: Mismatched password
        res = self.client.post('/register', data=dict(
            name="Audit Student",
            email="audit_student@iiitv.ac.in",
            roll_number="202351998",
            department="B.Tech Computer Science",
            phone="+91 98989 89898",
            password="password123",
            confirm_password="mismatchPassword"
        ), follow_redirects=True)
        self.assertIn(b'Passwords do not match', res.data)

        # 1.2 Form validations: Short password (< 6 chars)
        res = self.client.post('/register', data=dict(
            name="Audit Student",
            email="audit_student@iiitv.ac.in",
            roll_number="202351998",
            department="B.Tech Computer Science",
            phone="+91 98989 89898",
            password="123",
            confirm_password="123"
        ), follow_redirects=True)
        self.assertIn(b'Password must be at least 6 characters long', res.data)

        # 1.3 Successful registration
        timestamp = int(datetime.now(timezone.utc).timestamp())
        reg_email = f"audit_user_{timestamp}@iiitv.ac.in"
        res = self.client.post('/register', data=dict(
            name="Audit User Real",
            email=reg_email,
            roll_number=f"ROLL{timestamp}",
            department="B.Tech Information Technology",
            phone="+91 98765 00000",
            password="validPassword123",
            confirm_password="validPassword123"
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Registration successful', res.data)

        # 1.4 Duplicate email registration prevention
        res = self.client.post('/register', data=dict(
            name="Audit User Duplicate",
            email=reg_email,
            roll_number=f"ROLL{timestamp}",
            department="B.Tech Information Technology",
            phone="+91 98765 00000",
            password="validPassword123",
            confirm_password="validPassword123"
        ), follow_redirects=True)
        self.assertIn(b'already exists', res.data)

        # 1.5 Login with invalid password
        res = self.login(reg_email, "wrongPassword")
        self.assertIn(b'Invalid email or password', res.data)

        # 1.6 Login with correct credentials
        res = self.login(reg_email, "validPassword123")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome', res.data)
        self.logout()
        print("  -> PASSED: Registration, password validation, duplicate prevention, and login.")

    # -------------------------------------------------------------------------
    # Audit 2 & 3: Complaint Submission, DB Persistence, Unique ID Generation
    # -------------------------------------------------------------------------
    def test_02_complaint_submission_and_unique_id(self):
        print("\n[AUDIT 2 & 3] Testing Complaint Submission, DB Persistence, and Unique ID...")
        # 3.1 Test Unique ID generator format & sequence
        with app.app_context():
            uid1 = generate_complaint_id()
            self.assertTrue(uid1.startswith("CMP-"))
            parts = uid1.split('-')
            self.assertEqual(len(parts), 3)
            self.assertTrue(parts[1].isdigit())
            self.assertTrue(parts[2].isdigit())
            self.assertGreaterEqual(int(parts[2]), 1001)
            print(f"  -> Generated sample ID: {uid1}")

        # 2.1 Login as student
        self.login('student1@iiitv.ac.in', 'student123')

        # 2.2 Submit with missing mandatory fields
        res = self.client.post('/complaint/new', data=dict(
            title="",
            category_id="",
            location="",
            description=""
        ), follow_redirects=True)
        self.assertIn(b'Please fill in all mandatory fields', res.data)

        # 2.3 Submit with invalid file extension
        with app.app_context():
            category = Category.query.first()
            cat_id = category.id

        bad_file = (io.BytesIO(b"malicious script content"), "hack.exe")
        res = self.client.post('/complaint/new', data=dict(
            title="Audit Test: Invalid extension",
            category_id=cat_id,
            priority="Medium",
            location="Room 101",
            description="Testing invalid file extension rejection.",
            attachment=bad_file
        ), content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'Invalid file format', res.data)

        # 2.4 Submit valid complaint with valid file attachment
        fake_file = (io.BytesIO(b"Simulated complaint photo content"), "evidence.png")
        sub_title = f"Audit Test: Overhead projector bulb burnout {int(datetime.now(timezone.utc).timestamp())}"
        res = self.client.post('/complaint/new', data=dict(
            title=sub_title,
            category_id=cat_id,
            priority="High",
            location="Classroom LH-201",
            description="Projector lamp stopped working during afternoon SPM presentation.",
            attachment=fake_file
        ), content_type='multipart/form-data', follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b'submitted successfully', res.data)

        # Verify DB persistence
        with app.app_context():
            c = Complaint.query.filter_by(title=sub_title).first()
            self.assertIsNotNone(c)
            self.assertEqual(c.status, 'Pending')
            self.assertEqual(c.priority, 'High')
            self.assertEqual(c.location, 'Classroom LH-201')
            self.assertIsNotNone(c.attachment)
            self.assertTrue(c.attachment.endswith('evidence.png'))

            # Verify initial timeline record
            self.assertEqual(len(c.timeline), 1)
            self.assertEqual(c.timeline[0].action, 'Complaint Submitted')
            self.assertEqual(c.timeline[0].status, 'Pending')
            print(f"  -> Verified DB persistence for {c.complaint_id} with attachment: {c.attachment}")

        self.logout()
        print("  -> PASSED: Complaint submission, DB persistence, attachment upload, and unique ID.")

    # -------------------------------------------------------------------------
    # Audit 4, 5, 6: Admin Complaint Management & Staff Assignment
    # -------------------------------------------------------------------------
    def test_03_admin_management_and_staff_assignment(self):
        print("\n[AUDIT 4, 5, 6] Testing Admin Management and Staff Assignment...")
        # Login as Admin
        res = self.login('admin@iiitv.ac.in', 'admin123')
        self.assertEqual(res.status_code, 200)

        # Access Admin Complaints page
        res = self.client.get('/admin/complaints')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'All Campus Complaints', res.data)

        # Test filter by status=Pending
        res = self.client.get('/admin/complaints?status=Pending')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Pending', res.data)

        # Test filter by unassigned staff (-1)
        res = self.client.get('/admin/complaints?staff_id=-1')
        self.assertEqual(res.status_code, 200)

        # Find our submitted complaint or any pending complaint
        with app.app_context():
            pending_c = Complaint.query.filter_by(status='Pending').first()
            self.assertIsNotNone(pending_c)
            cid = pending_c.complaint_id
            staff = User.query.filter_by(role='staff', email='staff.sharma@iiitv.ac.in').first()
            staff_id = staff.id

        # Admin assigns staff with remarks
        res = self.client.post(f'/admin/complaint/{cid}/assign', data=dict(
            staff_id=staff_id,
            remarks="Assigned to Vikas Sharma. Please inspect projector urgently."
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'assigned to', res.data)

        # Verify database state after assignment
        with app.app_context():
            updated_c = Complaint.query.filter_by(complaint_id=cid).first()
            self.assertEqual(updated_c.status, 'Assigned')
            self.assertEqual(updated_c.assigned_staff_id, staff_id)
            latest_log = updated_c.timeline[-1]
            self.assertIn('Staff Assigned', latest_log.action)
            self.assertIn('Instructions: Assigned to Vikas Sharma', latest_log.remarks)

        self.logout()
        print("  -> PASSED: Admin review, filtering, staff assignment, and audit timeline recording.")

    # -------------------------------------------------------------------------
    # Audit 7 & 8: Complete Lifecycle (User Lodge -> Admin Assign -> Staff Progress -> Staff Resolve -> User View & Feedback)
    # -------------------------------------------------------------------------
    def test_04_complete_lifecycle_and_user_feedback(self):
        print("\n[AUDIT 7 & 8] Testing Complete Lifecycle, Staff Resolution, and User Feedback...")
        
        # Step A: Student1 submits a fresh complaint specifically for this workflow
        self.login('student1@iiitv.ac.in', 'student123')
        with app.app_context():
            category = Category.query.first()
            cat_id = category.id

        ts = int(datetime.now(timezone.utc).timestamp())
        unique_title = f"End-to-End Lifecycle: Water Dispenser Noise {ts}"
        res = self.client.post('/complaint/new', data=dict(
            title=unique_title,
            category_id=cat_id,
            priority="Medium",
            location="Hostel Block-B 1st Floor",
            description="The water dispenser compressor is vibrating noisily at night."
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'submitted successfully', res.data)

        with app.app_context():
            c = Complaint.query.filter_by(title=unique_title).first()
            cid = c.complaint_id
            self.assertEqual(c.status, 'Pending')

        self.logout()

        # Step B: Admin assigns to staff.sharma
        self.login('admin@iiitv.ac.in', 'admin123')
        with app.app_context():
            staff = User.query.filter_by(email='staff.sharma@iiitv.ac.in').first()
            staff_id = staff.id

        res = self.client.post(f'/admin/complaint/{cid}/assign', data=dict(
            staff_id=staff_id,
            remarks="Check motor mounting pads."
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.logout()

        # Step C: Staff Vikas Sharma logs in, updates progress, and resolves
        self.login('staff.sharma@iiitv.ac.in', 'staff123')
        
        # Post progress update
        res = self.client.post(f'/staff/complaint/{cid}/update-progress', data=dict(
            remarks="Inspected dispenser motor mounting. Tightened loose chassis screws and ordered rubber damping pads."
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Progress update recorded successfully', res.data)

        with app.app_context():
            c = Complaint.query.filter_by(complaint_id=cid).first()
            self.assertEqual(c.status, 'In Progress')

        # Mark as resolved
        res = self.client.post(f'/staff/complaint/{cid}/resolve', data=dict(
            resolution_notes="Installed rubber isolation bushings under the compressor. Vibration noise eliminated. Tested continuous cooling cycle."
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'marked as resolved successfully', res.data)

        with app.app_context():
            c = Complaint.query.filter_by(complaint_id=cid).first()
            self.assertEqual(c.status, 'Resolved')
            self.assertIsNotNone(c.resolved_at)
            self.assertIn('Installed rubber isolation', c.resolution_remarks)

        self.logout()

        # Step D: Student1 logs back in, tracks status, and submits feedback rating
        self.login('student1@iiitv.ac.in', 'student123')
        res = self.client.get(f'/complaint/{cid}', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Resolved', res.data)
        self.assertIn(b'Official Resolution Remarks', res.data)
        self.assertIn(b'Installed rubber isolation', res.data)

        # Submit 5-star rating & feedback
        res = self.client.post(f'/complaint/{cid}/feedback', data=dict(
            rating=5,
            feedback="Completely fixed! No more vibration noise. Great work Vikas!"
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Your feedback has been recorded', res.data)

        with app.app_context():
            c = Complaint.query.filter_by(complaint_id=cid).first()
            self.assertEqual(c.user_rating, 5)
            self.assertIn('Completely fixed', c.user_feedback)
            # Verify all timeline entries exist: Submitted, Assigned, Progress Note, Resolved, Feedback
            actions = [t.action for t in c.timeline]
            self.assertIn('Complaint Submitted', actions)
            self.assertTrue(any('Staff Assigned' in a for a in actions))
            self.assertIn('Progress Update', actions)
            self.assertIn('Resolved', actions)
            self.assertIn('User Feedback Provided', actions)

        self.logout()
        print("  -> PASSED: Full lifecycle from submission -> admin assignment -> staff update -> resolution -> user feedback.")

    # -------------------------------------------------------------------------
    # Audit 9: Admin Analytics and CSV Reports
    # -------------------------------------------------------------------------
    def test_05_admin_analytics_and_reports(self):
        print("\n[AUDIT 9] Testing Admin Analytics and CSV Reports...")
        self.login('admin@iiitv.ac.in', 'admin123')

        # 9.1 Test Chart.js API endpoint
        res = self.client.get('/api/admin/chart-data')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertIn('status', json_data)
        self.assertIn('category', json_data)
        self.assertIn('priority', json_data)
        self.assertIn('trend', json_data)
        self.assertEqual(len(json_data['status']['labels']), 5)
        print(f"  -> Chart status distribution: {dict(zip(json_data['status']['labels'], json_data['status']['counts']))}")

        # 9.2 Test Reports page calculations
        res = self.client.get('/admin/reports')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Category & Department Performance', res.data)
        self.assertIn(b'Technical Staff Workload & Efficiency', res.data)
        self.assertIn(b'Resolution Rate', res.data)

        # 9.3 Test CSV Export
        res = self.client.get('/admin/reports/export-csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.headers.get('Content-Type', ''))
        csv_content = res.data.decode('utf-8')
        self.assertIn('Complaint ID,Title,Category,Priority,Status', csv_content)
        self.assertIn('CMP-', csv_content)
        print(f"  -> Generated CSV rows count: {len(csv_content.splitlines())}")

        self.logout()
        print("  -> PASSED: Analytics charts API, KPI indicators, category/staff metrics, and CSV export.")

    # -------------------------------------------------------------------------
    # Audit 10: Role-Based Access Control and Unauthorized Route Protection
    # -------------------------------------------------------------------------
    def test_06_rbac_and_route_protection(self):
        print("\n[AUDIT 10] Testing Role-Based Access Control (RBAC) and Protection...")
        # 10.1 Unauthenticated access to protected routes
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Please sign in to access this page', res.data)

        res = self.client.get('/staff/dashboard', follow_redirects=True)
        self.assertIn(b'Please sign in to access this page', res.data)

        res = self.client.get('/complaint/new', follow_redirects=True)
        self.assertIn(b'Please sign in to access this page', res.data)

        # 10.2 Student attempting to access Admin & Staff routes
        self.login('student1@iiitv.ac.in', 'student123')
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        res = self.client.get('/admin/users', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        res = self.client.get('/staff/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        res = self.client.get('/staff/complaints', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        # 10.3 Student attempting to view another student's complaint
        with app.app_context():
            other_user = User.query.filter_by(email='student2@iiitv.ac.in').first()
            other_c = Complaint.query.filter_by(user_id=other_user.id).first()
            other_cid = other_c.complaint_id

        res = self.client.get(f'/complaint/{other_cid}', follow_redirects=True)
        self.assertIn(b'You do not have permission to view this complaint', res.data)

        self.logout()

        # 10.4 Staff attempting to access Admin routes
        self.login('staff.sharma@iiitv.ac.in', 'staff123')
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        res = self.client.get('/admin/reports', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        # 10.5 Staff attempting to view a complaint NOT assigned to them
        with app.app_context():
            other_staff = User.query.filter_by(email='staff.verma@iiitv.ac.in').first()
            verma_c = Complaint.query.filter_by(assigned_staff_id=other_staff.id).first()
            verma_cid = verma_c.complaint_id

        res = self.client.get(f'/complaint/{verma_cid}', follow_redirects=True)
        self.assertIn(b'This complaint is not assigned to you', res.data)

        self.logout()
        print("  -> PASSED: All unauthenticated, cross-role, and cross-user boundaries are protected.")

if __name__ == '__main__':
    unittest.main()
