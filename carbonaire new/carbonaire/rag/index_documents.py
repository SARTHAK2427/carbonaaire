import json
import chromadb
from sentence_transformers import SentenceTransformer

def build_index():
    # Load Q&A dataset
    with open("rag/carbon_qa.json", "r") as f:
        qa_data = json.load(f)

    # Load embedding model (downloads once, ~80MB)
    print("Loading embedding model...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    # Connect to ChromaDB
    client = chromadb.PersistentClient(path="./rag/chroma_db")
    
    # Delete existing collection if rebuilding
    try:
        client.delete_collection("carbonaire")
    except:
        pass
    
    collection = client.create_collection("carbonaire")

    # Prepare data
    documents = []
    ids = []
    metadatas = []

    for item in qa_data:
        # Combine question + keywords + answer for richer embedding
        full_text = item["question"] + " " + " ".join(item["keywords"]) + " " + item["answer"]
        documents.append(full_text)
        ids.append(str(item["id"]))
        metadatas.append({
            "question": item["question"],
            "answer": item["answer"]
        })

    # Generate embeddings
    print(f"Embedding {len(documents)} entries...")
    embeddings = embedder.encode(documents).tolist()

    # Store in ChromaDB
    collection.add(
        embeddings=embeddings,
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )

    print(f"✅ Indexed {len(documents)} entries into ChromaDB")

if __name__ == "__main__":
    build_index()