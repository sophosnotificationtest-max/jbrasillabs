from app import create_app

# Cria a instância do Flask
app = create_app()

# Apenas para rodar localmente com 'python wsgi.py'
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)