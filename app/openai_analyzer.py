import os
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def embed_function(texts):
    if isinstance(texts, str):
        texts = [texts]
    return embedding_model.embed_documents(texts)

# def split_text(text, max_length=1024):
#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size=max_length,
#         chunk_overlap=100, 
#         separators=["\n\n", "\n", " ", "."]  
#     )
#     chunks = text_splitter.split_text(text)
#     return chunks

# def generate_analysis(prompt): 
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModelForCausalLM.from_pretrained(model_name)
#     inputs = tokenizer(prompt, return_tensors="pt")
#     with torch.no_grad():
#         outputs = model.generate(**inputs, max_length=2000)
#     return tokenizer.decode(outputs[0], skip_special_tokens=True)

def update_faiss_knowledge_base(new_texts):
    global resume_db
    if resume_db is None:
        resume_db = FAISS.from_texts(new_texts, embed_function)
    else:
        resume_db.add_texts(new_texts)

    resume_db.save_local("knowledge_base")


def analyze_resume(text):
    text_embedding = np.array(embed_function(text)).reshape(1, -1)
    
    results = resume_db.similarity_search_by_vector(text_embedding)
    tips = [r.page_content for r in results] if results else []

    retrieved_embeddings = []
    for r in tips:
        emb = embed_function(r)
        retrieved_embeddings.append(np.array(emb).reshape(1, -1))
        
        
    similarities = []
    for emb in retrieved_embeddings:
        if emb.shape == text_embedding.shape:
            similarity = cosine_similarity(text_embedding, emb)[0][0]
            similarities.append(similarity)
            
    avg_similarity = np.mean(similarities) if similarities else 0

    metrics = {
        "similarity_score": round(avg_similarity, 3),
        "resume_strength": "Strong" if avg_similarity > 0.75 else "Moderate" if avg_similarity > 0.5 else "Weak"
    }
    
    suggestions = []
    if avg_similarity < 0.75:
        suggestions.append("Consider adding more industry-specific keywords.")
    if avg_similarity < 0.5:
        suggestions.append("Your resume structure may need improvement. Try a more concise format.")
    if len(text.split()) < 150:
        suggestions.append("Your resume appears too short. Try adding more details on projects or experience.")

    return metrics, suggestions

try:
    resume_db = FAISS.load_local("knowledge_base", embed_function, allow_dangerous_deserialization=True)
except Exception:
    resume_db = FAISS.from_texts([""], embed_function)
    resume_db.save_local("knowledge_base")

