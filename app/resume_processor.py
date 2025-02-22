import re
import fitz  # PyMuPDF

def clean_extracted_text(text):
    text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace characters with a single space
    text = text.replace('\n', ' ')     # Replace newlines with spaces
    return text.strip()                 # Remove leading and trailing whitespace

def extract_experience_and_projects_from_pdf(pdf_path):
    resume_text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            resume_text += clean_extracted_text(page.get_text()) + " "  # Clean and add text from each page

    # Define regex patterns to match different section titles
    experience_pattern = r'(?:EXPERIENCE|experience|work experience|employment|professional experience)(.*?)(?=PROJECTS|projects|research projects|academic projects|project work|$)'
    projects_pattern = r'(?:PROJECTS|projects|research projects|academic projects|project work)(.*?)(?=\n\s*\n|\Z)'

    # Find experience section
    experience_match = re.search(experience_pattern, resume_text, re.IGNORECASE | re.DOTALL)
    projects_match = re.search(projects_pattern, resume_text, re.IGNORECASE | re.DOTALL)

    # Extract experience content
    experience = experience_match.group(1).strip() if experience_match else "No experience section found."
    
    # Extract projects content
    projects = projects_match.group(1).strip() if projects_match else "No projects section found."

    return {
        "experience": experience,
        "projects": projects
    }

# Example usage
if __name__ == "__main__":
    pdf_path = "app/uploads/resume/Shivang_-_Resume.pdf" 
    result = extract_experience_and_projects_from_pdf(pdf_path)
    print(result)
