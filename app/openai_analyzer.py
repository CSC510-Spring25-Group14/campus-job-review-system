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

embed_function = SentenceTransformer("all-MiniLM-L6-v2")
tokenizer = embed_function.tokenizer 
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({'pad_token': '[PAD]'})

def split_text(text, max_length=1024):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_length,
        chunk_overlap=100, 
        separators=["\n\n", "\n", " ", "."]  
    )
    chunks = text_splitter.split_text(text)
    return chunks

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
    tips = []
    if resume_db:
        results = resume_db.similarity_search(text, k=3) 
        tips = [r.page_content if hasattr(r, 'page_content') else str(r) for r in results]

    text_embedding = embed_function.encode([text], convert_to_numpy=True)[0]

    retrieved_embeddings = [embed_function.encode(r, convert_to_numpy=True) for r in tips]

    similarities = [cosine_similarity([text_embedding], [emb])[0][0] for emb in retrieved_embeddings]

    avg_similarity = np.mean(similarities) if similarities else 0  # Average similarity score
    metrics = {
        "similarity_score": round(avg_similarity, 3),  # How close the resume is to top resumes
        "resume_strength": "Strong" if avg_similarity > 0.75 else "Moderate" if avg_similarity > 0.5 else "Weak"
    }

    # Generate suggestions based on differences with top resumes
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
except Exception as e:
    resume_db = None

    resume_db = FAISS.from_texts([""], embed_function)
    resume_db.save_local("knowledge_base")
