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

# --- Leaderboard ---
scores = []

# --- Funções ---
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

def get_client_ip():
    x_forwarded_for = request.headers.get('X-Forwarded-For', '')
    return x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.remote_addr

def get_country(ip: str):
    try:
        response = geo_reader.country(ip)
        return response.country.name or "Desconhecido"
    except:
        return "Desconhecido"

# --- Endpoints ---
@app.route('/geoip', methods=['GET'])
def get_geoip():
    ip = get_client_ip()
    country = get_country(ip)
    return jsonify({'entry': f"{ip} ({country})"}), 200

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.get_json()
    entry = data.get('entry', 'Acesso detectado')
    ip = get_client_ip()
    country = get_country(ip)
    log_entry = f"[SOC] {entry} | IP: {ip} ({country})"
    append_log(log_entry)
    return jsonify({'status': 'ok', 'log': log_entry}), 200

# --- Leaderboard Endpoints ---
@app.route('/score', methods=['POST'])
def post_score():
    data = request.get_json()
    score = data.get('score')
    if score is not None:
        scores.append({'score': score})
        scores.sort(key=lambda x: x['score'], reverse=True)
        scores[:] = scores[:10]  # Mantém top 10
        return jsonify({'status': 'ok'}), 200
    return jsonify({'status': 'error', 'message': 'Score não enviado'}), 400

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    return jsonify(scores), 200

# --- Run Server ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
