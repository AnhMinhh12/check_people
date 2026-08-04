# Image NVIDIA CUDA với Ubuntu 22.04
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết
RUN sed -i 's/archive.ubuntu.com/mirrors.edge.kernel.org/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.edge.kernel.org/g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-distutils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Cài đặt đồng thời tất cả thư viện (Đảm bảo CUDA 12.1 được giữ nguyên)
COPY requirements.txt .
RUN python3.11 -m pip install --no-cache-dir --upgrade pip && \
    python3.11 -m pip install --no-cache-dir --ignore-installed -r requirements.txt

COPY . .

EXPOSE 5000

LABEL version="5.8-gpu-fixed"
LABEL description="Sentinel Warden AI - Fixed GPU Compatibility"

CMD ["python3.11", "-m", "app.main"]
