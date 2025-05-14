FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --timeout=100 -r requirements.txt

COPY . .

CMD ["python3", "./main.py"]
