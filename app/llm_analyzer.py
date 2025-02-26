import os
import re
import fitz
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def clean_extracted_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    return text.strip()

def extract_experience_and_projects_from_pdf(pdf_path):
    resume_text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            resume_text += clean_extracted_text(page.get_text()) + " "

    experience_pattern = r'(?:EXPERIENCE|experience|work experience|employment|professional experience)(.*?)(?=PROJECTS|projects|research projects|academic projects|project work|$)'
    projects_pattern = r'(?:PROJECTS|projects|research projects|academic projects|project work)(.*?)(?=\n\s*\n|\Z)'

    experience_match = re.search(experience_pattern, resume_text, re.IGNORECASE | re.DOTALL)
    projects_match = re.search(projects_pattern, resume_text, re.IGNORECASE | re.DOTALL)

    experience_section = experience_match.group(1).strip() if experience_match else "No experience section found."
    experiences = [exp.strip() for exp in experience_section.split("•") if exp.strip()]

    projects_section = projects_match.group(1).strip() if projects_match else "No projects section found."
    project_entries = [proj.strip() for proj in projects_section.split("•") if proj.strip()]

    projects = []
    current_project = ""
    for entry in project_entries:
        if re.match(r'^[A-Z].*', entry):
            if current_project:
                projects.append(current_project.strip())
            current_project = entry
        else:
            current_project += " " + entry

    if current_project:
        projects.append(current_project.strip())

    return {
        "experience": experiences,
        "projects": projects
    }

def analyze_resume(resume_text):
    model = genai.GenerativeModel('gemini-1.5-pro')
    prompt = (
        f"This is my projects and experience section from resume: {resume_text}. Suggest me where I can improve."
    )

    try:
        response = model.generate_content(prompt)
        text = response.text

        # Clean up the text:
        text = re.sub(r'\*+', '', text)  # Remove asterisks
        text = re.sub(r'WARNING:.*', '', text, flags=re.DOTALL) # Remove warnings
        text = text.strip()  # Remove leading/trailing whitespace

        return text
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return None

def process_resume(pdf_path):
    extracted_data = extract_experience_and_projects_from_pdf(pdf_path)

    resume_text = f"Experience: {', '.join(extracted_data['experience'])}\n\nProjects: {', '.join(extracted_data['projects'])}"
    suggestions = analyze_resume(resume_text)

    return {
        "extracted_data": extracted_data,
        "suggestions": suggestions
    }

if __name__ == "__main__":
    pdf_path = "app/uploads/resume/Shivang_-_Resume.pdf"
    result = process_resume(pdf_path)
    print("Extracted Data:", result['extracted_data'])
    print("Suggestions:", result['suggestions'])