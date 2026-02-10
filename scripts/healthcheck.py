import http.client
import sys

def check_health():
    """
    Docker Compose가 컨테이너의 건강 상태를 확인하기 위해 실행하는 스크립트입니다.
    """
    try:
        # [핵심 수정] localhost 대신 도커 네트워크 상의 서비스 이름 'fastapi_app2'를 사용하거나 
        # 컨테이너 내부이므로 0.0.0.0 또는 127.0.0.1을 사용합니다.
        # 여기서는 컨테이너 내부 로컬 루프백을 호출합니다.
        conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=5)
        conn.request("GET", "/health") # app.main 또는 라우터에 설정된 헬스체크 엔드포인트
        
        response = conn.getresponse()
        if response.status == 200:
            print("✅ Health check passed")
            sys.exit(0)
        else:
            print(f"❌ Health check failed with status: {response.status}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Health check error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_health()