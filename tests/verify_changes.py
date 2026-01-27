
import os
import sys
import json
import sqlite3

# Add root to path
sys.path.append(os.getcwd())

from scoring_engine import ScoringEngine
from database import init_db, get_db_connection

def test_scoring_engine():
    print("Testing Scoring Engine...")
    engine = ScoringEngine()
    
    cv_text = """
    EXPERIENCE
    Software Engineer at Tech Corp
    5 years of experience in Python, Flask, and AWS.
    Built scalable APIs and managed PostgreSQL databases.
    
    SKILLS
    Python, Java, AWS, Docker, Git.
    """
    
    jd_text = """
    We are looking for a Software Engineer with 5+ years of experience.
    Must know Python, Flask, and AWS.
    Experience with Docker and PostgreSQL is a plus.
    """
    
    # Test Hybrid Score
    result = engine.score_cv(cv_text, jd_text)
    print("Scoring Result Keys:", result.keys())
    print("Total Score:", result['total_score'])
    print("Breakdown:", result['breakdown'])
    
    assert 'semantic_match' in result['breakdown']
    assert 'skills_match' in result['breakdown']
    assert 'experience_match' in result['breakdown']
    assert result['breakdown']['years_experience'] >= 5
    
    print("✅ Scoring Engine Test Passed")

def test_database_schema():
    print("\nTesting Database Schema...")
    # Ensure DB exists
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check candidates table for 'notes' column
    cursor.execute("PRAGMA table_info(candidates)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'notes' in columns:
        print("✅ 'notes' column exists in candidates table.")
    else:
        print("❌ 'notes' column MISSING in candidates table.")
        
    conn.close()

if __name__ == "__main__":
    try:
        test_scoring_engine()
        test_database_schema()
        print("\nAll Verification Tests Passed!")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
