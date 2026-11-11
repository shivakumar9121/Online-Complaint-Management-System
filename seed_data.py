import os
from datetime import datetime, timedelta, timezone
from models import db, User, Category, Complaint, ComplaintTimeline

def seed_database():
    """Seed initial categories, demo users, and realistic sample complaints."""
    # Check if database is already seeded
    if User.query.first():
        return

    print("Seeding database with initial data...")

    # Optional environment variable overrides for initial passwords (default demo passwords preserved)
    admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
    staff_password = os.environ.get('DEFAULT_STAFF_PASSWORD', 'staff123')
    student_password = os.environ.get('DEFAULT_STUDENT_PASSWORD', 'student123')

    # 1. Categories
    categories = [
        Category(name="IT & Wi-Fi Network", description="Campus Wi-Fi, LAN, portal access, email and lab computers", icon="bi-wifi", color="primary"),
        Category(name="Hostel & Room Maintenance", description="Hostel rooms, furniture, doors, windows and locks", icon="bi-building", color="info"),
        Category(name="Academic & Classrooms", description="Lecture halls, smart boards, audio-visual, labs and projectors", icon="bi-mortarboard", color="success"),
        Category(name="Mess & Canteen Food", description="Food quality, hygiene, mess timings and kitchen issues", icon="bi-cup-hot", color="warning"),
        Category(name="Sanitation & Hygiene", description="Washroom cleanliness, garbage disposal and campus pest control", icon="bi-trash3", color="secondary"),
        Category(name="Electricity & Water Supply", description="Power outages, geysers, RO filters and water availability", icon="bi-lightning-charge", color="danger"),
        Category(name="Library & Study Facilities", description="Book borrowing, reading room AC, digital catalog", icon="bi-book", color="dark"),
        Category(name="Sports & Gymnasium", description="Gym equipment, badminton court lighting, sports gear", icon="bi-trophy", color="primary")
    ]
    db.session.add_all(categories)
    db.session.commit()

    cat_map = {c.name: c.id for c in Category.query.all()}

    # 2. Users (Admin, Staff, Students)
    admin = User(
        email="admin@iiitv.ac.in",
        name="Dr. Karan Verma",
        role="admin",
        roll_number="EMP-ADMIN-01",
        department="Central Administration",
        phone="+91 98765 43210"
    )
    admin.set_password(admin_password)

    staff_it = User(
        email="staff.sharma@iiitv.ac.in",
        name="Vikas Sharma (IT Support Lead)",
        role="staff",
        roll_number="EMP-STAFF-101",
        department="IT & Wi-Fi Services",
        phone="+91 98765 43211"
    )
    staff_it.set_password(staff_password)

    staff_hostel = User(
        email="staff.verma@iiitv.ac.in",
        name="Ramesh Verma (Hostel Supervisor)",
        role="staff",
        roll_number="EMP-STAFF-102",
        department="Hostel & Infrastructure",
        phone="+91 98765 43212"
    )
    staff_hostel.set_password(staff_password)

    staff_mess = User(
        email="staff.patel@iiitv.ac.in",
        name="Sunil Patel (Sanitation & Mess Caretaker)",
        role="staff",
        roll_number="EMP-STAFF-103",
        department="Mess & Sanitation",
        phone="+91 98765 43213"
    )
    staff_mess.set_password(staff_password)

    student1 = User(
        email="student1@iiitv.ac.in",
        name="Pathlavath Shiva Kumar",
        role="user",
        roll_number="202351099",
        department="B.Tech Computer Science",
        phone="+91 91234 56789"
    )
    student1.set_password(student_password)

    student2 = User(
        email="student2@iiitv.ac.in",
        name="Gugulothu Ganesh",
        role="user",
        roll_number="202351042",
        department="B.Tech Information Technology",
        phone="+91 91234 56788"
    )
    student2.set_password(student_password)

    student3 = User(
        email="student3@iiitv.ac.in",
        name="Spandana Vanam",
        role="user",
        roll_number="202351139",
        department="B.Tech Computer Science",
        phone="+91 91234 56787"
    )
    student3.set_password(student_password)

    student4 = User(
        email="student4@iiitv.ac.in",
        name="Jay Banoth",
        role="user",
        roll_number="202351170",
        department="B.Tech Computer Science",
        phone="+91 91234 56786"
    )
    student4.set_password(student_password)

    db.session.add_all([admin, staff_it, staff_hostel, staff_mess, student1, student2, student3, student4])
    db.session.commit()

    # 3. Sample Complaints with realistic timeline
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Complaint 1: In Progress
    c1 = Complaint(
        complaint_id="CMP-202611-1001",
        title="Wi-Fi connectivity keeps dropping on 3rd Floor Hostel Block B",
        description="The Wi-Fi access point in the corridor of 3rd floor Block-B frequent drops connections every 10 minutes. Students are unable to attend online lab sessions or submit assignments.",
        category_id=cat_map["IT & Wi-Fi Network"],
        priority="High",
        status="In Progress",
        location="Hostel Block-B, 3rd Floor Corridor AP-3",
        user_id=student1.id,
        assigned_staff_id=staff_it.id,
        created_at=now - timedelta(days=2, hours=4),
        updated_at=now - timedelta(hours=6)
    )
    db.session.add(c1)
    db.session.flush()

    t1_1 = ComplaintTimeline(
        complaint_id=c1.id,
        updated_by_id=student1.id,
        action="Complaint Submitted",
        status="Pending",
        remarks="Initial complaint logged by student.",
        created_at=now - timedelta(days=2, hours=4)
    )
    t1_2 = ComplaintTimeline(
        complaint_id=c1.id,
        updated_by_id=admin.id,
        action="Staff Assigned",
        status="Assigned",
        remarks="Assigned to IT Support Lead Vikas Sharma for router diagnosis.",
        created_at=now - timedelta(days=1, hours=8)
    )
    t1_3 = ComplaintTimeline(
        complaint_id=c1.id,
        updated_by_id=staff_it.id,
        action="Progress Note",
        status="In Progress",
        remarks="Inspected AP-3 hardware. Firmware update initiated and replacement PoE injector requisitioned.",
        created_at=now - timedelta(hours=6)
    )
    db.session.add_all([t1_1, t1_2, t1_3])

    # Complaint 2: Assigned
    c2 = Complaint(
        complaint_id="CMP-202611-1002",
        title="Continuous water leakage from tap in Hostel Block A 2nd floor washroom",
        description="The main washbasin tap is continuously leaking clean water leading to slippery floor and water wastage. Immediate plumber attention required.",
        category_id=cat_map["Electricity & Water Supply"],
        priority="Urgent",
        status="Assigned",
        location="Hostel Block-A, 2nd Floor Common Washroom",
        user_id=student2.id,
        assigned_staff_id=staff_hostel.id,
        created_at=now - timedelta(days=1, hours=2),
        updated_at=now - timedelta(hours=14)
    )
    db.session.add(c2)
    db.session.flush()

    t2_1 = ComplaintTimeline(
        complaint_id=c2.id,
        updated_by_id=student2.id,
        action="Complaint Submitted",
        status="Pending",
        remarks="Urgent water leakage reported.",
        created_at=now - timedelta(days=1, hours=2)
    )
    t2_2 = ComplaintTimeline(
        complaint_id=c2.id,
        updated_by_id=admin.id,
        action="Staff Assigned",
        status="Assigned",
        remarks="Assigned to Ramesh Verma. Please inspect with plumbing team.",
        created_at=now - timedelta(hours=14)
    )
    db.session.add_all([t2_1, t2_2])

    # Complaint 3: Pending
    c3 = Complaint(
        complaint_id="CMP-202611-1003",
        title="Projector HDMI display flickering in Classroom LH-102",
        description="During lectures, the overhead projector screen continuously flickers to pink and turns black when connected to HDMI laptops. Cable or connector port seems loose.",
        category_id=cat_map["Academic & Classrooms"],
        priority="Medium",
        status="Pending",
        location="Academic Block, Lecture Hall LH-102",
        user_id=student3.id,
        assigned_staff_id=None,
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=5)
    )
    db.session.add(c3)
    db.session.flush()

    t3_1 = ComplaintTimeline(
        complaint_id=c3.id,
        updated_by_id=student3.id,
        action="Complaint Submitted",
        status="Pending",
        remarks="Ticket registered awaiting administrative review.",
        created_at=now - timedelta(hours=5)
    )
    db.session.add(t3_1)

    # Complaint 4: Resolved (with feedback)
    c4 = Complaint(
        complaint_id="CMP-202611-1004",
        title="Air conditioning unit stopped cooling in Central Library Digital Lab",
        description="AC Unit #2 in the digital section is making a loud buzzing sound and blowing ambient warm air. It gets very uncomfortable during afternoon study hours.",
        category_id=cat_map["Library & Study Facilities"],
        priority="Medium",
        status="Resolved",
        location="Central Library, 1st Floor Digital Reading Wing",
        user_id=student1.id,
        assigned_staff_id=staff_hostel.id,
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=2),
        resolved_at=now - timedelta(days=2),
        resolution_remarks="HVAC technician serviced the compressor, refilled refrigerant gas (R410A), and thoroughly cleaned air filters. Cooling verified at 21C.",
        user_rating=5,
        user_feedback="Quick turnaround and very efficient repair. AC is working great now!"
    )
    db.session.add(c4)
    db.session.flush()

    t4_1 = ComplaintTimeline(
        complaint_id=c4.id,
        updated_by_id=student1.id,
        action="Complaint Submitted",
        status="Pending",
        remarks="AC failure reported in library digital room.",
        created_at=now - timedelta(days=5)
    )
    t4_2 = ComplaintTimeline(
        complaint_id=c4.id,
        updated_by_id=admin.id,
        action="Staff Assigned",
        status="Assigned",
        remarks="Assigned to Ramesh Verma for HVAC inspection.",
        created_at=now - timedelta(days=4, hours=18)
    )
    t4_3 = ComplaintTimeline(
        complaint_id=c4.id,
        updated_by_id=staff_hostel.id,
        action="Progress Note",
        status="In Progress",
        remarks="Technician on-site. Identified compressor gas shortage.",
        created_at=now - timedelta(days=3, hours=10)
    )
    t4_4 = ComplaintTimeline(
        complaint_id=c4.id,
        updated_by_id=staff_hostel.id,
        action="Resolved",
        status="Resolved",
        remarks="HVAC technician serviced compressor and refilled refrigerant gas. Tested cooling.",
        created_at=now - timedelta(days=2)
    )
    db.session.add_all([t4_1, t4_2, t4_3, t4_4])

    # Complaint 5: In Progress
    c5 = Complaint(
        complaint_id="CMP-202611-1005",
        title="Water cooler filter replacement and hygiene audit in Student Canteen",
        description="The drinking water from the cooler near canteen counter tastes metallic. Kindly replace water filter cartridges and disinfect the storage tank.",
        category_id=cat_map["Mess & Canteen Food"],
        priority="High",
        status="In Progress",
        location="Student Activity Center, Ground Floor Canteen",
        user_id=student4.id,
        assigned_staff_id=staff_mess.id,
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(hours=10)
    )
    db.session.add(c5)
    db.session.flush()

    t5_1 = ComplaintTimeline(
        complaint_id=c5.id,
        updated_by_id=student4.id,
        action="Complaint Submitted",
        status="Pending",
        remarks="Water cooler filter replacement requested.",
        created_at=now - timedelta(days=3)
    )
    t5_2 = ComplaintTimeline(
        complaint_id=c5.id,
        updated_by_id=admin.id,
        action="Staff Assigned",
        status="Assigned",
        remarks="Assigned to Sunil Patel for vendor filter replacement.",
        created_at=now - timedelta(days=2, hours=12)
    )
    t5_3 = ComplaintTimeline(
        complaint_id=c5.id,
        updated_by_id=staff_mess.id,
        action="Progress Note",
        status="In Progress",
        remarks="Vendor contacted for Kent RO filter cartridge kit. Scheduled servicing today at 4 PM.",
        created_at=now - timedelta(hours=10)
    )
    db.session.add_all([t5_1, t5_2, t5_3])

    # Complaint 6: Pending
    c6 = Complaint(
        complaint_id="CMP-202611-1006",
        title="Damaged power sockets on Desk 14 in Seminar Hall 2",
        description="Three multi-plug sockets near Row 3 Desk 14 have burnt marks and spark when laptop chargers are plugged in. Need replacement before seminar on Friday.",
        category_id=cat_map["Hostel & Room Maintenance"],
        priority="Medium",
        status="Pending",
        location="Main Building, Seminar Hall 2, Row 3",
        user_id=student2.id,
        assigned_staff_id=None,
        created_at=now - timedelta(hours=8),
        updated_at=now - timedelta(hours=8)
    )
    db.session.add(c6)
    db.session.flush()

    t6_1 = ComplaintTimeline(
        complaint_id=c6.id,
        updated_by_id=student2.id,
        action="Complaint Submitted",
        status="Pending",
        remarks="Electrical socket fault reported.",
        created_at=now - timedelta(hours=8)
    )
    db.session.add(t6_1)

    # Complaint 7: Resolved
    c7 = Complaint(
        complaint_id="CMP-202611-1007",
        title="LAN port damaged and loose connection in Room 412 Hostel C",
        description="RJ45 wall socket plastic pin is broken off so the ethernet cable does not lock in place.",
        category_id=cat_map["IT & Wi-Fi Network"],
        priority="Low",
        status="Resolved",
        location="Hostel Block-C, Room 412",
        user_id=student1.id,
        assigned_staff_id=staff_it.id,
        created_at=now - timedelta(days=6),
        updated_at=now - timedelta(days=3),
        resolved_at=now - timedelta(days=3),
        resolution_remarks="Replaced RJ45 faceplate connector socket and tested connectivity with Fluke network tester. Speed is stable at 1 Gbps.",
        user_rating=4,
        user_feedback="Fixed nicely, thank you!"
    )
    db.session.add(c7)
    db.session.flush()

    t7_1 = ComplaintTimeline(
        complaint_id=c7.id,
        updated_by_id=student1.id,
        action="Complaint Submitted",
        status="Pending",
        remarks="Hostel LAN jack broken.",
        created_at=now - timedelta(days=6)
    )
    t7_2 = ComplaintTimeline(
        complaint_id=c7.id,
        updated_by_id=admin.id,
        action="Staff Assigned",
        status="Assigned",
        remarks="Assigned to Vikas Sharma.",
        created_at=now - timedelta(days=5)
    )
    t7_3 = ComplaintTimeline(
        complaint_id=c7.id,
        updated_by_id=staff_it.id,
        action="Progress Note",
        status="In Progress",
        remarks="Purchased new CAT6 keystone jack from store.",
        created_at=now - timedelta(days=4)
    )
    t7_4 = ComplaintTimeline(
        complaint_id=c7.id,
        updated_by_id=staff_it.id,
        action="Resolved",
        status="Resolved",
        remarks="Faceplate replaced and connection tested at 1 Gbps.",
        created_at=now - timedelta(days=3)
    )
    db.session.add_all([t7_1, t7_2, t7_3, t7_4])

    db.session.commit()
    print("Database seeding completed successfully!")
