import sys
import http.client
import json # New import for JSON parsing

try:
    conn = http.client.HTTPConnection("localhost", 8000, timeout=5)
    conn.request("GET", "/health/mqtt") # Changed from "/health"
    response = conn.getresponse()
    if response.status == 200:
        # Check specific status from the new endpoint's response
        response_data = json.loads(response.read().decode())
        if response_data.get("status") == "mqtt_connected":
            print("Health check passed: MQTT connected.")
            sys.exit(0)
        else:
            print(f"Health check failed: MQTT reported disconnected. Status: {response_data.get('status')}")
            sys.exit(1)
    elif response.status == 503: # Service Unavailable for mqtt_disconnected
        print("Health check failed: MQTT service unavailable (disconnected).")
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