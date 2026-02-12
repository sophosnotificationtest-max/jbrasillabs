from flask import Flask, request, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import io
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

app = Flask(__name__)

# Caminho para o arquivo JSON da Service Account
SERVICE_ACCOUNT_FILE = 'credenciais.json'
SCOPES = ['https://www.googleapis.com/auth/drive']

# ID da pasta no Google Drive onde o log será armazenado
FOLDER_ID = 'ID_DA_PASTA_DO_DRIVE'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

# Nome do arquivo de log
LOG_FILE_NAME = 'log.txt'

def append_log_line(line):
    # Verifica se o arquivo já existe
    results = drive_service.files().list(
        q=f"name='{LOG_FILE_NAME}' and '{FOLDER_ID}' in parents",
        fields="files(id, name)"
    ).execute()
    files = results.get('files', [])
    
    if files:
        file_id = files[0]['id']
        # Baixa conteúdo atual
        request_download = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_download)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        content = fh.getvalue().decode() + line + "\n"
        
        # Envia arquivo atualizado
        fh = io.BytesIO(content.encode())
        media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        # Cria arquivo novo
        fh = io.BytesIO(line.encode())
        media = MediaIoBaseUpload(fh, mimetype='text/plain', resumable=True)
        file_metadata = {'name': LOG_FILE_NAME, 'parents': [FOLDER_ID]}
        drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

@app.route('/log', methods=['POST'])
def log():
    data = request.json
    ip = data.get("ip", "Desconhecido")
    country = data.get("country", "Desconhecido")
    browser = data.get("browser", "Desconhecido")
    action = data.get("action", "unknown")
    time = datetime.utcnow().isoformat()
    
    line = f"[{time}] {ip} ({country}) Browser: {browser} Action: {action}"
    append_log_line(line)
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
