from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from ..extensions import db
from ..forms.daily_target import DailyTargetForm
from ..models.daily_target import DailyTarget
from datetime import datetime

bp = Blueprint('daily_target', __name__)

@bp.route('/daily_budget', methods=['GET', 'POST'])
@login_required
def daily_budget():
    form = DailyTargetForm()
    edit_mode = request.args.get('edit', 'false') == 'true'
    
    # Get existing targets
    targets = DailyTarget.query.filter_by(user_id=current_user.id).first()
    
    if form.validate_on_submit():
        if targets:
            # Update existing targets
            targets.calories = form.calories.data
            targets.protein = form.protein.data
            targets.fat = form.fat.data
            targets.carbs = form.carbs.data
            targets.date_modified = datetime.now()  # Changed from utcnow() to now()
        else:
            # Create new targets
            targets = DailyTarget(
                user_id=current_user.id,
                calories=form.calories.data,
                protein=form.protein.data,
                fat=form.fat.data,
                carbs=form.carbs.data
            )
            db.session.add(targets)
            
        db.session.commit()
        flash('Daily targets updated successfully!', 'success')
        return redirect(url_for('daily_target.daily_budget'))
        
    elif targets:
        # Pre-populate form with existing targets
        form.calories.data = targets.calories
        form.protein.data = targets.protein
        form.fat.data = targets.fat
        form.carbs.data = targets.carbs
        
    return render_template('daily_target/budget.html', form=form, edit_mode=edit_mode, targets=targets)