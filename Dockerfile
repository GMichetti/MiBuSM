# Use a base Ubuntu image (Jammy)
FROM ubuntu:22.04

# Set the variable to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install the necessary dependencies, including supervisor and cron
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip \
    supervisor \
    cron \
    udev \
    usbutils \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /env
ENV PATH="/env/bin:$PATH"

# Copy your scripts and configuration files into the container
COPY /app/ /app/
RUN /env/bin/pip install -r /app/requirements.txt

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Adding folder for logs
RUN mkdir -p /var/log/mibu

# # Create the udev rules file with the provided idVendor and idProduct
# RUN echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="'MY_ID_VENDOR'", ATTRS{idProduct}=="'MY_ID_PRODUCT'", GROUP="users", MODE="0666"' > /etc/udev/rules.d/cp.rules

# # Create the module load configuration file
# RUN echo 'usbhi' > /etc/modules-load.d/00-my-usbhid.conf

# Create the cron job configuration file. This job will run every 72 hours to delete .zip files in /var/log/mibu
RUN echo "0 */72 * * * find /var/log/mibu -type f -name \"*.zip\" -delete" > /etc/cron.d/mibu-cleanup
RUN chmod 0644 /etc/cron.d/mibu-cleanup

# Set the working directory
WORKDIR /app

# Start supervisor and cron in the foreground
CMD ["sh", "-c", "cron && /usr/bin/supervisord -c /etc/supervisor/supervisord.conf"]

# Expose port 8000 internally to Docker
EXPOSE 8000
