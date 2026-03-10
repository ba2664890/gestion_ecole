"""
Seeding utility for generating randomized academic data.
Used for testing and "Random Generate" features.
"""

import random
from datetime import date, timedelta
from models import SessionLocal, Project, Session, Course, Student, Grade, Attendance, User
import hashlib

def generate_random_students(n=30):
    db = SessionLocal()
    try:
        noms = ["Diallo", "Ndiaye", "Mbaye", "Sow", "Fall", "Thiam", "Ba", "Sarr", "Diop", "Cisse", "Gueye", "Traore", "Sy", "Faye"]
        prenoms = ["Fatou", "Moussa", "Aminata", "Ibrahim", "Marième", "Cheikh", "Rokhaya", "Oumar", "Awa", "Alioune", "Ndèye", "Modou", "Khady", "Mamadou"]
        
        for _ in range(n):
            nom = random.choice(noms)
            prenom = random.choice(prenoms)
            email = f"{prenom.lower()}.{nom.lower()}{random.randint(1, 999)}@sga.edu"
            
            # Check unique
            if not db.query(Student).filter_by(email=email).first():
                s = Student(
                    nom=nom,
                    prenom=prenom,
                    email=email,
                    date_naissance=date.today() - timedelta(days=random.randint(6000, 9000))
                )
                db.add(s)
        db.commit()
    finally:
        db.close()

def generate_random_users(n=5):
    db = SessionLocal()
    try:
        noms = ["Kane", "Senghor", "Diouf", "Wade", "Gassama"]
        prenoms = ["Prof.", "Dr.", "M.", "Mme."]
        
        for i in range(n):
            nom = random.choice(noms)
            prenom = random.choice(prenoms)
            username = f"{prenom.replace('.', '').lower()}{nom.lower()}{random.randint(1,99)}"
            email = f"{username}@sga.edu"
            
            if not db.query(User).filter_by(username=username).first():
                u = User(
                    username=username,
                    password_hash=hashlib.sha256("password123".encode()).hexdigest(),
                    role="teacher",
                    nom_complet=f"{prenom} {nom}",
                    email=email
                )
                db.add(u)
        db.commit()
    finally:
        db.close()

def generate_random_grades(n_per_student=3):
    db = SessionLocal()
    try:
        students = db.query(Student).all()
        courses = db.query(Course).all()
        if not students or not courses: return
        
        types_eval = ["Examen", "Contrôle Continu", "Projet", "TP"]
        
        for student in students:
            for _ in range(n_per_student):
                course = random.choice(courses)
                g = Grade(
                    student_id=student.id,
                    course_id=course.id,
                    note=round(random.uniform(5.0, 20.0), 2),
                    coefficient=random.choice([1.0, 2.0, 3.0]),
                    type_evaluation=random.choice(types_eval)
                )
                db.add(g)
        db.commit()
    finally:
        db.close()

def generate_random_attendances():
    db = SessionLocal()
    try:
        sessions = db.query(Session).all()
        students = db.query(Student).all()
        if not sessions or not students: return
        
        for session in sessions:
            for student in students:
                # 15% chance to be absent
                is_absent = random.random() < 0.15
                is_justifie = is_absent and random.random() < 0.3 # If absent, 30% chance justified
                
                # Check if already exists
                if not db.query(Attendance).filter_by(session_id=session.id, student_id=student.id).first():
                    a = Attendance(
                        session_id=session.id,
                        student_id=student.id,
                        absent=is_absent,
                        justifie=is_justifie
                    )
                    db.add(a)
        db.commit()
    finally:
        db.close()

def generate_random_projects(n=5):
    db = SessionLocal()
    try:
        courses = db.query(Course).all()
        if not courses: return
        
        statuses = ["To Do", "In Progress", "Done"]
        priorities = ["badge-red", "badge-orange", "badge-blue", "badge-purple", "badge-green"]
        
        for _ in range(n):
            course = random.choice(courses)
            status = random.choice(statuses)
            progress = 100 if status == "Done" else random.randint(0, 90)
            
            p = Project(
                title=f"Projet {random.choice(['Data', 'IA', 'Stats', 'Rapport', 'Analyse'])} {random.randint(1, 99)}",
                course_id=course.id,
                status=status,
                priority=random.choice(priorities),
                deadline=f"{(date.today() + timedelta(days=random.randint(5, 30))).strftime('%d %b')}",
                progress=progress,
                members=random.randint(2, 6)
            )
            db.add(p)
        db.commit()
    finally:
        db.close()

def generate_random_schedule():
    db = SessionLocal()
    try:
        courses = db.query(Course).all()
        if not courses: return
        
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        
        times = ["08:00", "10:00", "14:00", "16:00"]
        themes = ["Introduction", "Travaux Pratiques", "Révisions", "Exercices", "Étude de Cas"]
        
        for day_offset in range(5):
            num_sessions = random.randint(1, 3)
            used_times = []
            for _ in range(num_sessions):
                st = random.choice([t for t in times if t not in used_times])
                used_times.append(st)
                
                course = random.choice(courses)
                s = Session(
                    course_id=course.id,
                    date=monday + timedelta(days=day_offset),
                    start_time=st,
                    duree=2.0,
                    theme=f"{random.choice(themes)}: {course.libelle}"
                )
                db.add(s)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding random data...")
    generate_random_students(30)
    generate_random_users(5)
    generate_random_projects(10)
    generate_random_schedule()
    generate_random_grades(5) # 5 per student
    generate_random_attendances()
    print("Done. Database successfully populated with realistic fake data.")
