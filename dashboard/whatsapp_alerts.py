from twilio.rest import Client
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio configuration - Replace these with your actual values
TWILIO_ACCOUNT_SID = "AC679dbc6360e4c6b9784e253539e8f264"  # Replace with your Twilio Account SID
TWILIO_AUTH_TOKEN = "e1dc4653ddcdfaad1b551593a0c80daa"    # Replace with your Twilio Auth Token
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Default Twilio sandbox number
RECIPIENT_WHATSAPP_NUMBERS = [
    "whatsapp:+917418308109",  # Replace with recipient's WhatsApp number (format: whatsapp:+[country code][number])
    # Add more numbers if needed
]

def send_whatsapp_alert(message_type, details=None):
    """
    Send WhatsApp alert based on the type of alert (warning or danger)
    
    Args:
        message_type (str): Type of alert - 'warning' or 'danger'
        details (str, optional): Additional details about the alert
    
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN]) or TWILIO_ACCOUNT_SID == "YOUR_TWILIO_ACCOUNT_SID":
        logger.warning("Twilio credentials not configured. WhatsApp alert not sent.")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        current_time = datetime.datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        
        if message_type.lower() == 'danger':
            emoji_prefix = "🚨 *DANGER ALERT* 🚨"
            message_body = (
                f"{emoji_prefix}\n\n"
                f"⚠️ *Cattle Detection System* detected a *dangerous animal* in your farm area!\n\n"
                f"🔹 *Type*: {details or 'Unknown'}\n"
                f"🔹 *Time*: {current_time}\n"
                f"🔹 *Location*: Monitoring Area\n\n"
                f"🛑 *Immediate action required!* Please ensure all personnel stay clear of the area.\n\n"
                f"_This is an automated alert from your Cattle Detection System._"
            )
        elif message_type.lower() == 'warning':
            emoji_prefix = "⚠️ *WARNING* ⚠️"
            message_body = (
                f"{emoji_prefix}\n\n"
                f"👀 *Cattle Detection System* detected human presence in your farm area.\n\n"
                f"🔹 *Time*: {current_time}\n"
                f"🔹 *Location*: Monitoring Area\n\n"
                f"⚠️ *Caution advised* - Unexpected human activity detected.\n\n"
                f"_This is an automated alert from your Cattle Detection System._"
            )
        else:
            logger.error(f"Unknown message type: {message_type}")
            return False

        # Send message to all recipient numbers
        successful_sends = 0
        for recipient in RECIPIENT_WHATSAPP_NUMBERS:
            message = client.messages.create(
                body=message_body,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=recipient
            )
            logger.info(f"WhatsApp alert sent to {recipient}, SID: {message.sid}")
            successful_sends += 1
        
        return successful_sends > 0
            
    except Exception as e:
        logger.error(f"Failed to send WhatsApp alert: {str(e)}")
        return False
