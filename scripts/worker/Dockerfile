# 1. 베이스 이미지 선택
FROM python:3.11-slim

# 2. 필수 시스템 패키지 설치 (이미지 가공을 위한 libGL 등 필요한 경우 추가)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /workspace

# 4. 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사 (프로젝트 루트 전체)
COPY . .

# 6. 환경 변수 설정 (Python 모듈 경로 인식)
ENV PYTHONPATH=/workspace

# 7. 실행 명령 (Entrypoint)
# 서버와 달리 uvicorn이 아닌 python으로 워커 스크립트를 직접 실행합니다.
CMD ["python", "scripts/worker/image_worker.py"]