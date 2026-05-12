"""
setup_gmail_watch.py
Registra el webhook de Gmail Push Notifications.
Ejecuta esto UNA VEZ (y cada 7 días para renovar).
Usa OAuth2 con refresh_token — compatible con Gmail personal.
"""

import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_credentials():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds

def setup_watch():
    creds   = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    request_body = {
        "labelIds":  ["INBOX"],
        "topicName": os.environ["PUBSUB_TOPIC"],
    }

    response = service.users().watch(userId="me", body=request_body).execute()
    print("✅ Gmail Watch activado:")
    print(f"   historyId: {response['historyId']}")
    print(f"   expira:    {response['expiration']} (epoch ms)")
    print("\nRecuerda renovarlo cada 7 días.")

if __name__ == "__main__":
    setup_watch()
