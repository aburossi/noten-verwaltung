import streamlit as st

def calculate_grade(points, max_points, scale_type='60% Scale'):
    if not points or not max_points or max_points == 0:
        return None
    
    percentage = points / max_points
    
    if scale_type == '60% Scale':
        note = (percentage * 5) + 1
    elif scale_type == '66% Scale':
        note = percentage * 6
    elif scale_type == '50% Scale':
        note = (percentage * 4) + 2
    else:
        note = (percentage * 5) + 1
    
    note = max(1.0, min(6.0, note))
    
    return {
        'note': round(note, 1),
        'percentage': round(percentage * 100, 1),
        'label': st.session_state.config['scales'][scale_type]['label']
    }

def calculate_weighted_average(student_id, subject):
    student_assignments = [
        a for a in st.session_state.assignments 
        if a['subject'] == subject and student_id in a.get('grades', {})
    ]
    
    if not student_assignments:
        return None
    
    total_weighted = 0
    total_weight = 0
    
    for assignment in student_assignments:
        grade = assignment['grades'].get(student_id)
        if grade is not None:
            try:
                grade_value = float(grade)
                weight = assignment.get('weight', 1.0)
                total_weighted += grade_value * weight
                total_weight += weight
            except (ValueError, TypeError):
                continue
    
    if total_weight > 0:
        return round(total_weighted / total_weight, 2)
    return None

def get_student_trend(student_id, subject):
    """
    Returns an icon and difference representing the trend between the last two graded assignments.
    """
    assigns = [a for a in st.session_state.assignments if a['subject'] == subject and student_id in a.get('grades', {})]
    assigns.sort(key=lambda x: x['date'], reverse=True) # Newest first
    
    if len(assigns) < 2:
        return None, 0
    
    try:
        newest = float(assigns[0]['grades'][student_id])
        previous = float(assigns[1]['grades'][student_id])
        diff = newest - previous
        
        if diff > 0.2: return "📈", diff
        elif diff < -0.2: return "📉", diff
        else: return "➡️", diff
    except:
        return None, 0