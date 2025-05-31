
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import datetime

# --- Налаштування ---
SCOPES = ['https://www.googleapis.com/auth/calendar']

# --- Визначаємо повний шлях до credentials.json ---
script_dir = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(script_dir, 'credentials.json')
TOKEN_PATH = os.path.join(script_dir, 'token.pickle')

# --- Створення token.pickle ---
def create_token():
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Не знайдено файл credentials.json за шляхом: {CREDENTIALS_PATH}")
        return
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'wb') as token:
        pickle.dump(creds, token)
    print("✅ Файл token.pickle успішно створено.")

# --- Завантаження токена ---
def load_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    # Якщо токен недійсний або закінчився — оновити
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds

# --- Виведення найближчих подій ---
def show_upcoming_events():
    creds = load_credentials()
    if not creds:
        print("❌ Немає дійсного токена. Спочатку запустіть create_token().")
        return

    service = build('calendar', 'v3', credentials=creds)
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' означає UTC
    print('🔎 Отримання наступних 10 подій...')

    events_result = service.events().list(
        calendarId='primary', timeMin=now,
        maxResults=10, singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        print('📭 Подій не знайдено.')
        return

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f"📅 {start} — {event['summary']}")

if __name__ == '__main__':
    # Спочатку створіть токен, якщо його ще немає
    if not os.path.exists(TOKEN_PATH):
        create_token()
    else:
        show_upcoming_events()
