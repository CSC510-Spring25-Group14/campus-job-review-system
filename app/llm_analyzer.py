import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('API_KEY')
model_id = "meta-llama/Llama-3.2-3B-Instruct"

def analyze_resume(resume_text):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    
    prompt = (
        f"This is my resume content: {resume_text}. Suggest me where I can improve."
    )
    
    payload = {
        "inputs": prompt,
        "options": {
            "use_cache": False,
            "max_new_tokens": 256
        }
    }
    
    response = requests.post(f"https://api-inference.huggingface.co/models/{model_id}", headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        return f"Error: {response.status_code} - {response.text}"


# resume_text = """
# John Doe
# Education: B.S. in Computer Science from XYZ University, 2020.
# Experience: Software Engineer at ABC Corp (2020 - 2022).
# Projects: Developed a web application for task management.
# Publications: Author of 'AI in Practice'.
# Awards: Employee of the Month at ABC Corp, 2021.
# """

# result = analyze_resume(resume_text)
# print(result)
