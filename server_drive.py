# server_drive.py
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

app = Flask(__name__)

# Configurações
SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'  # sua credencial
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'  # ID da planilha
SHEET_NAME = 'Logs'  # nome da aba que você criou
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Autenticação Google Sheets
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheet_service = build('sheets', 'v4', credentials=credentials)
sheet = sheet_service.spreadsheets()

def write_log_to_sheet(entry):
    """Adiciona um log à aba Logs da planilha"""
    try:
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=SHEET_NAME,  # não usar A:A
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [[entry]]}
        ).execute()
        print(f"[Sheet] Log enviado: {entry}")
    except Exception as e:
        print(f"[Erro Sheet] {e}")

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
