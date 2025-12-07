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
                        user_id INTEGER REFERENCES users(id),
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
                        user_id INTEGER, -- Link to User table
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(job_id) REFERENCES jobs(id),
                        FOREIGN KEY(user_id) REFERENCES users(id)
                    )''')
        # Users Table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT DEFAULT 'candidate', -- recruiter, candidate, admin
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        
        conn.commit()
        conn.close()
        print("Initialized SQLite Database.")


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

