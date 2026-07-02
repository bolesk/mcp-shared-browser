FROM mcr.microsoft.com/playwright/python:v1.60.0-jammy


# Install Xvfb and other required libraries
RUN apt-get update && apt-get install -y \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project dependency definitions
COPY pyproject.toml uv.lock* /app/

# Install dependencies (will use pre-installed browsers in the base image)
RUN uv sync --no-cache

# Copy project source code
COPY ports/ /app/ports/
COPY adapters/ /app/adapters/
COPY delivery/ /app/delivery/
COPY tests/ /app/tests/
COPY main.py /app/

# Set env so Playwright uses the system-installed browsers from the base image
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Python manages Xvfb lifecycle via pyvirtualdisplay
CMD ["uv", "run", "pytest", "-v"]

