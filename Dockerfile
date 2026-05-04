FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY app /workspace/app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
       fastapi==0.136.1 \
       uvicorn==0.46.0 \
       python-multipart==0.0.27 \
       requests \
       pandas \
       parse

COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh \
    && mkdir -p /workspace/app/.local/pregrade

EXPOSE 5000

CMD ["/workspace/start.sh"]
