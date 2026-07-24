# This line tells Docker which base image to start from for the container. it Use an official Python runtime environment as a parent image
#as all the codes in app.py are written in python and hence we need to run them in a python environment
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Define environment variable
ENV NAME World

# Run gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:app"]
# Format for CMD is "gunicorn [options] [module_name]:[app_instance_name]"