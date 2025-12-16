# InsuranceAI Toolkit - Streamlit Web UI
# Dockerfile for containerized Guardian demo

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for pdf2image, if needed)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies with web extras (Streamlit + Plotly)
RUN pip install --no-cache-dir -e ".[web]"

# Expose Streamlit port
EXPOSE 8501

# Streamlit configuration
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_LOGGER_LEVEL=info

# Run Streamlit app
CMD ["streamlit", "run", "src/insurance_ai/web/app.py"]
