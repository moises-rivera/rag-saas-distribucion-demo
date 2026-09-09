"""Interfaz web local del RAG, ejecutable con ``python -m rag_final.webapp``."""

from flask import Flask, jsonify, render_template, request

from .service import answer_question


app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/ask")
def ask():
    if not request.is_json:
        return jsonify(error="La solicitud debe usar JSON."), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="El cuerpo JSON no es válido."), 400
    if "question" not in payload:
        return jsonify(error="Falta el campo 'question'."), 400

    question = payload["question"]
    if not isinstance(question, str):
        return jsonify(error="El campo 'question' debe ser texto."), 400
    if not question.strip():
        return jsonify(error="La pregunta no puede estar vacía."), 400

    try:
        return jsonify(answer_question(question))
    except ValueError as error:
        return jsonify(error=str(error)), 400
    except RuntimeError:
        return jsonify(
            error="No se pudo procesar la pregunta. Revisa la configuración del servidor."
        ), 503
    except Exception:
        return jsonify(error="Ocurrió un error interno al procesar la pregunta."), 500


@app.errorhandler(404)
def not_found(_error):
    return jsonify(error="Ruta no encontrada."), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify(error="Método HTTP no permitido."), 405


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
