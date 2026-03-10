import random
from datetime import date, timedelta
from sqlalchemy.orm import Session
from models import SessionLocal, Student, Course, Session as SessionModel, Attendance, Grade

def generate_mock_data():
    db = SessionLocal()
    try:
        # Check if we already have enough students/courses
        students = db.query(Student).all()
        courses = db.query(Course).all()
        
        if not students or not courses:
            print("Please ensure students and courses are seeded first (run init_db if needed).")
            return
            
        print(f"Found {len(students)} students and {len(courses)} courses.")
        
        # 1. Create Sessions for each course
        print("Generating sessions...")
        sessions_created = 0
        themes = ["Introduction", "Chapitre 1", "Chapitre 2", "Travaux Pratiques", "Révisions", "Évaluation"]
        base_date = date.today() - timedelta(days=60) # Start 2 months ago
        
        for course in courses:
            # Create 5-10 sessions per course
            num_sessions = random.randint(5, 10)
            for i in range(num_sessions):
                session_date = base_date + timedelta(days=random.randint(1, 60))
                theme = random.choice(themes)
                duree = random.choice([1.0, 1.5, 2.0, 3.0])
                
                # Check if session exists to avoid duplicates
                existing = db.query(SessionModel).filter_by(
                    course_id=course.id, 
                    date=session_date, 
                    theme=theme
                ).first()
                
                if not existing:
                    new_session = SessionModel(
                        course_id=course.id,
                        date=session_date,
                        duree=duree,
                        theme=f"{theme} - Session {i+1}",
                        notes="Généré automatiquement"
                    )
                    db.add(new_session)
                    sessions_created += 1
        
        db.commit()
        print(f"Created {sessions_created} sessions.")
        
        # Reload sessions
        all_sessions = db.query(SessionModel).all()
        
        # 2. Create Attendances
        print("Generating attendances...")
        attendances_created = 0
        
        for session in all_sessions:
            for student in students:
                # 15% chance of being absent
                is_absent = random.random() < 0.15
                is_justifie = is_absent and random.random() < 0.3 # 30% of absences are justified
                
                existing = db.query(Attendance).filter_by(
                    session_id=session.id,
                    student_id=student.id
                ).first()
                
                if not existing:
                    att = Attendance(
                        session_id=session.id,
                        student_id=student.id,
                        absent=is_absent,
                        justifie=is_justifie
                    )
                    db.add(att)
                    attendances_created += 1
                    
        db.commit()
        print(f"Created {attendances_created} attendance records.")
        
        # 3. Create Grades
        print("Generating grades...")
        grades_created = 0
        eval_types = ["Contrôle Continu", "Devoir Maison", "Examen Partiel", "Projet"]
        
        for course in courses:
            # 2 to 4 grades per course
            num_grades = random.randint(2, 4)
            for _ in range(num_grades):
                eval_type = random.choice(eval_types)
                coefficient = random.choice([1.0, 1.5, 2.0])
                
                for student in students:
                    # Generate a random grade following a rough normal distribution around 12
                    base_grade = random.gauss(12, 3)
                    final_grade = max(0.0, min(20.0, round(base_grade * 2) / 2)) # Round to nearest 0.5, bound 0-20
                    
                    # Avoid exact duplicates for the same student/course/type
                    existing = db.query(Grade).filter_by(
                        student_id=student.id,
                        course_id=course.id,
                        type_evaluation=eval_type
                    ).first()
                    
                    if not existing:
                        grade = Grade(
                            student_id=student.id,
                            course_id=course.id,
                            note=final_grade,
                            coefficient=coefficient,
                            type_evaluation=eval_type
                        )
                        db.add(grade)
                        grades_created += 1
                        
        db.commit()
        print(f"Created {grades_created} grades.")
        
        print("Mock data generation complete!")
        
    except Exception as e:
        db.rollback()
        print(f"Error generating data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    from models import init_db
    print("Initializing DB to ensure base data exists...")
    init_db()
    generate_mock_data()
