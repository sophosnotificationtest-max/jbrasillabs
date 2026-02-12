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
# Certifique-se de que o arquivo GeoLite2-Country.mmdb está na mesma pasta no Render
GEO_DB = 'GeoLite2-Country.mmdb'
geo_reader = geoip2.database.Reader(GEO_DB)

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

# --- NOVO: Endpoint para o Frontend consultar o IP ---
@app.route('/geoip', methods=['GET'])
def get_geoip():
    # Pega o IP real do visitante
    x_forwarded_for = request.headers.get('X-Forwarded-For', '')
    first_ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.remote_addr
    
    try:
        response = geo_reader.country(first_ip)
        country = response.country.name or "Desconhecido"
    except:
        country = "Desconhecido"
    
    # Retorna o formato que o seu JavaScript espera
    return jsonify({'entry': f"{first_ip} ({country})"}), 200

# --- Endpoint para receber logs ---
@app.route('/log', methods=['POST'])
def receive_log():
    data = request.get_json()
    # Se o front enviar a mensagem, gravamos ela. Se não, pegamos o IP aqui.
    entry = data.get('entry', 'Acesso detectado')

    x_forwarded_for = request.headers.get('X-Forwarded-For', '')
    first_ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.remote_addr

    try:
        response = geo_reader.country(first_ip)
        country = response.country.name or "Desconhecido"
    except:
        country = "Desconhecido"

    log_entry = f"[SOC] {entry} | IP: {first_ip} ({country})"
    append_log(log_entry)

    return jsonify({'status': 'ok', 'log': log_entry}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
