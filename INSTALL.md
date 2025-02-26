# Installation Guide

Follow the steps below to set up the Campus Job Review System. You can choose to install using Docker or without Docker.

---

## Table of Contents
- [Setup Groq API Key](#setup-groq-api-key)
- [Installation with Docker](#installation-with-docker)
   - [Docker Prerequisites](#docker-prerequisites)
   - [Docker Installation Steps](#docker-project-setup)
- [Installation without Docker](#installation-without-docker)
   - [Prerequisites](#prerequisites)
      - [For Windows](#for-windows)
      - [For Mac OS](#for-mac-os)
   - [Project Setup](#project-setup)
   - [Database Maintenance](#database-maintenance)

---

## Setup Groq API Key
- Obtain an Groq API Key from [here](https://console.groq.com/docs/quickstart). Store the key safely as it cannot be retrieved later.

## Setup Google Gemini API Key
- Obtain Google Gemini AI model API key from [Google AI Studio](https://aistudio.google.com/prompts/new_chat).

## Installation with Docker

### Docker Prerequisites
1. **Install Docker:**
   - [Get Docker for Windows/Mac/Linux](https://docs.docker.com/get-docker/).
   - Follow the instructions on Docker’s website to install Docker Desktop on your system.
   - After installation, verify by running:
     ```bash
     docker --version
     ```

### Docker Project Setup
1. **Clone the Project:**
   ```bash
   git clone https://github.com/CSC510-Spring25-Group14/campus-job-review-system.git
   ```
2. **Navigate to the Project Directory:**
   ```bash
   cd campus-job-review-system
   ```
3. **Obtain Groq API Key:**

   Update the following line in [Dockerfile](Dockerfile) with your Groq API key.
   ```
   ENV GROQ_API_KEY=<YOUR-GROQ-API-KEY-HERE>
   ```

4. **Run the Deployment Script:**
   #### For Mac OS
   ```bash
   bash deploy.sh
   ```

   #### For Windows
   ```bash
   sh deploy.sh
   ```
   This script will build and run the Docker container.

5. **Access the Application:**
   Once the container is running, you should be able to access the application locally at `http://localhost:3000`.

---

## Installation without Docker

### Prerequisites

1. **Installing Python:**

    #### For Windows
    
    1. Download the Python installer from [Python Downloads](https://www.python.org/downloads/).
    2. Run the installer and follow the prompts. Ensure you add Python to your environment variables.
    3. Verify the installation:
       ```bash
       python --version
       ```
    
    #### For Mac OS
    
    1. Install [Homebrew](https://brew.sh/) (if not already installed):
       ```bash
       /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
       ```
    2. Use Homebrew to install Python:
       ```bash
       brew install python
       ```
    3. Verify the installation:
       ```bash
       python --version
       ```

### Project Setup
1. **Set Environment Variable:**
   
   Add the Groq API key we obtained earlier as an environment variable with name ```GROQ_API_KEY``` in the system.

2. **Clone the Project:**
   ```bash
   git clone https://github.com/CSC510-Spring25-Group14/campus-job-review-system.git
   ```
3. **Navigate to the Project Directory:**
   ```bash
   cd campus-job-review-system/
   ```
4. **Set Up a Virtual Environment:**
   ```bash
   python -m venv venv
   ```
5. **Activate the Virtual Environment:**
    - On Windows:
      ```bash
      .\venv\Scripts\activate
      ```
    - On Mac OS/Linux:
      ```bash
      source venv/bin/activate

      ```
6. **Install Dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
7. **Database Setup:**
    - Initialize the database:
      ```bash
      flask db init
      ```
    - Apply migrations:
      ```bash
      flask db migrate -m "Initial migration"
      flask db upgrade
      ```
8. **Run the Application:**
   ```bash
   flask run
   ```
   The application will start on `http://localhost:5000`.

### Database Maintenance

To create new tables, run:
```bash
flask shell
from app import db
db.create_all()
```

To delete all tables:
```bash
flask shell
from app import db
db.drop_all()
```
