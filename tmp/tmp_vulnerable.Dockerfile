FROM ubuntu:20.04
RUN apt-get update && apt-get install -y --no-install-recommends curl nginx=1.18.0-0ubuntu1.16 && rm -rf /var/lib/apt/lists/*
RUN useradd appuser && chown -R appuser:appuser /app
USER appuser
WORKDIR /app
COPY . /app
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]