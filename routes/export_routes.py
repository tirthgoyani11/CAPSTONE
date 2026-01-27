
import csv
import io
from flask import Blueprint, make_response, flash, redirect, url_for
from flask_login import login_required, current_user
import database

bp = Blueprint('export', __name__, url_prefix='/export')

@bp.route('/talent_pool/csv')
@login_required
def export_talent_pool_csv():
    try:
        # Get all candidates for the user
        candidates = database.get_all_candidates(current_user.id)
        
        # Create a CSV in memory
        si = io.StringIO()
        cw = csv.writer(si)
        
        # Header
        cw.writerow(['Name', 'Email', 'Phone', 'Applied Job', 'Status', 'Score', 'Skills Match'])
        
        # Rows
        for cand in candidates:
            # Convert Row to dict for safe access
            cand_dict = dict(cand) if hasattr(cand, 'keys') else cand
            
            cw.writerow([
                cand_dict.get('name', 'N/A') or cand_dict.get('filename', 'N/A'),
                cand_dict.get('email', 'N/A'),
                cand_dict.get('phone', 'N/A'),
                cand_dict.get('job_role', 'General'),
                cand_dict.get('status', 'Applied'),
                cand_dict.get('total_score', 0),
                cand_dict.get('skills_score', 0)
            ])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=talent_pool_export.csv"
        output.headers["Content-type"] = "text/csv"
        return output
        
    except Exception as e:
        print(f"Export Error: {e}")
        flash(f"Failed to export data: {e}", "danger")
        return redirect(url_for('talent_pool.index'))
