from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

app = Flask(__name__)

# ---------- CONFIGURAÇÃO ----------
SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'
SHEET_NAME = 'Logs'  # Nome da aba dentro do Sheet
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# -----------------------------------

# Autentica com o Google Sheets
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheets_service = build('sheets', 'v4', credentials=credentials)

def append_log_to_sheet(entry):
    """Adiciona uma nova linha na planilha Google Sheets"""
    try:
        body = {'values': [[entry]]}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:A",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        print(f"[Sheet] Log adicionado: {entry}")
    except Exception as e:
        print(f"[Erro Sheet] {e}")

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.json
    if not data or 'entry' not in data:
        return jsonify({'status': 'error', 'message': 'entry missing'}), 400

    entry = data['entry']
    print(f"[Render] Log recebido: {entry}")

    append_log_to_sheet(entry)

    return jsonify({'status':'ok','entry':entry}), 200

@app.route('/')
def index():
    return "JBrasil Labs Logging Server Active"

if __name__ == '__main__':
    # Render define a variável de ambiente PORT automaticamente
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
