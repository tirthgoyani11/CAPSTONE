import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from scoring_engine import ScoringEngine
from cv_parser import extract_text
import database

# Initialize App and DB
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
database.init_db()

# Initialize AI Engine
MODEL_PATH = "gcetv23"
engine = ScoringEngine(model_path=MODEL_PATH)

# Register Blueprints (Modular Routes)
from routes import talent_pool, analytics, settings
app.register_blueprint(talent_pool.bp)
app.register_blueprint(analytics.bp)
app.register_blueprint(settings.bp)

# --- Core Routes (Dashboard & Jobs) ---
# Kept here for simplicity, or could be moved to routes/jobs.py

@app.route('/')
def dashboard():
    conn = database.get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
    
    # Safely handle empty DB
    total_cand_row = conn.execute('SELECT COUNT(*) FROM candidates').fetchone()
    total_candidates = total_cand_row[0] if total_cand_row else 0
    
    avg_score_row = conn.execute('SELECT AVG(total_score) FROM candidates').fetchone()
    avg_score = round(avg_score_row[0], 1) if avg_score_row and avg_score_row[0] else 0
    
    conn.close()
    return render_template('dashboard.html', jobs=jobs, total_candidates=total_candidates, avg_score=avg_score)

@app.route('/jobs/create', methods=['POST'])
def create_job():
    title = request.form['title']
    desc_file = request.files['desc_file']
    
    if desc_file:
        filename = secure_filename(desc_file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        desc_file.save(path)
        description = extract_text(path)
    else:
        description = request.form.get('description', '')

    conn = database.get_db_connection()
    conn.execute('INSERT INTO jobs (title, description) VALUES (?, ?)', (title, description))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/jobs/<int:job_id>')
def job_detail(job_id):
    conn = database.get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    if not job:
        return "Job not found", 404
        
    candidates = conn.execute('SELECT * FROM candidates WHERE job_id = ? ORDER BY total_score DESC', (job_id,)).fetchall()
    conn.close()
    return render_template('job_detail.html', job=job, candidates=candidates)

@app.route('/jobs/<int:job_id>/upload', methods=['POST'])
def upload_cvs(job_id):
    conn = database.get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    cv_files = request.files.getlist('cvs')
    weights = {'overall_similarity': 0.5, 'skills': 0.3, 'experience': 0.2}

    for cv_file in cv_files:
        if cv_file.filename == '': continue
            
        filename = secure_filename(cv_file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        cv_file.save(path)
        
        try:
            cv_text = extract_text(path)
            score_data = engine.score_cv(cv_text, job['description'], weights)
            analysis = engine.analyze_candidate(cv_text, job['description'])
            
            conn.execute('''INSERT INTO candidates 
                            (job_id, filename, semantic_score, skills_score, experience_score, total_score, full_text, missing_skills, interview_questions)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                            (job_id, filename, 
                             score_data['breakdown']['semantic_match'],
                             score_data['breakdown']['skills_match'],
                             score_data['breakdown']['experience_match'],
                             score_data['total_score'],
                             cv_text,
                             json.dumps(analysis['missing']),
                             json.dumps(analysis['questions'])
                            ))
        except Exception as e:
            print(f"Error: {e}")
            
    conn.commit()
    conn.close()
    return redirect(url_for('job_detail', job_id=job_id))

@app.route('/jobs/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    conn = database.get_db_connection()
    conn.execute('DELETE FROM candidates WHERE job_id = ?', (job_id,))
    conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/candidate/<int:candidate_id>')
def candidate_modal(candidate_id):
    conn = database.get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    if not candidate: return jsonify({'error': 'Not found'}), 404
    
    # We need the JD to do fresh analysis for the chart if not stored properly,
    # but we stored 'missing' and 'questions'. We need 'matching' for the UI though.
    # The original implementation re-ran analyze_candidate.
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (candidate['job_id'],)).fetchone()
    conn.close()
    
    analysis = engine.analyze_candidate(candidate['full_text'], job['description'])
    
    return jsonify({
        'html': render_template('candidate_modal.html', candidate=candidate, analysis=analysis)
    })

@app.route('/candidate/<int:candidate_id>/delete', methods=['POST'])
def delete_candidate(candidate_id):
    conn = database.get_db_connection()
    cand = conn.execute('SELECT job_id FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    if cand:
        conn.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('job_detail', job_id=cand['job_id']))
    return redirect(url_for('dashboard'))

@app.route('/jobs/<int:job_id>/export')
def export_csv(job_id):
    import csv, io
    from flask import Response
    
    conn = database.get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    candidates = conn.execute('SELECT * FROM candidates WHERE job_id = ? ORDER BY total_score DESC', (job_id,)).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Rank', 'Candidate Filename', 'Total Score', 'Semantic Score', 'Skills Score', 'Experience Score', 'Missing Skills'])

    for idx, cand in enumerate(candidates, 1):
        writer.writerow([
            idx, cand['filename'], f"{cand['total_score']:.2f}",
            f"{cand['semantic_score']:.2f}", f"{cand['skills_score']:.2f}",
            f"{cand['experience_score']:.2f}", cand['missing_skills']
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={secure_filename(job['title'])}_candidates.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True)
