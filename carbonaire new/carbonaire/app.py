from flask import Flask, request, jsonify
from flask_cors import CORS
from rag.rag_engine import get_answer

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question", "").strip()
    user_data = data.get("userData", {})

    if not question:
        return jsonify({"answer": "Please ask a question."})

    answer = get_answer(question, user_data)
    return jsonify({"answer": answer})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)