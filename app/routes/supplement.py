from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.supplement import UserSupplement
from app import db
from datetime import datetime

bp = Blueprint('supplement', __name__)

# List of all available supplements
SUPPLEMENTS = [
    "Omega 3", "Magnesium", "Multi Vitamin", "Boron", "Vitamin D", 
    "Fennel Seed", "Fenugreek", "Creatine", "Ashwagandha", "Collagen", 
    "Zinc", "Probiotic", "Shilajit", "Grape Seed Extract", "Tribulus", 
    "Calcium", "Ginseng", "Glucosamine Chondroitin", "B12", 
    "Folic Acid", "Vitamin K", "Tribulus Terrestris"
]

@bp.route('/track_supplements', methods=['GET', 'POST'])
@login_required
def track_supplements():
    today = datetime.now().date()
    
    if request.method == 'POST':
        # Delete existing entries for today to avoid duplicates
        UserSupplement.query.filter_by(
            user_id=current_user.id,
            date_taken=today
        ).delete()
        
        # Create new entries for each checked supplement
        for supplement in SUPPLEMENTS:
            if request.form.get(supplement.lower().replace(' ', '_')):
                new_supplement = UserSupplement(
                    user_id=current_user.id,
                    supplement_name=supplement,
                    date_taken=today
                )
                db.session.add(new_supplement)
        
        try:
            db.session.commit()
            flash('Supplements tracked successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving data: {str(e)}', 'error')
            
        return redirect(url_for('supplement.track_supplements'))
    
    # Get today's supplements for this user
    taken_supplements = UserSupplement.query.filter_by(
        user_id=current_user.id,
        date_taken=today
    ).all()
    
    # Convert to a set of names for easy checking
    taken_supplement_names = {s.supplement_name for s in taken_supplements}
    
    return render_template(
        'supplement/track_supplements.html', 
        supplements=SUPPLEMENTS,
        taken_supplements=taken_supplement_names,
        today=today
    )