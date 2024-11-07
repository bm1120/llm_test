# Python 3.9 이미지를 기본으로 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# Chromium 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    unzip \
    build-essential \
    python3-dev \
    xvfb \
    dbus-x11 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 필요한 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 가상 디스플레이 설정
ENV DISPLAY=:99
ENV DBUS_SESSION_BUS_ADDRESS=/dev/null

# 실행 명령
CMD Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset > /dev/null 2>&1 & python ai_crawling_automation.py
