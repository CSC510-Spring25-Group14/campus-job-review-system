import pdfplumber
import re

def text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                page_text = re.sub(r'([a-z])([A-Z])', r'\1 \2', page_text)  
                page_text = re.sub(r'(?<!\s)(?=[,.])', ' ', page_text) 
                text += page_text + "\n"
    return text.strip()
