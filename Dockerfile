# Use Python 3.11 Alpine as the base image for a minimal footprint
FROM python:3.11-alpine

# Set build-time environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Install system dependencies required for compiling 'lupa' (LuaJIT)
# These are removed after installation to keep the image slim
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    make

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to reduce image size
RUN apk del .build-deps

# Copy the rest of the application code
COPY . .

# Ensure the scripts directory exists (it will be mounted as a volume anyway)
RUN mkdir -p scripts

# Set the entrypoint to run the module
ENTRYPOINT ["python", "-m", "veus"]
