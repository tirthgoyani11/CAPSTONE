from flask import Blueprint, render_template
import database

bp = Blueprint('analytics', __name__)

from flask_login import login_required
from decorators import role_required

@bp.route('/analytics')
@login_required
@role_required('recruiter')
def index():
    conn = database.get_db_connection()
    
    # 1. Candidates per Job
    jobs = conn.execute("SELECT id, title FROM jobs").fetchall()
    job_labels = []
    job_counts = []
    
    for job in jobs:
        count = conn.execute("SELECT COUNT(*) FROM candidates WHERE job_id = ?", (job['id'],)).fetchone()[0]
        job_labels.append(job['title'])
        job_counts.append(count)
        
    # 2. Score Distribution (e.g. 0-50, 51-75, 76-100)
    scores = conn.execute("SELECT total_score FROM candidates").fetchall()
    score_buckets = [0, 0, 0] # Low, Medium, High
    
    for s in scores:
        val = s['total_score']
        if val < 50: score_buckets[0] += 1
        elif val < 80: score_buckets[1] += 1
        else: score_buckets[2] += 1
        
    # 3. Pipeline Funnel (Status Counts)
    statuses = ['Applied', 'Screening', 'Interview', 'Offer', 'Rejected']
    status_counts = []
    for st in statuses:
        # Check for NULL status and treat as 'Applied' if st=='Applied'
        if st == 'Applied':
            c = conn.execute("SELECT COUNT(*) FROM candidates WHERE status = ? OR status IS NULL", (st,)).fetchone()[0]
        else:
            c = conn.execute("SELECT COUNT(*) FROM candidates WHERE status = ?", (st,)).fetchone()[0]
        status_counts.append(c)

    # 4. Market Insights: Top Skills (Skills Gap)
    import json
    skill_gap_counts = {}
    candidates_data = conn.execute("SELECT missing_skills FROM candidates").fetchall()
    
    for row in candidates_data:
        if row['missing_skills']:
            try:
                missing = json.loads(row['missing_skills'])
                for m in missing:
                    skill_gap_counts[m] = skill_gap_counts.get(m, 0) + 1
            except:
                pass
                
    # Sort and get top 10
    sorted_gaps = sorted(skill_gap_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    gap_labels = [x[0] for x in sorted_gaps]
    gap_counts = [x[1] for x in sorted_gaps]

    # 5. Additional Metrics
    total_candidates = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Open'").fetchone()[0]
    avg_score_row = conn.execute("SELECT AVG(total_score) FROM candidates").fetchone()
    avg_score = round(avg_score_row[0], 1) if avg_score_row and avg_score_row[0] else 0
    hired_count = conn.execute("SELECT COUNT(*) FROM candidates WHERE status = 'Hired'").fetchone()[0]

    conn.close()
    
    return render_template('analytics.html', 
                           job_labels=job_labels, 
                           job_counts=job_counts,
                           score_buckets=score_buckets,
                           pipeline_labels=statuses,
                           pipeline_counts=status_counts,
                           gap_labels=gap_labels,
                           gap_counts=gap_counts,
                           total_candidates=total_candidates,
                           total_jobs=total_jobs,
                           avg_score=avg_score,
                           hired_count=hired_count)
