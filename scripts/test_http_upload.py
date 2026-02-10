import requests
import os

# --- 설정 ---
IMAGE_FILENAME = "test_image.jpg"

# [수정] 다니엘님이 DB에 시딩해둔 "진짜 UUID"를 넣습니다.
TEST_UUID = "550e8400-e29b-41d4-a716-446655440000" 

# 도커 내부 통신용 주소
URL = "http://fastapi_app2:8000/api/v1/upload/image"

def upload_test():
    if not os.path.exists(IMAGE_FILENAME):
        print(f"❌ Error: '{IMAGE_FILENAME}' 파일이 없습니다.")
        return

    print(f"📸 Uploading {IMAGE_FILENAME} to {URL}...")

    try:
        with open(IMAGE_FILENAME, "rb") as f:
            files = {"file": (IMAGE_FILENAME, f, "image/jpeg")}
            
            data = {
                "device_uuid": TEST_UUID, # 여기 수정됨
                "snapshot_id": "snap-docker-test-001"
            }
            
            response = requests.post(URL, files=files, data=data)
            
            if response.status_code == 200:
                print("✅ Upload Success!")
                print(f"📩 Server Response: {response.json()}")
                print("📂 확인: 'server2/storage/devices/...' 폴더를 확인하세요.")
            else:
                print(f"❌ Upload Failed (Code: {response.status_code})")
                print(f"📩 Error Message: {response.text}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    upload_test()