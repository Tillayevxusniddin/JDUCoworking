# apps/meetings/google_api.py

from uuid import uuid4
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
import traceback

SERVICE_ACCOUNT_FILE = getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_FILE', None)
SCOPES = ['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']

def create_google_meet_event(title, description, start_time, end_time, attendees_emails):
    if not SERVICE_ACCOUNT_FILE:
        print("DIQQAT: Google Service Account fayli sozlanmagan.")
        return None, None

    try:
        # ✅ ASOSIY O'ZGARISH: Bu yerga universitetingiz emailini yozasiz
        DELEGATED_USER_EMAIL = '225158x@jdu.uz'

        credentials = service_account.Credentials.from_service_account_file(
            str(SERVICE_ACCOUNT_FILE), scopes=SCOPES
        )
        # Boshqa foydalanuvchi ("xo'jayin") nomidan ishlash uchun
        delegated_credentials = credentials.with_subject(DELEGATED_USER_EMAIL)
        service = build('calendar', 'v3', credentials=delegated_credentials)

        attendees = [{'email': email} for email in attendees_emails]

        event_body = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_time.isoformat(), 'timeZone': settings.TIME_ZONE},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': settings.TIME_ZONE},
            'attendees': attendees,
            'conferenceData': {
                'createRequest': {
                    'requestId': str(uuid4()),
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }

        created_event = service.events().insert(
            calendarId='primary',  # `DELEGATED_USER_EMAIL`ning asosiy kalendari
            body=event_body,
            conferenceDataVersion=1
        ).execute()

        print(f"✅ TADBIR TO'LIQ ({DELEGATED_USER_EMAIL} uchun) YARATILDI")

        conference_data = created_event.get('conferenceData', {})
        meet_link = next((ep['uri'] for ep in conference_data.get('entryPoints', []) if ep.get('entryPointType') == 'video'), None)
        event_id = created_event.get('id')

        return meet_link, event_id

    except Exception as e:
        print("❌ GOOGLE CALENDAR'DA TADBIR YARATISHDA XATOLIK:")
        traceback.print_exc()
        return None, None