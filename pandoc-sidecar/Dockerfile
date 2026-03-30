FROM python:3.12-alpine
RUN apk add --no-cache pandoc
COPY server.py nobreak.html break.html compact.html callouts.lua copycode.html /app/
WORKDIR /app
CMD ["python3", "/app/server.py"]
