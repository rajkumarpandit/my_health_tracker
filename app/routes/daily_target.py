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
    # Get existing targets
    targets = DailyTarget.query.filter_by(user_id=current_user.id).first()
    
    # Create the form
    form = DailyTargetForm()
    
    # Check if edit mode is enabled
    edit_mode = request.args.get('edit') == 'true'
    
    if request.method == 'POST':
        # Check which tab was used for submission
        tab = request.form.get('tab', 'advanced')
        
        if tab == 'basic':
            # Handle the basic tab form submission
            calories = request.form.get('basic_calories', 0)
            protein = request.form.get('basic_protein', 0)
            carbs = request.form.get('basic_carbs', 0)
            fat = request.form.get('basic_fat', 0)
            
            try:
                # Convert to float
                calories = float(calories) if calories else 0
                protein = float(protein) if protein else 0
                carbs = float(carbs) if carbs else 0
                fat = float(fat) if fat else 0
                
                if targets:
                    # Update existing targets
                    targets.calories = calories
                    targets.protein = protein
                    targets.carbs = carbs
                    targets.fat = fat
                    targets.updated_at = datetime.now()
                else:
                    # Create new targets
                    targets = DailyTarget(
                        user_id=current_user.id,
                        calories=calories,
                        protein=protein,
                        carbs=carbs,
                        fat=fat
                    )
                    db.session.add(targets)
                    
                db.session.commit()
                flash('Nutrition targets updated successfully!', 'success')
                return redirect(url_for('daily_target.daily_budget'))
                
            except ValueError:
                flash('Please enter valid numeric values for all nutrition fields.', 'error')
                return redirect(url_for('daily_target.daily_budget', edit='true'))
                
        else:  # Advanced tab
            # Original form validation logic
            if form.validate_on_submit():
                if targets:
                    # Update existing targets
                    targets.calories = form.calories.data
                    targets.protein = form.protein.data
                    targets.carbs = form.carbs.data
                    targets.fat = form.fat.data
                    targets.updated_at = datetime.now()
                else:
                    # Create new targets
                    targets = DailyTarget(
                        user_id=current_user.id,
                        calories=form.calories.data,
                        protein=form.protein.data,
                        carbs=form.carbs.data,
                        fat=form.fat.data
                    )
                    db.session.add(targets)
                    
                db.session.commit()
                flash('Nutrition targets updated successfully!', 'success')
                return redirect(url_for('daily_target.daily_budget'))
    
    # Populate form with existing data if available
    if targets and form:
        form.calories.data = targets.calories
        form.protein.data = targets.protein
        form.carbs.data = targets.carbs
        form.fat.data = targets.fat
    
    return render_template(
        'daily_target/budget.html', 
        form=form, 
        targets=targets, 
        edit_mode=edit_mode
    )