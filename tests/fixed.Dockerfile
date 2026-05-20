# Step 1: Update package lists
RUN apt-get update

# Step 2: Install necessary packages
RUN apt-get install -y --no-install-recommends \
    curl \
    nginx

# Step 3: Remove unused package lists
RUN rm -rf /var/lib/apt/lists/*

# Step 4: Create a non-root user and switch to it
RUN useradd -u 10011 appuser && chown -R appuser:appuser /usr/share/nginx/html /etc/nginx /var/www/html

# Step 5: Install system packages under the new user
USER appuser
RUN apt-get install -y \
    curl \
    nginx

# Step 6: Configure Nginx and start it
CMD ["nginx", "-g", "daemon off;"]