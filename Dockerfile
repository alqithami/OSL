FROM python:3.11-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
# Ensure matplotlib works headless
ENV MPLBACKEND=Agg

WORKDIR /app

# Install system deps (optional; wheels usually suffice, but keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
  && rm -rf /var/lib/apt/lists/*

# Copy dependency descriptors first (better Docker layer caching)
COPY requirements.txt requirements-dev.txt pyproject.toml setup.py README.md LICENSE ./

# Install dependencies
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt && \
    pip install --no-cache-dir -e .

# Copy source code and experiments/tests
COPY src/ src/
COPY experiments/ experiments/
COPY tests/ tests/
COPY run_full_experiments.py run_tests.py ./

# Default: quick experiments + tests (CI-style smoke run)
CMD ["bash", "-lc", "python run_tests.py && python run_full_experiments.py --quick --output-dir results_docker"]
