from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'
SHEET_NAME = 'Logs'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def append_log(entry):
    try:
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        values = [[timestamp, entry]]
        body = {'values': values}
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:B",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"Erro Sheet: {e}")
        return False

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.get_json()
    entry = data.get('entry', 'Sem conteúdo')
    
    # Se o JS falhou, o Python pega o IP aqui:
    if "Analisando" in entry or "Unknown" in entry:
        real_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        entry = f"[SOC] ACCESS GRANTED: {real_ip} (Detectado pelo Servidor)"

    append_log(entry)
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
