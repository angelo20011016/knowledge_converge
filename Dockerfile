# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
# Upgrade pip and install yt-dlp first, as it changes less often
RUN pip install --no-cache-dir --upgrade pip yt-dlp
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Run app.py when the container launches
# Use the entrypoint script to run migrations and then start the server
CMD ["./entrypoint.sh"]
