__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, SIMILARITY_THRESHOLD, MAX_EXAMPLES

# Initialise embedding model and ChromaDB
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="examples")

def add_example(message: str, label: str) -> None:
  """
  Converts an example message into an embedding and stores it in ChromaDB.

  Args:
    message: The example text
    label: "SAFE" or "BAN"
  """
  embedding = embedding_model.encode(message).tolist()
  collection.add(
    embeddings = [embedding],
    documents = [message],
    metadatas=[{"label": label}],
    ids=[str(hash(message))]
  )

def get_similar_examples(message:str) -> str:
  """
  Retrieves most similar examples from ChromaDB for a given input.

  Args:
    message: Incoming Telegram message

  Returns:
    A formatted string of similar examples to inject into the prompt, or empty string if no relevant examples found.
  """
  if collection.count() == 0:
    return ""
  embedding = embedding_model.encode(message).tolist()
  results = collection.query(
    query_embeddings=[embedding],
    n_results=min(MAX_EXAMPLES, collection.count())
  )
  examples = []
  for doc, metadata, distance in zip(
    results["documents"][0],
    results["metadatas"][0],
    results["distances"][0]
  ):
    if distance < SIMILARITY_THRESHOLD:
      examples.append(f"Message: {doc}\nClassification: {metadata['label']}")

  if not examples:
    return ""
  return "\n\n".join(examples)