# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN pip install pytest coverage

# Copy the rest of the application code to /app
COPY . /app

# Set environment variables
ENV FLASK_APP=crudapp.py
ENV FLASK_ENV=development
ENV GROQ_API_KEY=<YOUR-GROQ-API-KEY-HERE>

# Initialize the database
RUN flask db init || true
RUN flask db migrate -m "entries table" || true
RUN flask db upgrade || true

# Expose port 5000
EXPOSE 5000

# Run the application
CMD ["flask", "run", "--host=0.0.0.0"]