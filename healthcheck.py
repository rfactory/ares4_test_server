import sys
import http.client

try:
    conn = http.client.HTTPConnection("localhost", 8000, timeout=5)
    conn.request("GET", "/health")
    response = conn.getresponse()
    if response.status == 200:
        print("Health check passed.")
        sys.exit(0)
    else:
        print(f"Health check failed with status: {response.status}")
        sys.exit(1)
except Exception as e:
    print(f"Health check failed with exception: {e}")
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
