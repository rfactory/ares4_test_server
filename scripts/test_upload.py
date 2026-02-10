import requests
import base64
import logging

# Ares4 서버 주소 (FastAPI) - .env 포트 8002 반영
API_URL = "http://localhost:8002/api/v1/mqtt/publish"
HEADERS = {
    "X-Ares-Secret": "ares4-super-secret-key-2026", # .env의 시크릿 키
    "Content-Type": "application/json"
}
DEVICE_UUID = "550e8400-e29b-41d4-a716-446655440000"

def run_test():
    # 1. 가짜 이미지 데이터 생성 (1x1 투명 PNG)
    dummy_img = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    img_b64 = base64.b64encode(dummy_img).decode('utf-8')

    # 2. 전송 데이터 구성 (EMQX Webhook 포맷)
    # [중요] IngestionDispatcher.py의 device_uuid = topic.split("/")[1] 로직에 맞게 토픽 수정
    # 토픽의 1번 인덱스(두 번째 자리)에 DEVICE_ID가 와야 'devices' 문자열 에러를 피할 수 있습니다.
    test_topic = f"ares4/{DEVICE_UUID}/images" 

    payload = {
        "topic": test_topic,
        "payload": {
            # Pydantic 모델이 가장 먼저 찾는 필드
            "id": "snap-20260127-001",
            "observation_type": "IMAGE",
            "device_id": DEVICE_UUID,
            "image_data": img_b64,
            "metadata": {
                "type": "IMAGE",
                "snapshot_id": "snap-20260127-001", # 로직 중복 대비
                "farm_type": "smart-farm-lab"
            }
        },
        "username": "ares_user",
        "clientid": DEVICE_UUID
    }

    print(f"📡 {DEVICE_UUID}에서 {test_topic} 토픽으로 Webhook 전송 시도...")
    
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        
        if response.status_code == 200:
            print("✅ [성공] 서버가 데이터를 수락하고 Dispatcher가 작동했습니다!")
            print(f"📩 서버 응답: {response.json()}")
        else:
            print(f"❌ [실패] 상태 코드: {response.status_code}")
            print(f"📝 응답 내용: {response.text}")
            print("\n💡 팁: 'devices' 파싱 에러가 여전하다면 서버의 IngestionDispatcher 인덱스 로직을 재확인하세요.")
            
    except Exception as e:
        print(f"🚨 에러 발생: {e}")

if __name__ == "__main__":
    run_test()