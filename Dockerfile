FROM python:3.11

# Set environment variables to reduce Python buffering and enable Docker build caching
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Update apt-get and install dependencies for building certain Python packages like pocketsphinx and PyAudio
RUN apt-get update && apt-get install -y \
    libasound2-dev \ 
    libpulse-dev \ 
    swig \
    build-essential \ 
    libssl-dev \ 
    libffi-dev \ 
    python3-dev \ 
    portaudio19-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the Python dependencies file to the container
COPY requirements.txt .

# Install python dependencies
RUN pip install -r requirements.txt

COPY src/ .

EXPOSE 8000

# Define the command to run your application
# Assuming 'main.py' is your entrypoint script
CMD ["python", "./main.py"]
