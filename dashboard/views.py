from django.shortcuts import render
from firebase_admin import credentials, db, initialize_app
from django.http import JsonResponse
from .whatsapp_alerts import send_whatsapp_alert
import logging
import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("hello/credentials.json")  # Path to your credentials.json
initialize_app(cred, {
    "databaseURL": "https://cattle-detection-project-default-rtdb.asia-southeast1.firebasedatabase.app"
})

# Track alert states to avoid duplicate alerts
previous_alert_state = {
    "is_danger": False,
    "danger_animal": None,
    "warning": False,
    "last_alert_time": None
}

# Maximum time (in seconds) before data is considered stale
DATA_FRESHNESS_THRESHOLD = 30  # 30 seconds

def dashboard_view(request):
    # Fetch data from Firebase Realtime Database
    ref = db.reference("/")
    data = ref.get()

    # Pass the data to the template
    return render(request, "dashboard/dashboard.html", {"data": data})

def fetch_data_api(request):
    global previous_alert_state
    
    # Fetch data from Firebase Realtime Database
    ref = db.reference("/")
    data = ref.get()
    
    # Check data freshness
    current_time = datetime.datetime.now()
    current_timestamp = int(time.time() * 1000)  # Current time in milliseconds
    
    # Initialize system_online flag with proper default value
    data['system_online'] = False  # Default to offline until verified otherwise
    
    # If last_updated exists, check if data is stale
    if 'last_updated' in data:
        time_diff_seconds = (current_timestamp - data['last_updated']) / 1000
        
        # Only consider system online if data is fresh (less than threshold)
        if time_diff_seconds <= DATA_FRESHNESS_THRESHOLD:
            data['system_online'] = True
            logger.info(f"System detected as online. Last update was {time_diff_seconds:.1f} seconds ago")
        else:
            logger.info(f"Data is stale. Last update was {time_diff_seconds:.1f} seconds ago")
            data['system_online'] = False
            data['time_since_update'] = format_time_since(time_diff_seconds)
    else:
        # If no timestamp exists, consider data stale
        data['system_online'] = False
        data['time_since_update'] = "unknown"
    
    # Only process alerts if the system is online
    if data['system_online']:
        min_alert_interval = datetime.timedelta(minutes=5)  # Minimum time between alerts
        
        # Process danger alerts
        if data.get('is_danger', False) and (
            not previous_alert_state['is_danger'] or 
            previous_alert_state['danger_animal'] != data.get('danger_animal') or
            (previous_alert_state['last_alert_time'] and 
             current_time - previous_alert_state['last_alert_time'] > min_alert_interval)
        ):
            # Send WhatsApp danger alert
            alert_sent = send_whatsapp_alert('danger', data.get('danger_animal', 'Unknown animal'))
            if alert_sent:
                logger.info(f"Danger WhatsApp alert sent for {data.get('danger_animal')}")
                data['alert_sent'] = True
                previous_alert_state['last_alert_time'] = current_time
            else:
                data['alert_sent'] = False
        
        # Process warning alerts (only if no danger alert is active)
        elif data.get('warning', False) and not data.get('is_danger', False) and (
            not previous_alert_state['warning'] or
            (previous_alert_state['last_alert_time'] and 
             current_time - previous_alert_state['last_alert_time'] > min_alert_interval)
        ):
            # Send WhatsApp warning alert
            alert_sent = send_whatsapp_alert('warning')
            if alert_sent:
                logger.info("Warning WhatsApp alert sent for human detection")
                data['alert_sent'] = True
                previous_alert_state['last_alert_time'] = current_time
            else:
                data['alert_sent'] = False
        
        # Update previous state tracker
        previous_alert_state['is_danger'] = data.get('is_danger', False)
        previous_alert_state['danger_animal'] = data.get('danger_animal')
        previous_alert_state['warning'] = data.get('warning', False)
    
    return JsonResponse({"data": data})

def format_time_since(seconds):
    """Format the time since last update in a human-readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days > 1 else ''}"
