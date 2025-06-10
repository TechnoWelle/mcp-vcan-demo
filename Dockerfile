FROM ubuntu:22.04

LABEL maintainer=""
LABEL description="Dockerfile for MCP Demo with vCAN and ECUs simulation"
LABEL version="1.0"
USER root
# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-can \
    python3-venv \
    iproute2 \
    can-utils \
    sudo \
    kmod \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /home/pi/MCP-Demo

# Set working directory
WORKDIR /home/pi/MCP-Demo

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip3 install --no-cache-dir cantools
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose MCP and other relevant ports
EXPOSE 6278 80 443 5000 8080

# Entrypoint: Run vCAN setup, then run MCP and simulation scripts concurrently
CMD ["bash", "-c", "./setup-vcan.sh && python3 can-mcp.py & python3 simulate-ecus.py && wait"]