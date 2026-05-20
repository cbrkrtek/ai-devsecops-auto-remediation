FROM ubuntu:20.04

# Update package list and install necessary packages without recommendations
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl \
        nginx \
        && rm -rf /var/lib/apt/lists/*

# Set a non-root user to run the container
USER appuser

# Expose the required port
EXPOSE 80

# Define the command to start Nginx in the background
CMD ["nginx", "-g", "daemon off;"]