import pdfplumber

def text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def resume_content(path):
    if path.endswith('.pdf'):
        return text_from_pdf(path)
    

