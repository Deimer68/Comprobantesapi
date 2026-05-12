"""
setup_oauth.py
Ejecuta este script UNA SOLA VEZ en tu computador local.
Te abre el navegador para autorizar acceso a Gmail,
y al final imprime el refresh_token que debes poner en Railway.

Requisitos:
  pip install google-auth-oauthlib google-api-python-client

Pasos:
  1. Descarga el archivo client_secret.json desde Google Cloud Console
     (APIs y servicios → Credenciales → OAuth 2.0 → Descargar JSON)
  2. Pon client_secret.json en la misma carpeta que este script
  3. Ejecuta: python setup_oauth.py
  4. Autoriza en el navegador
  5. Copia el refresh_token que aparece en la terminal
  6. Agrégalo en Railway como variable GMAIL_REFRESH_TOKEN
  7. Ejecuta también setup_gmail_watch.py para activar el watch
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

CLIENT_SECRET_FILE = "client_secret.json"

def main():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "="*60)
    print("✅ Autorización exitosa. Guarda estos valores en Railway:")
    print("="*60)
    print(f"\nGMAIL_CLIENT_ID     = {creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET = {creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN = {creds.refresh_token}")
    print("\n" + "="*60)

    # Verificar que funciona
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()
    print(f"\n✅ Acceso verificado al correo: {profile['emailAddress']}")
    print(f"   Total de mensajes: {profile['messagesTotal']}")

if __name__ == "__main__":
    main()
