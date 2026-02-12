from flask import Flask, request, jsonify
from datetime import datetime
import json
import os
import pickle

# Google Drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Arquivo de log local
LOG_FILE = "logs.json"

# Nome do folder no Google Drive (coloque o ID da sua pasta)
DRIVE_FOLDER_ID = "1ajsiTAC1bBkeyN0ixaGd9w25RmR42FHR"

# Credenciais do Google Drive
GOOGLE_CRED_FILE = "tactile-vial-373717-4b5adeb02171.json"

# Inicializa serviço do Drive
def init_drive_service():
    creds = Credentials.from_service_account_file(GOOGLE_CRED_FILE, scopes=["https://www.googleapis.com/auth/drive.file"])
    service = build('drive', 'v3', credentials=creds)
    return service

drive_service = init_drive_service()

# Função para salvar log localmente
def save_local_log(entry):
    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []
    data.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Função para enviar log ao Google Drive
def upload_log_to_drive():
    if not os.path.exists(LOG_FILE):
        return
    file_metadata = {
        'name': f'logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
        'parents': [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(LOG_FILE, mimetype='application/json')
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"[Drive] Log enviado com sucesso!")
    # Limpa log local após envio
    os.remove(LOG_FILE)

# Rota para receber logs do front-end
@app.route("/log", methods=["POST"])
def log_event():
    data = request.json
    data["timestamp"] = datetime.utcnow().isoformat()
    save_local_log(data)
    try:
        upload_log_to_drive()
    except Exception as e:
        print(f"Erro ao enviar para Drive: {e}")
    return jsonify({"status":"ok"}), 200

# Health check
@app.route("/", methods=["GET"])
def home():
    return "JBrasil Labs Logging Server Active"

if __name__ == "__main__":
    # Porta 5000 é padrão para Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
