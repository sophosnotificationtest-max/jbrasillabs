# server_drive.py
from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import os

app = Flask(__name__)

# Configurações
SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'  # credencial do Drive
FOLDER_ID = '1ajsiTAC1bBkeyN0ixaGd9w25RmR42FHR'  # ID da pasta no Drive
FILE_NAME = 'logs.txt'
LOCAL_LOG_FILE = '/tmp/logs.txt'  # Render aceita /tmp para escrita
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Autenticação Google Drive
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

def write_log_local(entry):
    """Salva log local temporário"""
    with open(LOCAL_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')

def upload_log_to_drive():
    """Cria ou atualiza logs.txt no Drive"""
    try:
        # Verifica se o arquivo já existe na pasta
        results = drive_service.files().list(
            q=f"name='{FILE_NAME}' and '{FOLDER_ID}' in parents",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        files = results.get('files', [])

        media = MediaFileUpload(LOCAL_LOG_FILE, mimetype='text/plain', resumable=True)

        if files:
            file_id = files[0]['id']
            drive_service.files().update(fileId=file_id, media_body=media).execute()
            print(f"[Drive] Log atualizado")
        else:
            file_metadata = {'name': FILE_NAME, 'parents': [FOLDER_ID]}
            drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"[Drive] Log criado")
    except Exception as e:
        print(f"[Erro Drive] {e}")

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.json
    if not data or 'entry' not in data:
        return jsonify({'status': 'error', 'message': 'entry missing'}), 400
    entry = data['entry']

    print(f"[Render] Log recebido: {entry}")

    # 1️⃣ Salva localmente
    write_log_local(entry)

    # 2️⃣ Envia para o Drive
    upload_log_to_drive()

    return jsonify({'status': 'ok', 'entry': entry}), 200

@app.route('/')
def index():
    return "JBrasil Labs Logging Server Active"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
