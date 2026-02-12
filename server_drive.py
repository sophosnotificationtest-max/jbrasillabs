# server_drive.py
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
from flask_cors import CORS
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)  # Permite requisições CORS

# --- Configurações ---
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "tactile-vial-373717-4b5adeb02171.json")
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'  # ID da planilha
SHEET_NAME = 'Logs'  # Nome da aba da planilha
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- Autenticação ---
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=credentials)
sheet = sheet_service.spreadsheets()

# --- Logger ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def append_log_to_sheet(entry: str) -> bool:
    """Adiciona uma nova linha na aba Logs do Google Sheet"""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    values = [[timestamp, entry]]
    body = {'values': values}
    try:
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=SHEET_NAME,  # Corrigido: apenas nome da aba ou "Logs!A:B"
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        logging.info(f"[Sheet] Log adicionado: {entry}")
        return True
    except Exception as e:
        logging.error(f"[Erro Sheet] {e}", exc_info=True)
        return False

# --- Rotas ---
@app.route('/')
def index():
    return "JBrasil Labs Logging Server Active"

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.json
    if not data or 'entry' not in data:
        return jsonify({'status': 'error', 'message': 'entry missing'}), 400
    entry = str(data['entry']).strip()
    if len(entry) > 500:
        return jsonify({'status': 'error', 'message': 'entry too long'}), 400
    success = append_log_to_sheet(entry)
    status = 'ok' if success else 'error'
    return jsonify({'status': status, 'entry': entry}), 200 if success else 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Retorna os últimos 10 registros da planilha"""
    try:
        result = sheet.values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:B"
        ).execute()
        values = result.get('values', [])
        return jsonify({'status': 'ok', 'logs': values[-10:]})
    except Exception as e:
        logging.error(f"[Erro Sheet] {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- Run ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
