FROM python:3.11-slim

# Enable VA-API (AMD) support in container for hosts exposing /dev/dri
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
        libva2 libva-drm2 libdrm2 mesa-va-drivers vainfo \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LIBVA_DRIVER_NAME=radeonsi

WORKDIR /app

COPY . /app

RUN python -m pip install --upgrade pip \
    && python -m pip install .

# Keep container alive by default; exec in to run CLI or set command
CMD ["bash", "-lc", "commonforms --help || true; sleep infinity"]

