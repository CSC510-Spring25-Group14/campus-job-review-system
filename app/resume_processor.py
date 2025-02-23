import re
import fitz  # PyMuPDF

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

# Example usage
if __name__ == "__main__":
    pdf_path = "app/uploads/resume/Shivang_-_Resume.pdf" 
    result = extract_experience_and_projects_from_pdf(pdf_path)
    print(result)
