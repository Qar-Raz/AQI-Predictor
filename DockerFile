# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /code

# Copy the requirements file into the container at /code
COPY ./requirements.txt /code/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the rest of your application code into the container
# This copies your api/, models/, data/, etc. folders
COPY . /code/

# Tell the port number your container will listen on
EXPOSE 7860

# Command to run your application
# Note: We use port 7860 as it's standard for Hugging Face Spaces
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "7860"]