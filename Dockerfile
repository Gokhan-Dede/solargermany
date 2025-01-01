# Use the official Python image as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire app to the container
COPY . .

# Expose the port Streamlit runs on
ENV PORT=8080

# Run the Streamlit app
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0
