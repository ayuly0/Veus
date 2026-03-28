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

RUN addgroup -S veus-group && adduser -S veus-ops -G veus-group && \
    mkdir -p scripts downloads && \
    chown -R veus-ops:veus-group /app

# Switch to non-root user
USER veus-ops

# Set the entrypoint to run the module
ENTRYPOINT ["python", "-m", "veus"]
