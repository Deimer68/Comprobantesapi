"""
Bancolombia Payment Notifier
Servidor principal que recibe webhooks de Gmail y notifica via WhatsApp
Usa OAuth2 — compatible con Gmail personal (@gmail.com)
"""

import os
import json
import base64
import re
import hmac
from datetime import datetime
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import requests

# ─── CONFIGURACIÓN ──────────────────────────────────────────────────────────

GMAIL_CLIENT_ID     = os.environ["GMAIL_CLIENT_ID"]
GMAIL_CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
GMAIL_REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]
GMAIL_USER_EMAIL    = os.environ["GMAIL_USER_EMAIL"]
CALLMEBOT_PHONE     = os.environ["CALLMEBOT_PHONE"]
CALLMEBOT_APIKEY    = os.environ["CALLMEBOT_APIKEY"]
PUBSUB_TOKEN        = os.environ["PUBSUB_TOKEN"]

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

def get_gmail_service():
    """Crea el cliente de Gmail API usando OAuth2 refresh token."""
    creds = Credentials(
        token=None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds)


def get_email_body(service, message_id: str) -> str:
    """Obtiene el cuerpo completo del correo en texto plano."""
    msg = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    parts = msg.get("payload", {}).get("parts", [])

    def extract_text(parts_list):
        text = ""
        for part in parts_list:
            if part["mimeType"] == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    text += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif "parts" in part:
                text += extract_text(part["parts"])
        return text

    if parts:
        body = extract_text(parts)
    else:
        data = msg.get("payload", {}).get("body", {}).get("data", "")
        if data:
            body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        else:
            body = ""

    return body


def parse_bancolombia_email(body: str) -> dict | None:
    """Extrae monto, remitente y referencia del correo de Bancolombia."""
    monto_pattern = r"por \$?([\d.,]+)"
    remit_pattern = r"transferencia de ([A-Za-záéíóúÁÉÍÓÚñÑ\s]+) por"
    ref_pattern   = r"llave\s+(\d+)"

    monto = re.search(monto_pattern, body, re.IGNORECASE)
    remit = re.search(remit_pattern, body, re.IGNORECASE)
    ref   = re.search(ref_pattern,   body, re.IGNORECASE)

    if not monto:
        return None

    return {
        "monto":      monto.group(1).strip() if monto else "No encontrado",
        "remitente":  remit.group(1).strip() if remit else "No encontrado",
        "referencia": ref.group(1).strip()   if ref   else "No encontrado",
        "hora":       datetime.now().strftime("%I:%M %p"),
        "fecha":      datetime.now().strftime("%d/%m/%Y"),
    }


def send_whatsapp(payment: dict):
    """Envía el mensaje de notificación vía CallMeBot."""
    mensaje = (
        f"✅ *PAGO RECIBIDO*\n"
        f"💰 Monto: ${payment['monto']}\n"
        f"👤 De: {payment['remitente']}\n"
        f"🕐 Hora: {payment['hora']}\n"
        f"📅 Fecha: {payment['fecha']}\n"
        f"📋 Ref: {payment['referencia']}"
    )

    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={CALLMEBOT_PHONE}"
        f"&text={requests.utils.quote(mensaje)}"
        f"&apikey={CALLMEBOT_APIKEY}"
    )

    resp = requests.get(url, timeout=10)
    print(f"[WhatsApp] Status: {resp.status_code} | {resp.text[:100]}")
    return resp.status_code == 200


# ─── WEBHOOK ────────────────────────────────────────────────────────────────

@app.route("/webhook/gmail", methods=["POST"])
def gmail_webhook():
    """Google Pub/Sub llama este endpoint cuando llega un correo nuevo."""

    # 1. Validar token
    token = request.args.get("token", "")
    if not hmac.compare_digest(token, PUBSUB_TOKEN):
        print("[Webhook] Token inválido")
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Decodificar mensaje Pub/Sub
    envelope = request.get_json(silent=True)
    if not envelope or "message" not in envelope:
        return jsonify({"error": "Bad request"}), 400

    pubsub_message = envelope["message"]
    data_b64 = pubsub_message.get("data", "")
    data = json.loads(base64.b64decode(data_b64).decode("utf-8"))

    print(f"[Webhook] Notificación recibida | historyId: {data.get('historyId')}")

    # 3. Buscar correo reciente de Bancolombia
    service  = get_gmail_service()
    results  = service.users().messages().list(
        userId="me",
        q="from:alertasynotificaciones@an.notificacionesbancolombia.com newer_than:1h",
        maxResults=1
    ).execute()

    messages = results.get("messages", [])
    if not messages:
        print("[Webhook] No se encontró correo de Bancolombia reciente")
        return jsonify({"status": "no_payment_email"}), 200

    # 4. Parsear el correo
    message_id = messages[0]["id"]
    body       = get_email_body(service, message_id)
    payment    = parse_bancolombia_email(body)

    if not payment:
        print("[Webhook] Correo encontrado pero no es de pago")
        return jsonify({"status": "not_payment"}), 200

    # 5. Enviar WhatsApp
    print(f"[Webhook] Pago detectado: ${payment['monto']} de {payment['remitente']}")
    sent = send_whatsapp(payment)

    return jsonify({
        "status":  "notified" if sent else "whatsapp_failed",
        "payment": payment
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
