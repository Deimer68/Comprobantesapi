# 🏦 Bancolombia → WhatsApp Notifier
## Guía completa y actualizada

---

## ✅ Lo que ya tienes listo (no tocar)

- ✅ Proyecto en Google Cloud: `bancolombia-notifier`
- ✅ Gmail API activada
- ✅ Pub/Sub API activada
- ✅ Tema Pub/Sub: `gmail-bancolombia`
- ✅ Suscripción Push apuntando a Railway
- ✅ Servidor en Railway corriendo
- ✅ CallMeBot configurado (phone: 573226642396, apikey: 5449419)
- ✅ Variables en Railway: GMAIL_USER_EMAIL, CALLMEBOT_PHONE, CALLMEBOT_APIKEY, PUBSUB_TOKEN, PUBSUB_TOPIC, PORT

---

## ❌ Lo que hay que cambiar (solo esto)

La Service Account no funciona con Gmail personal (@gmail.com).
Hay que usar OAuth2 en su lugar. Son 3 pasos simples.

---

## PASO 1 — Crear credencial OAuth2 en Google Cloud

1. Ve a https://console.cloud.google.com
2. Menú → **APIs y servicios → Credenciales**
3. Clic **+ Crear credenciales → ID de cliente OAuth 2.0**
4. Si pide configurar "pantalla de consentimiento" primero:
   - Tipo de usuario: **Externo**
   - Nombre de la app: `Bancolombia Notifier`
   - Correo de soporte: tu correo
   - Clic **Guardar y continuar** en todos los pasos
   - En "Usuarios de prueba" agrega tu correo de Gmail
5. Vuelve a **Credenciales → + Crear credenciales → ID de cliente OAuth 2.0**
6. Tipo de aplicación: **Aplicación de escritorio**
7. Nombre: `gmail-reader`
8. Clic **Crear**
9. Clic **Descargar JSON** → guarda el archivo como `client_secret.json`

---

## PASO 2 — Obtener el token de acceso (solo una vez, en tu PC)

Pon el archivo `client_secret.json` en la carpeta raíz de tu proyecto.
Luego en la terminal:

```bash
pip install google-auth-oauthlib google-api-python-client
python src/setup_oauth.py
```

Se abre el navegador → seleccionas tu cuenta de Gmail → autorizas el acceso.

En la terminal aparecerá:

```
============================================================
✅ Autorización exitosa. Guarda estos valores en Railway:
============================================================

GMAIL_CLIENT_ID     = 376903426812-xxxxxxxxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET = GOCSPX-xxxxxxxxxxxxxxxxxx
GMAIL_REFRESH_TOKEN = 1//xxxxxxxxxxxxxxxxxxxxxxxxxx

✅ Acceso verificado al correo: tucorreo@gmail.com
```

Copia esos 3 valores.

---

## PASO 3 — Actualizar Railway

### 3.1 — Variables
Ve a Railway → Variables y agrega:

| Variable | Valor |
|---|---|
| GMAIL_CLIENT_ID | el que apareció en la terminal |
| GMAIL_CLIENT_SECRET | el que apareció en la terminal |
| GMAIL_REFRESH_TOKEN | el que apareció en la terminal |

Y elimina: GOOGLE_CREDENTIALS_JSON (ya no se usa)

### 3.2 — Subir archivos nuevos a GitHub
Reemplaza en tu repositorio:
- src/main.py
- src/setup_gmail_watch.py
- src/setup_oauth.py (nuevo, agrégalo)
- requirements.txt

Railway redespliega automáticamente.

### 3.3 — Activar el Watch de Gmail
Railway → Settings → Pre-deploy Command:
```
python src/setup_gmail_watch.py
```
Guarda → Redeploy → en los logs debe aparecer:
```
✅ Gmail Watch activado:
```

---

## Variables finales en Railway

| Variable | Valor |
|---|---|
| GMAIL_USER_EMAIL | tu correo @gmail.com |
| GMAIL_CLIENT_ID | de Google Cloud |
| GMAIL_CLIENT_SECRET | de Google Cloud |
| GMAIL_REFRESH_TOKEN | del setup_oauth.py |
| CALLMEBOT_PHONE | 573226642396 |
| CALLMEBOT_APIKEY | 5449419 |
| PUBSUB_TOKEN | 235474 |
| PUBSUB_TOPIC | projects/bancolombia-notifier/topics/gmail-bancolombia |
| PORT | 8080 |
