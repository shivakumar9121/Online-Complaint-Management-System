import os
import unittest
from datetime import datetime, timezone
from app import app, db
from models import User, Category, Complaint, ComplaintTimeline

class OCMSTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def login(self, email, password):
        return self.client.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_01_seed_data_exists(self):
        """Verify seeded categories, users, and complaints exist"""
        with app.app_context():
            admin = User.query.filter_by(email='admin@iiitv.ac.in').first()
            self.assertIsNotNone(admin)
            self.assertEqual(admin.role, 'admin')

            staff = User.query.filter_by(email='staff.sharma@iiitv.ac.in').first()
            self.assertIsNotNone(staff)
            self.assertEqual(staff.role, 'staff')

            student = User.query.filter_by(email='student1@iiitv.ac.in').first()
            self.assertIsNotNone(student)
            self.assertEqual(student.role, 'user')

            complaints = Complaint.query.all()
            self.assertGreater(len(complaints), 0)
            print(f"Verified {len(complaints)} seeded complaints present.")

    def test_02_auth_admin(self):
        """Test admin login, access to admin dashboard, users, and reports"""
        res = self.login('admin@iiitv.ac.in', 'admin123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Executive Control Center', res.data)

        # Test reports page
        res = self.client.get('/admin/reports')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Reports & Analytics', res.data)

        # Test chart API
        res = self.client.get('/api/admin/chart-data')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'status', res.data)
        self.assertIn(b'category', res.data)

        # Test CSV export
        res = self.client.get('/admin/reports/export-csv')
        self.assertEqual(res.status_code, 200)
        self.assertIn('text/csv', res.headers.get('Content-Type', ''))

        self.logout()

    def test_03_auth_staff_flow(self):
        """Test staff login, viewing assigned complaints, updating progress, and resolving"""
        res = self.login('staff.sharma@iiitv.ac.in', 'staff123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Active Work Orders', res.data)

        # Find an assigned complaint
        with app.app_context():
            staff = User.query.filter_by(email='staff.sharma@iiitv.ac.in').first()
            assigned_c = Complaint.query.filter_by(assigned_staff_id=staff.id, status='In Progress').first()
            cid = assigned_c.complaint_id

        # Post progress update
        res = self.client.post(f'/staff/complaint/{cid}/update-progress', data=dict(
            remarks="Testing progress update: inspected cables and hardware."
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Progress update recorded successfully', res.data)

        self.logout()

    def test_04_user_flow(self):
        """Test student registering, logging in, lodging complaint, and checking timeline"""
        # Register new student
        unique_email = f"test_student_{int(datetime.now(timezone.utc).timestamp())}@iiitv.ac.in"
        res = self.client.post('/register', data=dict(
            name="Test Student",
            email=unique_email,
            roll_number="202351999",
            department="B.Tech Computer Science",
            phone="+91 99999 88888",
            password="password123",
            confirm_password="password123"
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Registration successful', res.data)

        # Login with newly registered student
        res = self.login(unique_email, 'password123')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome, Test', res.data)

        # Submit new complaint
        with app.app_context():
            cat = Category.query.first()
            cat_id = cat.id

        res = self.client.post('/complaint/new', data=dict(
            title="Automated Test: Lab 3 switch failure",
            category_id=cat_id,
            priority="High",
            location="Lab 3, Academic Block",
            description="Testing automated complaint submission functionality for SPM Group 37 project."
        ), follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'submitted successfully', res.data)

        self.logout()

    def test_05_role_security(self):
        """Verify role protection: normal student cannot access admin or staff pages"""
        self.login('student1@iiitv.ac.in', 'student123')

        # Try to access admin dashboard
        res = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        # Try to access staff dashboard
        res = self.client.get('/staff/dashboard', follow_redirects=True)
        self.assertIn(b'Access denied', res.data)

        self.logout()

if __name__ == '__main__':
    unittest.main()
