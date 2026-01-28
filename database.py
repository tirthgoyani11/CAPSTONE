import sqlite3
import datetime

DB_NAME = "ats.db"


# Enhanced DB Connection (SQLite for Local, Postgres for Docker/Cloud)
import os

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Postgres Initialization
        import psycopg2
        conn = psycopg2.connect(db_url)
        c = conn.cursor()
        
        # Postgres Syntax
        c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'Open'
                    )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'candidate',
                        resume_path TEXT,
                        skills TEXT,
                        experience TEXT,
                        education TEXT,
                        profile_summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')

        c.execute('''CREATE TABLE IF NOT EXISTS candidates (
                        id SERIAL PRIMARY KEY,
                        job_id INTEGER REFERENCES jobs(id),
                        name TEXT,
                        filename TEXT,
                        semantic_score REAL,
                        skills_score REAL,
                        experience_score REAL,
                        total_score REAL,
                        email TEXT,
                        phone TEXT,
                        full_text TEXT,
                        missing_skills TEXT,
                        interview_questions TEXT,
                        notes TEXT,
                        status TEXT DEFAULT 'Applied',
                        user_id INTEGER REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')

        # Activity Logs Table (Postgres)
        c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
                        id SERIAL PRIMARY KEY,
                        candidate_id INTEGER REFERENCES candidates(id),
                        user_id INTEGER REFERENCES users(id),
                        action_type TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')

        # Interviews Table (Postgres)
        c.execute('''CREATE TABLE IF NOT EXISTS interviews (
                        id SERIAL PRIMARY KEY,
                        candidate_id INTEGER REFERENCES candidates(id),
                        interviewer_id INTEGER REFERENCES users(id),
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        location TEXT,
                        notes TEXT,
                        status TEXT DEFAULT 'Scheduled',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        
        conn.commit()
        conn.close()
        print("Initialized PostgreSQL Database.")
    else:
        # SQLite Initialization (Existing Logic)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Jobs Table
        c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'Open'
                    )''')
        
        # Candidates Table
        c.execute('''CREATE TABLE IF NOT EXISTS candidates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id INTEGER,
                        name TEXT,
                        filename TEXT,
                        semantic_score REAL,
                        skills_score REAL,
                        experience_score REAL,
                        total_score REAL,
                        email TEXT,
                        phone TEXT,
                        full_text TEXT,
                        missing_skills TEXT,
                        interview_questions TEXT,
                        notes TEXT, -- New Column
                        user_id INTEGER, -- Link to User table
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(job_id) REFERENCES jobs(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
        
        # Activity Logs Table
        c.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        candidate_id INTEGER,
                        user_id INTEGER,
                        action_type TEXT, -- 'status_change', 'note', 'email', 'interview'
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(candidate_id) REFERENCES candidates(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')

        # Interviews Table
        c.execute('''CREATE TABLE IF NOT EXISTS interviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        candidate_id INTEGER,
                        interviewer_id INTEGER,
                        start_time TIMESTAMP,
                        end_time TIMESTAMP,
                        location TEXT, -- 'Google Meet', 'Office', etc.
                        notes TEXT,
                        status TEXT DEFAULT 'Scheduled', -- 'Scheduled', 'Completed', 'Cancelled'
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(candidate_id) REFERENCES candidates(id),
                        FOREIGN KEY(interviewer_id) REFERENCES users(id)
                    )''')

        # Users Table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'candidate', -- recruiter, candidate, admin
                        resume_path TEXT,
                        skills TEXT,
                        experience TEXT,
                        education TEXT,
                        profile_summary TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        
        # Simple Migration for missing columns (Quick Fix for dev)
        # Candidates table migrations
        try:
            c.execute("ALTER TABLE candidates ADD COLUMN notes TEXT")
        except sqlite3.OperationalError:
            pass # Already exists
            
        try:
            c.execute("ALTER TABLE candidates ADD COLUMN status TEXT DEFAULT 'Applied'")
        except sqlite3.OperationalError:
            pass # Already exists
            
        # Users table migrations
        try:
            c.execute("ALTER TABLE users ADD COLUMN resume_path TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            c.execute("ALTER TABLE users ADD COLUMN skills TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            c.execute("ALTER TABLE users ADD COLUMN experience TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            c.execute("ALTER TABLE users ADD COLUMN education TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            c.execute("ALTER TABLE users ADD COLUMN profile_summary TEXT")
        except sqlite3.OperationalError:
            pass
            
        conn.commit()
        conn.close()
        print("Initialized SQLite Database.")

def get_all_candidates(user_id=None):
    conn = get_db_connection()
    # Join with jobs to get job title
    query = '''
        SELECT c.*, j.title as job_role
        FROM candidates c
        LEFT JOIN jobs j ON c.job_id = j.id
    '''
    params = []
    # If user_id is provided, filtering logic could go here depending on requirements
    # For now returning all for recruiter visibility
    
    candidates = conn.execute(query, params).fetchall()
    conn.close()
    return candidates

def get_candidate(candidate_id):
    conn = get_db_connection()
    cand = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    conn.close()
    return cand

def add_candidate_note(candidate_id, note):
    conn = get_db_connection()
    conn.execute('UPDATE candidates SET notes = ? WHERE id = ?', (note, candidate_id))
    conn.commit()
    conn.close()


# User Class for Flask-Login
from flask_login import UserMixin
import werkzeug.security

class User(UserMixin):
    def __init__(self, id, name, email, role, password_hash, resume_path=None, skills=None, experience=None, education=None, profile_summary=None):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.password_hash = password_hash
        self.resume_path = resume_path
        self.skills = skills
        self.experience = experience
        self.education = education
        self.profile_summary = profile_summary

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if not user: return None
        return User(user['id'], user['name'], user['email'], user['role'], user['password_hash'], 
                   user['resume_path'], user['skills'], user['experience'], user['education'], user['profile_summary'])

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        if not user: return None
        return User(user['id'], user['name'], user['email'], user['role'], user['password_hash'],
                   user['resume_path'], user['skills'], user['experience'], user['education'], user['profile_summary'])
        
    @staticmethod
    def create(name, email, password, role='candidate'):
        hashed = werkzeug.security.generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)', 
                         (name, email, hashed, role))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def check_password(self, password):
        return werkzeug.security.check_password_hash(self.password_hash, password)

