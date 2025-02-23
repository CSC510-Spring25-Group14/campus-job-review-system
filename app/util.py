"""
  This file contains utility functions that can be reused.
"""
from app.models import JobExperience

def extract_experience_summary(applicant):
  """
    Given an applicant, this function returns a dictionary summarizing the applicant's profile.
  """
  # Retrieve all the experiences of the applicant
  experiences = JobExperience.query.filter_by(username=applicant.username).all()

  # Convert all those experiences as dictionaries
  experience_list = [exp.to_dict() for exp in experiences]

  # One dict which combines all the experiences of an applicant.
  experience_summary = {}

  # Combine all experiences into experience_summary
  for d in experience_list:
    for key, value in d.items():
      if key == "id":
        continue
      if key in experience_summary:
        if key in ['username']:
          continue
        elif isinstance(experience_summary[key], list):
          experience_summary[key].append(value)
        else:
          experience_summary[key] = [experience_summary[key], value]  # Convert to list if first encounter
      else:
        if key in ['username'] or type(value) is list:
          experience_summary[key] = value
        else:
          experience_summary[key] = [value]
  
  return experience_summary

def call_groq_api(template_path, input_data):
  """
    Given a prompt template, the function returns the output from GROQ AI
  """
  with open(template_path, "r") as pt:
    prompt_temp = pt.read()
  
  from groq import Groq
  import os

  client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
  completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
      {
        "role": "user",
        "content": prompt_temp
      },
      {
        "role": "user",
        "content": input_data
      }
    ],
    temperature=0.4,
    max_completion_tokens=1024,
    top_p=1,
    stream=False,
    stop=None
  )

  return completion.choices[0].message.content
