import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModel
import torch
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()
model_name = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model_final = AutoModel.from_pretrained(model_name)

def get_embeddings(texts):
    if not texts:  
        raise ValueError("Input texts must not be empty.")
    
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        embeddings = model_final(**inputs).last_hidden_state
        embeddings = embeddings.mean(dim=1)  
    return embeddings

tips = [
    "Use strong action verbs like 'spearheaded', 'optimized', and 'orchestrated'",
    "Always quantify achievements (e.g., 'Increased efficiency by 25%')",
    "Avoid generic soft skills—show impact with examples.",
    "Include relevant keywords from job descriptions.",
    "Use STAR format for structuring experiences."
]

embeddings = get_embeddings(tips)
embed_np = embeddings.detach().cpu().numpy()  

text_embeddings = list(zip(tips, embed_np))

resume_db = FAISS.from_embeddings(embedding=embed_np, text_embeddings=text_embeddings)
resume_db.save_local("knowledge_base")
