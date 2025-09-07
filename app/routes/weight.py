from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
from app.extensions import db
from app.models.weight import UserWeight

bp = Blueprint('weight', __name__)

@bp.route('/record_weight', methods=['GET', 'POST'])
@login_required
def record_weight():
    if request.method == 'POST':
        try:
            weight = float(request.form.get('weight'))
            date_str = request.form.get('date')
            date_recorded = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if weight already exists for this date
            existing_weight = UserWeight.query.filter_by(
                user_id=current_user.id,
                date_recorded=date_recorded
            ).first()
            
            if existing_weight:
                existing_weight.weight = weight
                existing_weight.created_at = datetime.now()
                flash('Weight updated successfully!', 'success')
            else:
                new_weight = UserWeight(
                    user_id=current_user.id,
                    weight=weight,
                    date_recorded=date_recorded
                )
                db.session.add(new_weight)
                flash('Weight recorded successfully!', 'success')
                
            db.session.commit()
            return redirect(url_for('weight.record_weight'))
            
        except ValueError:
            flash('Please enter a valid weight in kg', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording weight: {str(e)}', 'error')
    
    # Get last 7 days of weight data for the chart
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)  # Last 7 days including today
    
    weight_data = UserWeight.query.filter(
        UserWeight.user_id == current_user.id,
        UserWeight.date_recorded >= start_date,
        UserWeight.date_recorded <= end_date
    ).order_by(UserWeight.date_recorded).all()
    
    # Format data for chart.js
    dates = []
    weights = []
    
    for entry in weight_data:
        dates.append(entry.date_recorded.strftime('%Y-%m-%d'))
        weights.append(entry.weight)
    
    # Default to today's date
    today = datetime.now().date().strftime('%Y-%m-%d')
    # chart_dates = json.dumps(dates)
    # chart_weights = json.dumps(weights)
    
    return render_template(
        'weight/record.html',
        today=today,
        chart_dates=json.dumps(dates),
        chart_weights=json.dumps(weights)
    )