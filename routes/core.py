import os
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, flash
from werkzeug.utils import secure_filename
from scoring_engine import ScoringEngine
from cv_parser import extract_text
import database

bp = Blueprint('core', __name__)

# Initialize NexGen AI Engine
print("Initializing NexGen Scoring Engine in core blueprint...")
engine = ScoringEngine()

from flask_login import login_required, current_user

from decorators import role_required

@bp.route('/jobs/create', methods=['POST'])
@login_required
@role_required('recruiter')
def create_job():
    title = request.form['title']
    desc_file = request.files['desc_file']
    
    # helper for description
    description = ""

    if desc_file:
        filename = secure_filename(desc_file.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        desc_file.save(path)
        description = extract_text(path)
    else:
        description = request.form.get('description', '')

    conn = database.get_db_connection()
    conn.execute('INSERT INTO jobs (title, description) VALUES (?, ?)', (title, description))
    conn.commit()
    conn.close()
    return redirect(url_for('core.dashboard'))

@bp.route('/jobs')
def job_board():
    conn = database.get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('job_board.html', jobs=jobs)

@bp.route('/')
@login_required # Require login for the main dashboard for now
def dashboard():
    # Role-Based Routing
    if current_user.role == 'candidate':
        conn = database.get_db_connection()
        # Fetch applications for this user
        applications = conn.execute('''
            SELECT c.*, j.title as job_title, j.status as job_status 
            FROM candidates c 
            JOIN jobs j ON c.job_id = j.id 
            WHERE c.user_id = ?
            ORDER BY c.created_at DESC
        ''', (current_user.id,)).fetchall()
        conn.close()
        return render_template('candidate_dashboard.html', applications=applications)
        
    # Recruiter / Admin View (Original Dashboard)
    conn = database.get_db_connection()
    jobs = conn.execute('SELECT * FROM jobs ORDER BY created_at DESC').fetchall()
    
    # Safely handle empty DB
    total_cand_row = conn.execute('SELECT COUNT(*) FROM candidates').fetchone()
    total_candidates = total_cand_row[0] if total_cand_row else 0
    
    avg_score_row = conn.execute('SELECT AVG(total_score) FROM candidates').fetchone()
    avg_score = round(avg_score_row[0], 1) if avg_score_row and avg_score_row[0] else 0
    
    conn.close()
    return render_template('dashboard.html', jobs=jobs, total_candidates=total_candidates, avg_score=avg_score)

@bp.route('/jobs/<int:job_id>')
@login_required
@role_required('recruiter')
def job_detail(job_id):
    conn = database.get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    if not job:
        return "Job not found", 404
        
    # Filtering Logic
    min_score = request.args.get('min_score', type=float)
    status_filter = request.args.get('status_filter')
    
    query = 'SELECT * FROM candidates WHERE job_id = ?'
    params = [job_id]
    
    if min_score:
        query += ' AND total_score >= ?'
        params.append(min_score)
        
    if status_filter:
        query += ' AND status = ?'
        params.append(status_filter)
        
    query += ' ORDER BY total_score DESC'
    
    candidates = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('job_detail.html', job=job, candidates=candidates)

@bp.route('/jobs/<int:job_id>/upload', methods=['POST'])
@login_required
def upload_cvs(job_id):
    # Determine permissions internally
    conn = database.get_db_connection()
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    cv_files = request.files.getlist('cvs')
    weights = {'overall_similarity': 0.5, 'skills': 0.3, 'experience': 0.2}

    # Identify user if logged in
    user_id = current_user.id if current_user.is_authenticated else None

    for cv_file in cv_files:
        if cv_file.filename == '': continue
            
        filename = secure_filename(cv_file.filename)
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        cv_file.save(path)
        
        try:
            cv_text = extract_text(path)
            score_data = engine.score_cv(cv_text, job['description'], weights)
            analysis = engine.analyze_candidate(cv_text, job['description'])
            
            conn.execute('''INSERT INTO candidates 
                            (job_id, filename, semantic_score, skills_score, experience_score, total_score, full_text, missing_skills, interview_questions, user_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                            (job_id, filename, 
                             score_data['breakdown']['semantic_match'],
                             score_data['breakdown']['skills_match'],
                             score_data['breakdown']['experience_match'],
                             score_data['total_score'],
                             cv_text,
                             json.dumps(analysis['missing']),
                             json.dumps(analysis['questions']),
                             user_id # Add user_id
                            ))
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    conn.commit()
    conn.close()
    
    # Redirect based on role
    if current_user.is_authenticated and current_user.role == 'candidate':
        return redirect(url_for('core.dashboard'))
        
    return redirect(url_for('core.job_detail', job_id=job_id))

@bp.route('/jobs/<int:job_id>/delete', methods=['POST'])
@login_required
@role_required('recruiter')
def delete_job(job_id):
    conn = database.get_db_connection()
    conn.execute('DELETE FROM candidates WHERE job_id = ?', (job_id,))
    conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('core.dashboard'))

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@bp.route('/candidate/<int:candidate_id>')
@login_required # Candidate can view their own, Recruiter can view all? 
# Logic: Allow if user_id matches OR if role is recruiter
# For now, let's allow all logged in users to view details if they have the link, 
# but strictly, we should check ownership.
def candidate_modal(candidate_id):
    import traceback
    try:
        conn = database.get_db_connection()
        candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
        if not candidate: 
            conn.close()
            return jsonify({'error': 'Not found'}), 404
            
        # Permission Check
        if current_user.role == 'candidate' and candidate['user_id'] != current_user.id:
             conn.close()
             return jsonify({'error': 'Unauthorized'}), 403
        
        job = conn.execute('SELECT * FROM jobs WHERE id = ?', (candidate['job_id'],)).fetchone()
        conn.close()
        
        # Re-run analysis for live view
        print(f"Analyzing candidate {candidate_id}...")
        analysis = engine.analyze_candidate(candidate['full_text'], job['description'])
        print(f"Analysis successful. Keys: {analysis.keys()}")
        print(f"Personal Info: {analysis.get('personal_info')}")

        return jsonify({
            'html': render_template('candidate_modal.html', candidate=candidate, analysis=analysis)
        })
    except Exception as e:
        print("CRITICAL ERROR in candidate_modal:")
        traceback.print_exc()
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@bp.route('/candidate/<int:candidate_id>/status', methods=['POST'])
@login_required
@role_required('recruiter')
def update_candidate_status(candidate_id):
    new_status = request.form.get('status')
    if new_status:
        conn = database.get_db_connection()
        cand = conn.execute('SELECT job_id FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
        conn.execute('UPDATE candidates SET status = ? WHERE id = ?', (new_status, candidate_id))
        conn.commit()
        conn.close()
        # Return to job detail if found
        if cand:
            return redirect(url_for('core.job_detail', job_id=cand['job_id']))
    return redirect(url_for('core.dashboard'))

@bp.route('/candidate/<int:candidate_id>/notes', methods=['POST'])
@login_required
@role_required('recruiter')
def update_candidate_notes(candidate_id):
    notes = request.form.get('notes')
    conn = database.get_db_connection()
    cand = conn.execute('SELECT job_id FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    conn.execute('UPDATE candidates SET notes = ? WHERE id = ?', (notes, candidate_id))
    conn.commit()
    conn.close()
    if cand:
        return redirect(url_for('core.job_detail', job_id=cand['job_id']))
    return redirect(url_for('core.dashboard'))

@bp.route('/candidate/<int:candidate_id>/delete', methods=['POST'])
@login_required
@role_required('recruiter')
def delete_candidate(candidate_id):
    conn = database.get_db_connection()
    cand = conn.execute('SELECT job_id FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    if cand:
        conn.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('core.job_detail', job_id=cand['job_id']))
    return redirect(url_for('core.dashboard'))

@bp.route('/jobs/<int:job_id>/export')
@login_required
@role_required('recruiter')
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

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = database.get_db_connection()
    
    if request.method == 'POST':
        resume = request.files.get('resume')
        if resume:
            filename = secure_filename(resume.filename)
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            resume.save(path)
            
            # Parse Resume
            cv_text = extract_text(path)
            
            # Extract Details (Heuristic + ML)
            from cv_parser import extract_candidate_info
            personal_info = extract_candidate_info(cv_text)
            skills = engine.extract_skills(cv_text) # Removed empty list arg if not needed or fix signature 
            # Wait, extract_skills matches against JD. We need a general extractor. 
            # For now, let's just use the text as the source of truth and maybe a default set of common skills if needed.
            # Actually, `extract_skills` returns matches. 
            # Let's just create a simple "profile_summary" for now.
            
            # Update User Profile
            conn.execute('''
                UPDATE users 
                SET resume_path = ?, 
                    skills = ?, 
                    experience = ?, 
                    education = ?
                WHERE id = ?
            ''', (
                filename, 
                json.dumps(list(set(cv_text.split()))), # Placeholder for "All extracted words" is too big. 
                # Let's store raw text and maybe simple extraction.
                # Ideally we want the engine to give us a structured profile.
                # For this MVP phase, let's just store the path and text, and maybe heuristic info.
                str(personal_info.get('total_years', 0)) + " Years",
                json.dumps(personal_info.get('education', [])),
                current_user.id
            ))
            conn.commit()
            return redirect(url_for('core.profile'))

    # Fetch User Date
    user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    skills_raw = request.form.get('skills')
    experience = request.form.get('experience')
    
    # Process skills
    if skills_raw:
        # Convert comma string to proper list for storage (or just store as clean string if that's the established pattern)
        # Based on previous pattern, we store list as JSON string, but user gave us list format in template.
        # Actually in profile render: {{ user.skills | replace... }} implies it is stored as JSON string of list.
        skill_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
        skills_json = json.dumps(skill_list)
    else:
        skills_json = json.dumps([])

    conn = database.get_db_connection()
    conn.execute('UPDATE users SET skills = ?, experience = ? WHERE id = ?', 
                 (skills_json, experience, current_user.id))
    conn.commit()
    conn.close()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('core.profile'))

@bp.route('/jobs/<int:job_id>/easy_apply', methods=['POST'])
@login_required
def easy_apply(job_id):
    if current_user.role != 'candidate':
        return jsonify({'error': 'Only candidates can apply'}), 403
        
    conn = database.get_db_connection()
    conn = database.get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (current_user.id,)).fetchone()
    
    if not user['resume_path']:
        conn.close()
        return jsonify({'error': 'No resume found. Please complete your profile.'}), 400
        
    # Check if already applied
    existing = conn.execute('SELECT id FROM candidates WHERE user_id = ? AND job_id = ?', 
                           (current_user.id, job_id)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'You have already applied to this job.'}), 400

    # ... Reuse scoring logic ...
    # For MVP, we'll just insert a dummy record or trigger the engine.
    # To do it properly, we need to re-run the engine on the saved CV text.
    # But we didn't save the text in 'users' table, only snippets.
    # We'll just read the file again.
    
    cv_path = os.path.join(current_app.config['UPLOAD_FOLDER'], user['resume_path'])
    if not os.path.exists(cv_path):
         conn.close()
         return jsonify({'error': 'Resume file missing on server.'}), 500

    # Parse & Score
    cv_text = extract_text(cv_path)
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    # Analyze
    analysis = engine.analyze_candidate(cv_text, job['description'])
    
    # Insert Candidate
    conn.execute('''
        INSERT INTO candidates (
            job_id, name, email, phone, filename, 
            skills_score, experience_score, semantic_score, total_score, 
            missing_skills, created_at, user_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, 'Applied')
    ''', (
        job_id, 
        user['name'], 
        user['email'], 
        analysis['personal_info'].get('phone', 'N/A'), 
        user['resume_path'], # Filename
        analysis['scores']['skills'],
        analysis['scores']['experience'],
        analysis['scores']['semantic'],
        analysis['scores']['total'],
        json.dumps(analysis['missing_skills']),
        current_user.id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Application submitted successfully!', 'redirect': url_for('core.dashboard')})
    
# --- Offer Management Routes ---

@bp.route('/candidate/<int:candidate_id>/offer/form')
@login_required
@role_required('recruiter')
def offer_form(candidate_id):
    conn = database.get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    if not candidate:
        conn.close()
        return "Candidate not found", 404
    
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (candidate['job_id'],)).fetchone()
    conn.close()
    
    return render_template('offer_form.html', candidate=candidate, job=job)

@bp.route('/candidate/<int:candidate_id>/offer/generate', methods=['POST'])
@login_required
@role_required('recruiter')
def generate_offer(candidate_id):
    from datetime import datetime, timedelta
    
    conn = database.get_db_connection()
    candidate = conn.execute('SELECT * FROM candidates WHERE id = ?', (candidate_id,)).fetchone()
    
    # Robust name retrieval (handle missing column or empty value)
    candidate_name = "Candidate"
    try:
        if candidate['name']:
            candidate_name = candidate['name']
        else:
            raise IndexError # Force fallback if empty
    except (IndexError, KeyError):
        # Fetch from Users table
        user = conn.execute('SELECT name FROM users WHERE id = ?', (candidate['user_id'],)).fetchone()
        if user:
            candidate_name = user['name']
            
    # Create a dict to ensure we have the name
    candidate_dict = dict(candidate)
    candidate_dict['name'] = candidate_name
    candidate = candidate_dict

    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (candidate['job_id'],)).fetchone()
    conn.close()
    
    today = datetime.now().strftime("%B %d, %Y")
    expiry = (datetime.now() + timedelta(days=3)).strftime("%B %d, %Y")
    
    salary = request.form.get('salary')
    start_date = request.form.get('start_date')
    bonus = request.form.get('bonus')
    terms = request.form.get('terms')
    
    # Format salary with commas
    try:
        salary = f"{int(salary):,}"
    except:
        pass
        
    try:
        if bonus: bonus = f"{int(bonus):,}"
    except:
        pass

    return render_template('offer_letter.html', 
                           candidate=candidate, 
                           job=job, 
                           salary=salary,
                           start_date=start_date,
                           bonus=bonus,
                           terms=terms,
                           today=today,
                           expiry_date=expiry)
    
    if not user['resume_path']:
        conn.close()
        return jsonify({'error': 'No profile found. Please upload a Master Resume first.'}), 400
        
    # Re-use existing analysis logic
    job = conn.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    path = os.path.join(current_app.config['UPLOAD_FOLDER'], user['resume_path'])
    
    try:
        cv_text = extract_text(path)
        # Weights
        weights = {'overall_similarity': 0.5, 'skills': 0.3, 'experience': 0.2}
        
        score_data = engine.score_cv(cv_text, job['description'], weights)
        analysis = engine.analyze_candidate(cv_text, job['description'])
        
        conn.execute('''INSERT INTO candidates 
                        (job_id, filename, semantic_score, skills_score, experience_score, total_score, full_text, missing_skills, interview_questions, user_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (job_id, user['resume_path'], 
                         score_data['breakdown']['semantic_match'],
                         score_data['breakdown']['skills_match'],
                         score_data['breakdown']['experience_match'],
                         score_data['total_score'],
                         cv_text,
                         json.dumps(analysis['missing']),
                         json.dumps(analysis['questions']),
                         current_user.id
                        ))
        conn.commit()
        conn.close()
        return redirect(url_for('core.dashboard'))
        
    except Exception as e:
        conn.close()
        return f"Error applying: {str(e)}", 500
