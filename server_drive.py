# server_drive.py
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

app = Flask(__name__)

# -----------------------------
# Configurações Google Sheets
# -----------------------------
SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'  # Substitua pelo seu JSON
SHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'       # ID da planilha
SHEET_NAME = 'Logs'                                             # Aba da planilha
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Autenticação
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
sheets_service = build('sheets', 'v4', credentials=credentials)
sheet = sheets_service.spreadsheets()

# -----------------------------
# Função para enviar log
# -----------------------------
def write_log_to_sheet(entry: str):
    """Adiciona um log como nova linha na aba Logs"""
    try:
        body = {"values": [[entry]]}  # Cada log é uma linha
        sheet.values().append(
            spreadsheetId=SHEET_ID,
            range=f"{SHEET_NAME}!A:A",           # Coluna A da aba Logs
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
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

    # Envia para Google Sheets
    write_log_to_sheet(entry)

    return jsonify({'status': 'ok', 'entry': entry}), 200

@app.route('/')
def index():
    return "JBrasil Labs Logging Server Active"

# -----------------------------
# Inicialização
# -----------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
