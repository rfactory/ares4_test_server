from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse
import json

router = APIRouter()

@router.post("/auth")
async def mqtt_auth(request: Request):
    raw_body = await request.body()
    print(f"[EMQX Auth] Raw request body (bytes): {raw_body}")
    try:
        body = json.loads(raw_body)
        print(f"[EMQX Auth] Parsed JSON body: {body}")
    except json.JSONDecodeError:
        print("[EMQX Auth] Failed to decode JSON from request body.")
        # Still allow for now, but log the failure
        return JSONResponse(content={"result": "allow"})

    # For now, allow all connections
    return JSONResponse(content={"result": "allow"})

@router.post("/acl")
async def mqtt_acl(request: Request):
    raw_body = await request.body()
    print(f"[EMQX ACL] Raw request body (bytes): {raw_body}")
    try:
        body = json.loads(raw_body)
        print(f"[EMQX ACL] Parsed JSON body: {body}")
    except json.JSONDecodeError:
        print("[EMQX ACL] Failed to decode JSON from request body.")
        # Still allow for now, but log the failure
        return JSONResponse(content={"result": "allow"})

    # For now, allow all publish/subscribe requests
    return JSONResponse(content={"result": "allow"})

@router.post("/superuser")
async def mqtt_superuser(request: Request):
    # TODO: Implement actual superuser logic
    # For now, deny all
    return {"result": 'deny'}
