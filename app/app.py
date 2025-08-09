from flask import Flask, render_template, request, jsonify, redirect, url_for, flash #  type:ignore 
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TimeField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Optional, NumberRange
from datetime import datetime, date, time
import shelve
import uuid
from urllib.parse import quote

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

class MedicationForm(FlaskForm):
    name = StringField('Medication Name', validators=[DataRequired()], 
                      render_kw={"placeholder": "Enter medication name"})
    dosage = StringField('Dosage', validators=[DataRequired()], 
                        render_kw={"placeholder": "e.g., 50mg, 2 tablets"})
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[Optional()])
    time_to_take = TimeField('Time to Take', validators=[DataRequired()],
                            default=time(9, 0))  # Default to 9:00 AM
    frequency = SelectField('Frequency', 
                           choices=[
                               ('daily', 'Daily'),
                               ('twice_daily', 'Twice Daily'),
                               ('three_times_daily', 'Three Times Daily'),
                               ('weekly', 'Weekly'),
                               ('monthly', 'Monthly'),
                               ('as_needed', 'As Needed')
                           ],
                           validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[Optional()],
                               render_kw={"placeholder": "Special instructions (optional)", "rows": 3})
    color = StringField('Color', validators=[DataRequired()], default='#3788d8',
                       render_kw={"type": "color"})

class SeizureForm(FlaskForm):
    seizure_date = DateField('Seizure Date', validators=[DataRequired()])
    seizure_time = TimeField('Seizure Time', validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[Optional(), NumberRange(min=0)],
                           render_kw={"placeholder": "Duration in minutes"})
    seizure_type = SelectField('Seizure Type',
                              choices=[
                                  ('generalized_tonic_clonic', 'Generalized Tonic-Clonic'),
                                  ('focal_aware', 'Focal Aware'),
                                  ('focal_impaired_awareness', 'Focal Impaired Awareness'),
                                  ('absence', 'Absence'),
                                  ('myoclonic', 'Myoclonic'),
                                  ('atonic', 'Atonic'),
                                  ('unknown', 'Unknown/Other')
                              ],
                              validators=[DataRequired()])
    severity = SelectField('Severity',
                          choices=[
                              ('mild', 'Mild'),
                              ('moderate', 'Moderate'),
                              ('severe', 'Severe')
                          ],
                          validators=[DataRequired()])
    triggers = TextAreaField('Possible Triggers', validators=[Optional()],
                           render_kw={"placeholder": "Stress, lack of sleep, missed medication, etc.", "rows": 2})
    notes = TextAreaField('Additional Notes', validators=[Optional()],
                         render_kw={"placeholder": "Recovery time, symptoms, etc.", "rows": 3})
    color = StringField('Color', validators=[DataRequired()], default='#dc3545',
                       render_kw={"type": "color"})

def get_medications():
    """Get all medications from shelve database"""
    with shelve.open('medications.db') as shelf:
        return dict(shelf)

def save_medication(medication_id, medication_data):
    """Save medication to shelve database"""
    with shelve.open('medications.db') as shelf:
        shelf[medication_id] = medication_data

def delete_medication(medication_id):
    """Delete medication from shelve database"""
    with shelve.open('medications.db') as shelf:
        if medication_id in shelf:
            del shelf[medication_id]
            return True
    return False

def get_seizures():
    """Get all seizures from shelve database"""
    with shelve.open('seizures.db') as shelf:
        return dict(shelf)

def save_seizure(seizure_id, seizure_data):
    """Save seizure to shelve database"""
    with shelve.open('seizures.db') as shelf:
        shelf[seizure_id] = seizure_data

def delete_seizure(seizure_id):
    """Delete seizure from shelve database"""
    with shelve.open('seizures.db') as shelf:
        if seizure_id in shelf:
            del shelf[seizure_id]
            return True
    return False

def medication_to_calendar_event(med_id, med_data):
    """Convert medication data to FullCalendar event format"""
    end_date = med_data['end_date']
    if end_date and isinstance(end_date, date):
        # Add one day for FullCalendar's end date format
        from datetime import timedelta
        end_date = (end_date + timedelta(days=1)).isoformat()
    elif end_date:
        end_date = end_date.isoformat()
    
    # Create title with medication name and dosage
    title = f"💊 {med_data['name']} - {med_data['dosage']}"
    if med_data.get('time_to_take'):
        if isinstance(med_data['time_to_take'], time):
            time_str = med_data['time_to_take'].strftime('%I:%M %p')
        else:
            time_str = med_data['time_to_take']
        title += f" at {time_str}"
    
    return {
        'id': f"med_{med_id}",
        'title': title,
        'start': med_data['start_date'].isoformat() if isinstance(med_data['start_date'], date) else med_data['start_date'],
        'end': end_date,
        'backgroundColor': med_data.get('color', '#3788d8'),
        'borderColor': med_data.get('color', '#3788d8'),
        'allDay': False,
        'classNames': ['medication-event'],
        'extendedProps': {
            'type': 'medication',
            'name': med_data['name'],
            'dosage': med_data['dosage'],
            'frequency': med_data['frequency'],
            'instructions': med_data.get('instructions', ''),
            'time_to_take': med_data.get('time_to_take', '').strftime('%H:%M') if isinstance(med_data.get('time_to_take'), time) else med_data.get('time_to_take', '')
        }
    }

def seizure_to_calendar_event(seizure_id, seizure_data):
    """Convert seizure data to FullCalendar event format"""
    # Combine date and time for the event
    seizure_datetime = datetime.combine(seizure_data['seizure_date'], seizure_data['seizure_time'])
    
    title = f"⚡ Seizure - {seizure_data['seizure_type'].replace('_', ' ').title()}"
    if seizure_data.get('duration'):
        title += f" ({seizure_data['duration']}min)"
    
    return {
        'id': f"seizure_{seizure_id}",
        'title': title,
        'start': seizure_datetime.isoformat(),
        'backgroundColor': seizure_data.get('color', '#dc3545'),
        'borderColor': seizure_data.get('color', '#dc3545'),
        'allDay': False,
        'classNames': ['seizure-event'],
        'extendedProps': {
            'type': 'seizure',
            'seizure_type': seizure_data['seizure_type'],
            'severity': seizure_data['severity'],
            'duration': seizure_data.get('duration'),
            'triggers': seizure_data.get('triggers', ''),
            'notes': seizure_data.get('notes', '')
        }
    }

@app.route('/')
def index():
    """Main calendar page"""
    return render_template('NewCalendar.html')

@app.route('/add_medication')
def add_medication_page():
    """Add medication form page"""
    form = MedicationForm()
    return render_template('add_medication.html', form=form)

@app.route('/add_seizure')
def add_seizure_page():
    """Add seizure form page"""
    form = SeizureForm()
    return render_template('add_seizure.html', form=form)

@app.route('/api/events')
def get_events_api():
    """API endpoint to get all events (medications and seizures) as calendar events"""
    medications = get_medications()
    seizures = get_seizures()
    events = []
    
    # Add medication events
    for med_id, med_data in medications.items():
        events.append(medication_to_calendar_event(med_id, med_data))
    
    # Add seizure events
    for seizure_id, seizure_data in seizures.items():
        events.append(seizure_to_calendar_event(seizure_id, seizure_data))
    
    return jsonify(events)


@app.route('/edit_medication/<medication_id>', methods=['POST'])
def edit_medication_route(medication_id):
    """Edit existing medication"""
    medications = get_medications()
    if medication_id not in medications:
        return jsonify({'success': False, 'error': 'Medication not found'}), 404

    medication_data = medications[medication_id]
    form = MedicationForm()
    
    if form.validate_on_submit():
        # Validate end date is after start date
        if form.end_date.data and form.end_date.data <= form.start_date.data:
            return jsonify({'success': False, 'error': 'End date must be after start date'}), 400

        updated_data = {
            'name': form.name.data,
            'dosage': form.dosage.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
            'time_to_take': form.time_to_take.data,
            'frequency': form.frequency.data,
            'instructions': form.instructions.data,
            'color': form.color.data,
            'created_at': medication_data.get('created_at', datetime.now()),
            'updated_at': datetime.now()
        }

        save_medication(medication_id, updated_data)
        return jsonify({'success': True, 'message': 'Medication updated successfully!'})
    
    # Return validation errors
    errors = []
    for field, field_errors in form.errors.items():
        for error in field_errors:
            errors.append(f"{getattr(form, field).label.text}: {error}")
    return jsonify({'success': False, 'errors': errors}), 400

@app.route('/edit_seizure/<seizure_id>', methods=['POST'])
def edit_seizure_route(seizure_id):
    """Edit existing seizure"""
    seizures = get_seizures()
    if seizure_id not in seizures:
        return jsonify({'success': False, 'error': 'Seizure record not found'}), 404

    seizure_data = seizures[seizure_id]
    form = SeizureForm()
    
    if form.validate_on_submit():
        updated_data = {
            'seizure_date': form.seizure_date.data,
            'seizure_time': form.seizure_time.data,
            'duration': form.duration.data,
            'seizure_type': form.seizure_type.data,
            'severity': form.severity.data,
            'triggers': form.triggers.data,
            'notes': form.notes.data,
            'color': form.color.data,
            'created_at': seizure_data.get('created_at', datetime.now()),
            'updated_at': datetime.now()
        }

        save_seizure(seizure_id, updated_data)
        return jsonify({'success': True, 'message': 'Seizure record updated successfully!'})
    
    # Return validation errors
    errors = []
    for field, field_errors in form.errors.items():
        for error in field_errors:
            errors.append(f"{getattr(form, field).label.text}: {error}")
    return jsonify({'success': False, 'errors': errors}), 400

@app.route('/submit_medication', methods=['POST'])
def submit_medication():
    """Submit new medication"""
    form = MedicationForm()
    if form.validate_on_submit():
        # Validate end date is after start date
        if form.end_date.data and form.end_date.data <= form.start_date.data:
            flash('End date must be after start date', 'error')
            return redirect(url_for('add_medication_page'))

        medication_id = str(uuid.uuid4())
        medication_data = {
            'name': form.name.data,
            'dosage': form.dosage.data,
            'start_date': form.start_date.data,
            'end_date': form.end_date.data,
            'time_to_take': form.time_to_take.data,
            'frequency': form.frequency.data,
            'instructions': form.instructions.data,
            'color': form.color.data,
            'created_at': datetime.now()
        }

        save_medication(medication_id, medication_data)
        
        # Redirect to calendar with success message
        success_message = f"Medication '{form.name.data}' added successfully!"
        return redirect(url_for('index') + f'?success={quote(success_message)}&added=medication')
    
    # Handle validation errors
    for field, field_errors in form.errors.items():
        for error in field_errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'error')
    
    return redirect(url_for('add_medication_page'))

@app.route('/submit_seizure', methods=['POST'])
def submit_seizure():
    """Submit new seizure"""
    form = SeizureForm()
    if form.validate_on_submit():
        seizure_id = str(uuid.uuid4())
        seizure_data = {
            'seizure_date': form.seizure_date.data,
            'seizure_time': form.seizure_time.data,
            'duration': form.duration.data,
            'seizure_type': form.seizure_type.data,
            'severity': form.severity.data,
            'triggers': form.triggers.data,
            'notes': form.notes.data,
            'color': form.color.data,
            'created_at': datetime.now()
        }

        save_seizure(seizure_id, seizure_data)
        
        # Redirect to calendar with success message
        success_message = f"Seizure record added successfully!"
        return redirect(url_for('index') + f'?success={quote(success_message)}&added=seizure')
    
    # Handle validation errors
    for field, field_errors in form.errors.items():
        for error in field_errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'error')
    
    return redirect(url_for('add_seizure_page'))

# Also update delete routes
@app.route('/delete_medication/<medication_id>', methods=['POST'])
def delete_medication_route(medication_id):
    """Delete medication"""
    if delete_medication(medication_id):
        success_message = "Medication deleted successfully!"
        return redirect(url_for('index') + f'?success={quote(success_message)}&updated=medication')
    else:
        error_message = "Medication not found"
        return redirect(url_for('index') + f'?error={quote(error_message)}')

@app.route('/delete_seizure/<seizure_id>', methods=['POST'])
def delete_seizure_route(seizure_id):
    """Delete seizure"""
    if delete_seizure(seizure_id):
        success_message = "Seizure record deleted successfully!"
        return redirect(url_for('index') + f'?success={quote(success_message)}&updated=seizure')
    else:
        error_message = "Seizure record not found"
        return redirect(url_for('index') + f'?error={quote(error_message)}')
if __name__ == '__main__':
    app.run(debug=True)

