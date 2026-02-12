from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
import geoip2.database
import os
from datetime import datetime

# --- Configurações Flask ---
app = Flask(__name__)
CORS(app)

# --- Google Sheets ---
SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'
SPREADSHEET_ID = '1WokAlWyXcYGlMjGWEWTlV9_Ej-GYJpuCTjOU8-r-HCQ'
SHEET_NAME = 'Logs'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- GeoIP2 ---
GEO_DB = 'GeoLite2-Country.mmdb'
geo_reader = geoip2.database.Reader(GEO_DB)

# --- Função para gravar log no Google Sheets ---
def append_log(entry: str) -> bool:
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
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
        print(f"Erro ao gravar no Google Sheets: {e}")
        return False

# --- Endpoint para receber logs ---
@app.route('/log', methods=['POST'])
def receive_log():
    data = request.get_json()
    entry = data.get('entry', 'Sem conteúdo')

    # Captura do IP real (primeiro do X-Forwarded-For ou remoto)
    x_forwarded_for = request.headers.get('X-Forwarded-For', '')
    first_ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.remote_addr

    # Detecta país via GeoLite2
    try:
        response = geo_reader.country(first_ip)
        country = response.country.name or "Desconhecido"
    except Exception:
        country = "Desconhecido"

    # Monta log final
    log_entry = f"[SOC] ACCESS GRANTED: {first_ip} ({country}, Detectado pelo Servidor)"
    
    # Envia para Google Sheets
    append_log(log_entry)

    return jsonify({'status': 'ok', 'log': log_entry}), 200

# --- Inicialização ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Servidor rodando na porta {port}")
    app.run(host='0.0.0.0', port=port)
