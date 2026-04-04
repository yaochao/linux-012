FROM --platform=linux/amd64 ubuntu:22.04

RUN apt-get update && apt-get install -y \
    bin86 \
    build-essential \
    file \
    gcc-multilib \
    patch \
    python3 \
    tar \
    util-linux \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
