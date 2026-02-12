from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

app = Flask(__name__)
# Configuração robusta do CORS para evitar bloqueios no navegador
CORS(app, resources={r"/*": {"origins": "*"}})

SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'
SHEET_NAME = 'Logs' # Certifique-se que o nome da aba na planilha é exatamente este

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def append_log(entry):
    try:
        service = get_sheets_service()
        # Formato de valores esperado pelo Google: Lista de Listas
        body = {'values': [[entry]]}
        
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_NAME}'!A1", # Aspas simples tratam nomes com espaços
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"Erro no Google Sheets: {e}")
        return False

@app.route('/log', methods=['POST', 'OPTIONS'])
def receive_log():
    # Trata o preflight do CORS
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
        
    data = request.get_json()
    if not data or 'entry' not in data:
        return jsonify({'status': 'error', 'message': 'Payload inválido'}), 400

    entry = data['entry']
    if append_log(entry):
        return jsonify({'status': 'ok', 'message': 'Log registrado'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Falha na escrita'}), 500

@app.route('/')
def health_check():
    return "JBrasil Labs SOC Server Online", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
