FROM ubuntu:20.04
USER root
RUN apt-get update && apt-get install -y --no-install-recommends     curl=7.68.0-1ubuntu2.13     nginx=1.14.0-0ubuntu1.15     && rm -rf /var/lib/apt/lists/*
RUN useradd -m appuser
RUN chown -R appuser:appuser /var/log/nginx /var/lib/nginx /run
USER appuser
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]