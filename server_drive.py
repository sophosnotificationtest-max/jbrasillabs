from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from datetime import datetime

app = Flask(__name__)
# Configuração de CORS para permitir requisições do seu domínio ou local
CORS(app)

# CONFIGURAÇÕES
SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'
SHEET_NAME = 'Logs' # Certifique-se que o nome na aba é exatamente este
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def append_log(entry):
    try:
        service = get_sheets_service()
        # Captura o horário atual para o log ser organizado
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        # Valores organizados em colunas: [Data, Conteúdo do Log]
        values = [[timestamp, entry]]
        body = {'values': values}
        
        # Range simplificado: "Logs!A:B" evita o erro "Unable to parse range"
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:B",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"ERRO SOC: {e}")
        return False

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.get_json()
    if not data or 'entry' not in data:
        return jsonify({'status': 'error', 'message': 'Payload vazio'}), 400

    # Pega o IP real do cliente via cabeçalho do Render/Proxy
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Se o front-end falhou em pegar o IP, usamos o que o servidor detectou
    entry = data['entry'].replace("Unknown", client_ip)
    
    if append_log(entry):
        return jsonify({'status': 'ok'}), 200
    return jsonify({'status': 'error'}), 500

@app.route('/')
def home():
    return "JBrasil Labs SOC Online", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
