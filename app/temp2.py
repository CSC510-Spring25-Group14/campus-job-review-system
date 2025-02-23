import os
import re
import fitz
from dotenv import load_dotenv
import google.generativeai as genai
import json

load_dotenv()

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

def clean_extracted_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\n', ' ')
    return text.strip()

def extract_projects_and_experience_from_pdf(pdf_path):
    resume_text = ""
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            resume_text += clean_extracted_text(page.get_text()) + " "
    return get_json_from_gemini(resume_text)

def get_json_from_gemini(resume_text):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    Given the following resume text, extract the experience and projects sections and format them as a JSON object.

    Resume Text:
    {resume_text}

    JSON Format:
    {{
        "experience": [
            {{
                "title": "...",
                "duration": "...",
                "description": "..."
            }},
            // ... more experience entries
        ],
        "projects": [
            {{
                "title": "...",
                "duration": "...",
                "description": "..."
            }},
            // ... more project entries
        ]
    }}

    Return ONLY the JSON object.
    """

    try:
        response = model.generate_content(prompt)
        json_string = response.text.strip()

        # Attempt to find JSON within the string
        try:
            start_index = json_string.find('{')
            end_index = json_string.rfind('}') + 1
            json_string = json_string[start_index:end_index]
            return json.loads(json_string)
        except:
            print("Could not isolate JSON from response")
            return None

    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return None

if __name__ == "__main__":
    pdf_path = "app/uploads/resume/Shivang_-_Resume.pdf"
    result = extract_projects_and_experience_from_pdf(pdf_path)
    if result:
        print(json.dumps(result, indent=4))
    else:
        print("Failed to extract JSON data.")