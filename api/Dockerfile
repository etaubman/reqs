FROM python:3.10-slim
WORKDIR /app
# Copy dependencies file and install them
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Copy application code
COPY . /app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
