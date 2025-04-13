from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.exercise import UserExercise
from app import db
from datetime import datetime

bp = Blueprint('exercise', __name__)

@bp.route('/track_calories_burned', methods=['GET', 'POST'])
@login_required
def track_calories_burned():
    # Get today's exercise record if it exists
    today = datetime.now().date()
    exercise = UserExercise.query.filter_by(
        user_id=current_user.id,
        date_recorded=today
    ).first()
    
    if request.method == 'POST':
        # Extract data from form
        gym = int(request.form.get('gym', 0))
        running = int(request.form.get('running', 0))
        yoga = int(request.form.get('yoga', 0))
        zumba = int(request.form.get('zumba', 0))
        hiit = int(request.form.get('hiit', 0))
        cardio = int(request.form.get('cardio', 0))
        cycling = int(request.form.get('cycling', 0))
        swimming = int(request.form.get('swimming', 0))
        badminton = int(request.form.get('badminton', 0))
        lawn_tennis = int(request.form.get('lawn_tennis', 0))
        table_tennis = int(request.form.get('table_tennis', 0))
        volleyball = int(request.form.get('volleyball', 0))
        basketball = int(request.form.get('basketball', 0))
        cricket = int(request.form.get('cricket', 0))
        football = int(request.form.get('football', 0))
        walking = int(request.form.get('walking', 0))
        other_sports = int(request.form.get('other_sports', 0))
        usual_movement = int(request.form.get('usual_movement', 0))
        step_count = int(request.form.get('step_count', 0))
        
        # Calculate total
        total_calories = (gym + running + yoga + zumba + hiit + cardio + cycling + 
                          swimming + badminton + lawn_tennis + table_tennis + 
                          volleyball + basketball + cricket + football + walking + 
                          other_sports + usual_movement)
        
        if exercise:
            # Update existing record
            exercise.gym = gym
            exercise.running = running
            exercise.yoga = yoga
            exercise.zumba = zumba
            exercise.hiit = hiit
            exercise.cardio = cardio
            exercise.cycling = cycling
            exercise.swimming = swimming
            exercise.badminton = badminton
            exercise.lawn_tennis = lawn_tennis
            exercise.table_tennis = table_tennis
            exercise.volleyball = volleyball
            exercise.basketball = basketball
            exercise.cricket = cricket
            exercise.football = football
            exercise.walking = walking
            exercise.other_sports = other_sports
            exercise.usual_movement = usual_movement
            exercise.total_calories = total_calories
            exercise.step_count = step_count
            exercise.updated_at = datetime.now()
        else:
            # Create new record
            exercise = UserExercise(
                user_id=current_user.id,
                date_recorded=today,
                gym=gym,
                running=running,
                yoga=yoga,
                zumba=zumba,
                hiit=hiit,
                cardio=cardio,
                cycling=cycling,
                swimming=swimming,
                badminton=badminton,
                lawn_tennis=lawn_tennis,
                table_tennis=table_tennis,
                volleyball=volleyball,
                basketball=basketball,
                cricket=cricket,
                football=football,
                walking=walking,
                other_sports=other_sports,
                usual_movement=usual_movement,
                total_calories=total_calories,
                step_count=step_count
            )
            db.session.add(exercise)
            
        try:
            db.session.commit()
            flash('Calories burned information saved successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving data: {str(e)}', 'error')
            
        return redirect(url_for('exercise.track_calories_burned'))
    
    # For GET request, prepare the data for the template
    calories = {}
    if exercise:
        calories = {
            'gym': exercise.gym,
            'running': exercise.running,
            'yoga': exercise.yoga,
            'zumba': exercise.zumba,
            'hiit': exercise.hiit,
            'cardio': exercise.cardio,
            'cycling': exercise.cycling,
            'swimming': exercise.swimming,
            'badminton': exercise.badminton,
            'lawn_tennis': exercise.lawn_tennis,
            'table_tennis': exercise.table_tennis,
            'volleyball': exercise.volleyball,
            'basketball': exercise.basketball,
            'cricket': exercise.cricket,
            'football': exercise.football,
            'walking': exercise.walking,
            'other_sports': exercise.other_sports,
            'usual_movement': exercise.usual_movement,
            'total': exercise.total_calories,
            'step_count': exercise.step_count
        }
    
    return render_template(
        'exercise/track_calories.html', 
        calories=calories,
        today=today  # Pass today's date to the template
    )