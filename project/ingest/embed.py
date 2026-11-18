# This script takes each chunk from chunks.json and calls Gemini's embedding API to convert it into vectors.
# This should only be done once and stored in the repo since our deployment PaaS doesn't give us a whole lot of JUICE to do this at runtime
# Then, at runtime, our script should use the same embeddings model to embed the user's question and find the answer through the rules embeddings.
# Ideally this will be both faster than the Ollama model and very lightweight since the actual LLM is being called via Google's API

from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from pathlib import Path
import json
import time
import numpy as np

load_dotenv()

EMBEDDING_MODEL = "gemini-embedding-001"
DIMS = 768
BATCH = 25
PAUSE = 4
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHUNKS_PATH = Path(__file__).resolve().parent.parent / "ingest" / "chunks.json"
OUT_DIR = CHUNKS_PATH.parent
PARTIAL = OUT_DIR / "embeddings_partial.npy"

def prepare_document(heading, body):
    return f"{heading}\n\n{body}"

def load_chunks():
    # Open the file in read mode ('r')
    with open(CHUNKS_PATH, 'r', encoding="utf-8") as file:
        data = json.load(file)
    return data

def embed_batch(client, batch):
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=batch,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=DIMS,
        ),
    )
    return [e.values for e in result.embeddings]

def with_retry(fn, *args, tries=6):
    for attempt in range(tries):
        try:
            return fn(*args)
        except Exception as e:
            if "PerDay" in str(e) or attempt == tries - 1:
                raise
            wait = 20 * (attempt + 1)
            print(f"Error: {e}\nRetrying in {wait}s...")
            time.sleep(wait)

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Unable to embed chunks. Gemini API key not provided.")
        exit(1)

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Load chunks from JSON
    chunks = load_chunks()

    # Prepare each chunk into a string to be sent to Gemini API
    texts = [prepare_document(chunk["heading"], chunk["body"]) for chunk in chunks]
    vectors = list(np.load(PARTIAL)) if PARTIAL.exists() else []
    print(f"Resuming from chunk {len(vectors)} of {len(texts)}")

    for i in range(len(vectors), len(texts), BATCH):
        batch = texts[i:i + BATCH]
        vectors.extend(with_retry(embed_batch, client, batch))
        np.save(PARTIAL, np.array(vectors, dtype="float32"))
        time.sleep(PAUSE)

    assert len(vectors) == len(chunks)

    arr = np.array(vectors, dtype="float32")
    arr /= np.linalg.norm(arr, axis=1, keepdims=True)

    print(arr.shape)

    np.save(CHUNKS_PATH.parent / "embeddings.npy", arr)