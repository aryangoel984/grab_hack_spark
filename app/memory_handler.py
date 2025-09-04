# app/memory_handler.py
import os
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import uuid
from dotenv import load_dotenv

load_dotenv()

# NEW INITIALIZATION SYNTAX
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

# YOU DO NOT NEED THE HOST PARAMETER. 
# The new SDK finds the correct host for you automatically.
index = pc.Index("synapse-rag-memory")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def update_rag_memory(resolved_plan: str, disruption_scenario: str):
    """Summarizes, embeds, and stores a successful workflow in Pinecone."""
    memory_id = str(uuid.uuid4())
    memory_summary = f"For the problem '{disruption_scenario}', the successful plan was: {resolved_plan}"
    print(f"--- 🧠 Adding to memory: {memory_summary} ---")
    memory_embedding = embeddings.embed_query(memory_summary)
    index.upsert(vectors=[{
        "id": memory_id,
        "values": memory_embedding,
        "metadata": {"summary": memory_summary}
    }])
    print("--- ✅ Memory updated. ---")

def retrieve_rag_memories(disruption_scenario: str) -> str:
    """Queries Pinecone to find the most similar past cases."""
    print("--- 🧠 Searching memory... ---")
    query_embedding = embeddings.embed_query(disruption_scenario)
    results = index.query(vector=query_embedding, top_k=3, include_metadata=True)
    if not results['matches']:
        return "No relevant memories found."
    memories = "\n".join([res['metadata']['summary'] for res in results['matches']])
    return memories