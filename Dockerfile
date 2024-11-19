# Python 3.9 이미지를 기본으로 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

ENV PORT 8080

# 실행 명령
CMD ["python", "ai_productivity_tools.py"]
