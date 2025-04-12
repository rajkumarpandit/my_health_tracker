from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class DailyTargetForm(FlaskForm):
    calories = FloatField('Daily Calorie Target', 
                         validators=[DataRequired(), NumberRange(min=0, max=10000)])
    protein = FloatField('Daily Protein Target (g)', 
                        validators=[DataRequired(), NumberRange(min=0, max=1000)])
    fat = FloatField('Daily Fat Target (g)', 
                     validators=[DataRequired(), NumberRange(min=0, max=1000)])
    carbs = FloatField('Daily Carbs Target (g)', 
                       validators=[DataRequired(), NumberRange(min=0, max=1000)])
    submit = SubmitField('Save Targets')