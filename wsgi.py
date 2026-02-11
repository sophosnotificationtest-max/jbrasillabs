from app import app  # importa o objeto Flask direto

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
