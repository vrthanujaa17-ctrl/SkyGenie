import os
import fitz  # PyMuPDF
import chromadb
from PIL import Image
from google import genai
from langchain_huggingface import HuggingFaceEmbeddings


GEMINI_API_KEY = "AIzaSyDzFepnVv0n1kJhcKCOTNke2BKPBvvyDHg"
client = genai.Client(api_key=GEMINI_API_KEY)

EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"
GENERATION_MODEL = "gemini-2.5-flash-lite"
VECTOR_DB_NAME = "multimodal_collection"

# Initialize HuggingFace embeddings
hf_embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={"device": "cpu"},  # Change to "cuda" if you have a GPU
    encode_kwargs={"normalize_embeddings": True},
)


class LangChainEmbeddingAdapter:
    def name(self):
        return "hf_bge_adapter"

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]
        return hf_embeddings.embed_documents(input)

    def embed_query(self, input):
        if isinstance(input, list):
            return hf_embeddings.embed_documents(input)
        return [hf_embeddings.embed_query(input)]


def extract_pdf_contents(pdf_path, output_image_dir="extracted_images"):
    """Extract text chunks and images from a PDF."""
    if not os.path.exists(output_image_dir):
        os.makedirs(output_image_dir)

    doc = fitz.open(pdf_path)
    text_chunks = []
    image_paths = []

    print(f"Extracting contents from {pdf_path}...")

    for page_num in range(len(doc)):
        page = doc[page_num]

        # Extract text
        text = page.get_text()
        if text.strip():
            text_chunks.append(
                {
                    "content": text,
                    "metadata": {
                        "source": pdf_path,
                        "page": page_num,
                        "type": "text",
                    },
                }
            )

        # Extract images
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_filename = f"page_{page_num}_img_{img_index}.{image_ext}"
            image_filepath = os.path.join(output_image_dir, image_filename)

            with open(image_filepath, "wb") as f:
                f.write(image_bytes)

            image_paths.append(
                {
                    "path": image_filepath,
                    "metadata": {
                        "source": pdf_path,
                        "page": page_num,
                        "type": "image",
                    },
                }
            )

    print(f"Extracted {len(text_chunks)} text chunks and {len(image_paths)} images.")
    return text_chunks, image_paths


def summarize_image(image_path):
    """Use Gemini to generate a description of an image."""
    img = Image.open(image_path)
    prompt = (
        "Describe this image in detail. Focus on information that would be useful "
        "for answering questions about it."
    )

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=[img, prompt],
    )
    return response.text


def build_vector_database(text_chunks, image_data):
    """Embed text and image summaries, then store them in ChromaDB."""
    chroma_client = chromadb.EphemeralClient()

    try:
        chroma_client.delete_collection(name=VECTOR_DB_NAME)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=VECTOR_DB_NAME,
        embedding_function=LangChainEmbeddingAdapter(),
    )

    docs = []
    metadatas = []
    ids = []

    print("Preparing text chunks...")
    for i, chunk in enumerate(text_chunks):
        docs.append(chunk["content"])
        metadatas.append(chunk["metadata"])
        ids.append(f"text_{i}")

    print("Summarizing and preparing images...")
    for i, img_info in enumerate(image_data):
        img_path = img_info["path"]
        try:
            summary = summarize_image(img_path)
            meta = img_info["metadata"].copy()
            meta["image_path"] = img_path

            docs.append(summary)
            metadatas.append(meta)
            ids.append(f"image_{i}")
        except Exception as e:
            print(f"Skipping image {img_path} due to error: {e}")

    if not docs:
        print("No documents found to index.")
        return collection

    print(f"Embedding and storing in ChromaDB using {EMBEDDING_MODEL_NAME}...")
    collection.add(
        documents=docs,
        metadatas=metadatas,
        ids=ids,
    )

    return collection


def ask_question(query, collection, top_k=3):
    """Retrieve relevant context and answer the query using Gemini."""
    print(f"\n[User Query]: {query}")

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
    )

    retrieved_docs = results["documents"][0]
    retrieved_metadatas = results["metadatas"][0]

    prompt_contents = [
        "You are an expert travel bot. Answer the question based on the provided text and images.",
        f"Question: {query}",
        "--- Context ---",
    ]

    for i, (doc_text, meta) in enumerate(zip(retrieved_docs, retrieved_metadatas)):
        if meta["type"] == "text":
            prompt_contents.append(f"[Text Context {i + 1}]:\n{doc_text}")
        elif meta["type"] == "image":
            prompt_contents.append(f"[Image Context {i + 1} Description]:\n{doc_text}")
            img_path = meta.get("image_path")
            if img_path and os.path.exists(img_path):
                try:
                    img_obj = Image.open(img_path)
                    prompt_contents.append(img_obj)
                except Exception:
                    pass

    print("Generating answer via Gemini...")
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt_contents,
    )

    print("\n--- Answer ---")
    print(response.text)
    print("--------------")


if __name__ == "__main__":
    TARGET_PDF = "sample_document.pdf"

    if not os.path.exists(TARGET_PDF):
        print(f"Error: '{TARGET_PDF}' not found.")
    else:
        texts, images = extract_pdf_contents(TARGET_PDF)
        vector_db = build_vector_database(texts, images)

        while True:
            user_input = input("\nEnter question (or 'quit'): ")
            if user_input.lower() in ["quit", "exit", "q"]:
                break
            ask_question(user_input, vector_db)