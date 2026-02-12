# server_drive.py
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

app = Flask(__name__)

# -----------------------------
# Configurações
# -----------------------------
SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'  # sua credencial JSON
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'  # ID do Sheet
SHEET_RANGE = 'Logs!A1'  # sempre apontar para a célula inicial A1
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Autenticação Google Sheets
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=credentials).spreadsheets()

# -----------------------------
# Função para enviar log
# -----------------------------
def write_log_to_sheet(entry: str):
    try:
        body = {'values': [[entry]]}  # cada entry em uma nova linha
        sheet_service.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=SHEET_RANGE,
            valueInputOption='RAW',      # mantém o texto como está
            insertDataOption='INSERT_ROWS',  # adiciona linha abaixo
            body=body
        ).execute()
        print(f"[Sheet] Log enviado: {entry}")
    except Exception as e:
        print(f"[Erro Sheet] {e}")

# -----------------------------
# Rotas Flask
# -----------------------------
@app.route('/log', methods=['POST'])
def receive_log():
    data = request.json
    if not data or 'entry' not in data:
        return jsonify({'status': 'error', 'message': 'entry missing'}), 400

    entry = data['entry']
    print(f"[Render] Log recebido: {entry}")

    write_log_to_sheet(entry)
    return jsonify({'status': 'ok', 'entry': entry}), 200

@app.route('/')
def index():
    return "JBrasil Labs Logging Server Active"

# -----------------------------
# Inicia servidor
# -----------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
