# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install poetry
RUN pip install poetry

# Install dependencies
RUN poetry install

# Expose the port the app runs on
EXPOSE 80

# Run the application
CMD ["poetry", "run", "services"]
