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
        f"This is my projects and experience section from resume: {resume_text}. Suggest me where I can improve."
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
        generated_text = response.json()[0]['generated_text']
        cleaned_response = generated_text.replace(prompt, "").strip()
        return cleaned_response
    else:
        return f"Error: {response.status_code} - {response.text}"
    
my_dict = {'experience': 'Software Development Intern | D360 Technologies Inc Jan. 2024 – May 2024 • Engineered an interactive frontend Dashboard Viewer that enabled clients to eﬀortlessly access diamond analytics, leading to a more streamlined data manipulation and enhanced user satisfaction across 50+ client accounts • Implemented advanced client veriﬁcation processes leading to a secure environment; reduced potential data breaches by 30%, enhanc- ing trust among certiﬁed clients while safeguarding sensitive diamond analytics • Designed and enforced client-speciﬁc data privacy controls, delivering tailored data views that met individual client needs while safe- guarding conﬁdential information Software Development Intern | D360 Technologies Inc June. 2023 – July 2023 • Formulated an eﬃcient search query feature that fetched detailed diamond information from a repository of over 1.1 million records, enabling fast and accurate data retrieval based on user input • Integrated Google Authentication to ensure secure access, restricting data usage exclusively to authenticated users and safeguarding sensitive diamond information • Optimized the search functionality to improve query performance, enhancing user experience and enabling seamless navigation through an extensive diamond database', 'projects': 'Automated Insulin Delivery using Deep Learning Techniques July 2023 - Dec 2023 • Created a robust predictive model using Bi-Directional LSTM to forecast blood glucose levels at precise intervals (5, 10, 15, 25, and 30 minutes) for Type-1 diabetes patients, achieving exceptional accuracy and performance • Leveraged two months of continuous glucose monitoring data from 12 Type-1 diabetes patients, sourced from Ohio State University, to signiﬁcantly enhance model precision by 20 • Provided actionable insights by optimizing the model for use in automated insulin delivery systems, contributing to potential advance- ments in diabetes management technology Malicious URL Detection Using Natural Language Processing and Deep Learning Jan 2023 - April 2023 • Developed a machine learning-based URL classiﬁcation system utilizing Support Vector Machines (SVM) and Artiﬁcial Neural Networks (ANN), achieving 95% accuracy in detecting phishing, malware, and spam-related URLs from a dataset of 6,000 URLs with over 80 features • Engineered a feature extraction pipeline incorporating NLP techniques, such as GloVe embeddings, and optimized feature selection using Principal Component Analysis (PCA) to enhance model eﬃciency and reduce computation time while maintaining classiﬁcation accuracy • Implemented a blockchain-based security layer for decentralized storage of detected malicious URLs, enabling tamper-proof logging and real-time threat intelligence sharing through smart contracts, enhancing security in web environments DNA Methylation Prediction in DNA sequence using CNN Aug 2022 – Nov 2022 • Structured a Convolutional Neural Network (CNN) with dropout to detect DNA methylation, optimizing the model to process 2000- character long DNA sequences eﬃciently • Achieved 93% accuracy by converting DNA sequences into matrices for training, signiﬁcantly reducing model training time and enhancing predictive performance PUBLICATIONS CONFERENCE PROCEEDINGS WITH JOURNAL PUBLICATION • Yogi Patel, Shivang Patel, Rajesh Gupta, Mohammad S. Obaidat, Riya Kakkar, Nilesh Kumar Jadav, Sudeep Tanwar, "Blockchain and AI-based Engine Fault Detection Scheme for Autonomous Vehicles" AWARDS Secured First Place in the MINeD Hackathon, jointly organized by Nirma University and the State University of New York, Binghamton. Developed an innovative solution for querying diamond inventory through chatbots, a project provided by D360 Technologies Inc.'}
resume_text = "Experience: " + my_dict["experience"] + "\n\nProjects: " + my_dict["projects"]

response = analyze_resume(resume_text)
print(response)
