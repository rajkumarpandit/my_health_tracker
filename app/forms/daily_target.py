from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class DailyTargetForm(FlaskForm):
    calories = FloatField('Calorie Target', 
                         validators=[DataRequired(), NumberRange(min=0, max=10000)])
    protein = FloatField('Protein Target (g)', 
                        validators=[DataRequired(), NumberRange(min=0, max=1000)])
    fat = FloatField('Fat Target (g)', 
                     validators=[DataRequired(), NumberRange(min=0, max=1000)])
    carbs = FloatField('Carbs Target (g)', 
                       validators=[DataRequired(), NumberRange(min=0, max=1000)])
    submit = SubmitField('Save Targets')