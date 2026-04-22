import os

import chromadb
import requests
from sentence_transformers import SentenceTransformer

# Load once when server starts
print("Loading RAG engine...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./rag/chroma_db")
collection = client.get_collection("carbonaire")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

def get_answer(user_question, user_data=None):
    # Step 1 — embed the question
    q_embedding = embedder.encode([user_question]).tolist()

    # Step 2 — find top 3 most relevant Q&A entries
    results = collection.query(
        query_embeddings=q_embedding,
        n_results=3
    )

    # Step 3 — build context from retrieved answers
    retrieved = results["metadatas"][0]
    context = ""
    for i, item in enumerate(retrieved):
        context += f"\nEntry {i+1}:\nQ: {item['question']}\nA: {item['answer']}\n"

    # Step 4 — build user data string
    user_context = ""
    if user_data:
        total    = user_data.get("total", 0)
        scope1   = user_data.get("scope1", 0)
        scope2   = user_data.get("scope2", 0)
        scope3   = user_data.get("scope3", 0)
        band     = user_data.get("band", "unknown")
        intensity = user_data.get("intensity", 0)
        renewable = user_data.get("renewable", 0)
        employees = user_data.get("employees", 0)
        servers  = user_data.get("servers", 0)
        company_name = user_data.get("company_name", "the user")
        industry_type = user_data.get("industry_type", "IT")
        location_state = user_data.get("location_state", "India")

        user_context = f"""
The user's actual emission data from Carbonaire:
- Company: {company_name}
- Industry: {industry_type}
- Location: {location_state}
- Total emissions: {total} tCO2e/year
- Scope 1 (fuel/diesel): {scope1} tCO2e
- Scope 2 (electricity): {scope2} tCO2e
- Scope 3 (cloud/travel): {scope3} tCO2e
- Carbon intensity: {intensity} tCO2e per Rs Crore
- Performance band: {band}
- Renewable energy: {renewable}%
- Employees: {employees}
- On-premise servers: {servers}
Always refer to these numbers specifically in your answer.
"""

    # Step 5 — call Ollama (local Mistral)
    prompt = f"""You are Carbonaire's AI assistant for IT companies in India.
You help users understand and reduce their carbon emissions.

{user_context}

Use the following knowledge to answer the question:
{context}

Question: {user_question}

Give a clear, specific answer in 3 to 5 sentences. 
If the user has emission data above, refer to their actual numbers.
If the question is completely unrelated to carbon emissions or Carbonaire, say:
"I can only help with questions about carbon emissions and Carbonaire."
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 300
                }
            },
            timeout=60
        )
        response.raise_for_status()
        answer = response.json()["response"].strip()
    except Exception as e:
        answer = f"Ollama server not responding. Make sure it is running. Error: {str(e)}"

    return answer
