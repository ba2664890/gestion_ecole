"""
SGA - Système de Gestion Académique
Database Models - SQLAlchemy ORM
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import os

Base = declarative_base()

DB_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///sga.db"
)

engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(bind=engine)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    date_naissance = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now())

    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.prenom} {self.nom}"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    libelle = Column(String(200), nullable=False)
    volume_horaire = Column(Float, nullable=False, default=0)
    enseignant = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    sessions = relationship("Session", back_populates="course", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="course", cascade="all, delete-orphan")

    @property
    def heures_effectuees(self):
        return sum(s.duree for s in self.sessions)

    @property
    def progression(self):
        if self.volume_horaire == 0:
            return 0
        return min(100, (self.heures_effectuees / self.volume_horaire) * 100)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(String(50), default="To Do")  # To Do, In Progress, Done
    priority = Column(String(50), default="badge-blue")
    deadline = Column(String(100))
    progress = Column(Integer, default=0)
    members = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(String(5), nullable=False, default="08:00") # Format "HH:MM"
    duree = Column(Float, nullable=False, default=1.5)
    theme = Column(String(500), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    absent = Column(Boolean, default=False)
    justifie = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    session = relationship("Session", back_populates="attendances")
    student = relationship("Student", back_populates="attendances")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    note = Column(Float, nullable=False)
    coefficient = Column(Float, default=1.0)
    type_evaluation = Column(String(100), default="Examen")
    created_at = Column(DateTime, default=func.now())

    student = relationship("Student", back_populates="grades")
    course = relationship("Course", back_populates="grades")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(50), default="teacher")
    nom_complet = Column(String(200), nullable=False)
    email = Column(String(200), unique=True)
    created_at = Column(DateTime, default=func.now())


def init_db():
    """Initialize database tables and seed default data."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning during create_all: {e}")
        # Sometimes sequences already exist even if tables don't, 
        # but create_all might still have created the tables.

    db = SessionLocal()
    try:
        # Check if admin user exists
        if not db.query(User).filter_by(username="admin").first():
            import hashlib
            admin = User(
                username="admin",
                password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
                role="admin",
                nom_complet="Administrateur SGA",
                email="admin@sga.edu"
            )
            db.add(admin)
            db.commit() # Commit admin early

        # Seed some demo data if empty
        if db.query(Student).count() == 0:
            students_data = [
                ("Diallo", "Fatou", "fatou.diallo@sga.edu", "2000-03-15"),
                ("Ndiaye", "Moussa", "moussa.ndiaye@sga.edu", "1999-07-22"),
                ("Mbaye", "Aminata", "aminata.mbaye@sga.edu", "2001-01-10"),
                ("Sow", "Ibrahim", "ibrahim.sow@sga.edu", "2000-11-05"),
                ("Fall", "Marième", "marieme.fall@sga.edu", "1999-09-18"),
                ("Thiam", "Cheikh", "cheikh.thiam@sga.edu", "2001-04-27"),
                ("Ba", "Rokhaya", "rokhaya.ba@sga.edu", "2000-08-03"),
                ("Sarr", "Oumar", "oumar.sarr@sga.edu", "1999-12-14"),
            ]
            from datetime import date
            for nom, prenom, email, dob in students_data:
                # Double check uniqueness before adding
                if not db.query(Student).filter_by(email=email).first():
                    s = Student(nom=nom, prenom=prenom, email=email,
                               date_naissance=date.fromisoformat(dob))
                    db.add(s)
            db.commit()

        if db.query(Course).count() == 0:
            courses_data = [
                ("MATH101", "Mathématiques Avancées", 60, "Dr. Kane"),
                ("INFO201", "Algorithmique & Structures de données", 45, "Prof. Diop"),
                ("PHYS101", "Physique Quantique", 40, "Dr. Gueye"),
                ("ECON301", "Économétrie", 35, "Prof. Sy"),
                ("FRAN101", "Littérature Française", 30, "Mme. Touré"),
            ]
            for code, libelle, vh, ens in courses_data:
                if not db.query(Course).filter_by(code=code).first():
                    c = Course(code=code, libelle=libelle, volume_horaire=vh, enseignant=ens)
                    db.add(c)
            db.commit()

        # Seed Projects if empty
        if db.query(Project).count() == 0:
            math_id = db.query(Course).filter_by(code="MATH101").first().id
            info_id = db.query(Course).filter_by(code="INFO201").first().id
            econ_id = db.query(Course).filter_by(code="ECON301").first().id
            
            projects_data = [
                ("Modélisation Risque", math_id, "To Do", "badge-red", "24 Mars", 0, 4),
                ("Dashboard ENSAE", info_id, "To Do", "badge-orange", "02 Avril", 15, 2),
                ("Sondage Électoral", econ_id, "In Progress", "badge-blue", "15 Mars", 65, 5),
                ("Analyse de Séries", math_id, "In Progress", "badge-purple", "28 Mars", 40, 3),
                ("Base de Données", info_id, "Done", "badge-green", "Terminé", 100, 3),
            ]
            for title, cid, status, prio, dl, prog, mb in projects_data:
                p = Project(title=title, course_id=cid, status=status, 
                           priority=prio, deadline=dl, progress=prog, members=mb)
                db.add(p)
            db.commit()

        # Seed Scheduled Sessions if empty (for the schedule page)
        if db.query(Session).count() == 0:
            from datetime import date as dt_date, timedelta
            today = dt_date.today()
            # Find last Monday
            monday = today - timedelta(days=today.weekday())
            
            math_id = db.query(Course).filter_by(code="MATH101").first().id
            info_id = db.query(Course).filter_by(code="INFO201").first().id
            econ_id = db.query(Course).filter_by(code="ECON301").first().id
            
            schedules = [
                (monday, "08:00", 2.0, "Probabilités & Stats", math_id),
                (monday, "10:00", 2.0, "Econométrie I", econ_id),
                (monday + timedelta(days=1), "08:00", 4.0, "Algorithmique Avancée", info_id),
                (monday + timedelta(days=2), "08:00", 2.0, "Microéconomie", econ_id),
                (monday + timedelta(days=3), "11:00", 2.0, "Algèbre Linéaire", math_id),
            ]
            for d, t, dur, theme, cid in schedules:
                s = Session(course_id=cid, date=d, start_time=t, duree=dur, theme=theme)
                db.add(s)
            db.commit()

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
