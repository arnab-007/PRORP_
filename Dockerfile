# ==========================================================
# Dockerfile for TACAS Artifact: PRORP
# ==========================================================

# 1. Base image
FROM python:3.11-slim

# 2. Metadata
LABEL title="PRORP Artifact"
LABEL version="1.0"

# 3. Set working directory inside the image
WORKDIR /app

# 4. Copy only the PRORP directory (not everything)
COPY PRORP /app/PRORP

# 5. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    wget \
    unzip \
    build-essential \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
    && rm -rf /var/lib/apt/lists/*

# 6. Download and install SAT tools
RUN wget https://github.com/msoos/cryptominisat/releases/download/release/5.13.0/cryptominisat5-linux-amd64.zip -O cryptominisat5.zip \
 && wget https://github.com/meelgroup/cmsgen/releases/download/release/6.1.1/cmsgen-linux-amd64.zip -O cmsgen.zip \
 && unzip cmsgen.zip \
 && unzip cryptominisat5.zip \
 && mv cmsgen /usr/local/bin/ \
 && mv cryptominisat5 /usr/local/bin/ \
 && chmod +x /usr/local/bin/cmsgen /usr/local/bin/cryptominisat5

# 7. Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# 8. Install Python dependencies
RUN pip install --no-cache-dir -r /app/PRORP/requirements.txt

# 9. Make run.sh executable (if it's inside PRORP)
RUN chmod +x /app/PRORP/run.sh

# 10. Default command
# CMD ["bash", "/app/PRORP/run.sh"]
