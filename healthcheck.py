import sys
import http.client

try:
    conn = http.client.HTTPConnection("localhost", 8000, timeout=5)
    conn.request("GET", "/health")
    response = conn.getresponse()
    if response.status == 200:
        from app.domains.mqtt.client import is_mqtt_connected  # 여기서 임포트
        if is_mqtt_connected:
            print("Health check passed.")
            sys.exit(0)
        else:
            print("Health check failed: MQTT not connected")
            sys.exit(1)
    else:
        print(f"Health check failed with status: {response.status}")
        sys.exit(1)
except Exception as e:
    print(f"Health check failed with exception: {e}")
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()