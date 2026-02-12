from flask import Flask, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google.oauth2 import service_account
import io
import os

app = Flask(__name__)

SERVICE_ACCOUNT_FILE = 'tactile-vial-373717-4b5adeb02171.json'
FILE_NAME = 'logs.txt'  # arquivo já existente no Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Autenticação
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
drive_service = build('drive', 'v3', credentials=credentials)

def write_log_to_drive(entry):
    try:
        # Procura o arquivo pelo nome
        results = drive_service.files().list(
            q=f"name='{FILE_NAME}'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        files = results.get('files', [])

        if not files:
            print(f"[Erro Drive] Arquivo {FILE_NAME} não encontrado. Certifique-se que ele existe e a conta de serviço tem acesso.")
            return

        file_id = files[0]['id']
        content = entry + '\n'

        # Baixa conteúdo atual
        request_download = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_download)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        fh.seek(0)
        combined_content = fh.read() + content.encode('utf-8')

        # Atualiza arquivo
        media = MediaIoBaseUpload(io.BytesIO(combined_content), mimetype='text/plain')
        drive_service.files().update(fileId=file_id, media_body=media).execute()
        print(f"[Drive] Log atualizado: {entry}")

    except Exception as e:
        print(f"[Erro Drive] {e}")

@app.route('/log', methods=['POST'])
def receive_log():
    data = request.json
    if not data or 'entry' not in data:
        return jsonify({'status':'error','message':'entry missing'}), 400
    entry = data['entry']
    print(f"[Render] Log recebido: {entry}")
    write_log_to_drive(entry)
    return jsonify({'status':'ok','entry':entry}), 200

@app.route('/')
def index():
    return "JBrasil Labs Logging Server Active"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
