그# Server -> Server2 마이그레이션 계획 (v4)

이 문서는 기존 `server`의 API 엔드포인트 로직을 `server2`의 새로운 아키텍처 및 데이터 모델로 이전하기 위한 구체적인 실행 계획을 정의합니다.

## 1. 핵심 원칙

- **`server2` 우선**: 마이그레이션은 `server`의 로직을 그대로 복사하는 것이 아니라, `server2`의 아키텍처(`4계층`, `도메인 분리`)와 "온톨로지화된" 데이터 모델에 맞게 **재작성**하는 것을 원칙으로 합니다.
- **기능 통합**: `server2`에 이미 존재하는 기능이 `server`의 기능보다 더 고도화된 경우(예: 2FA 로그인), `server2`의 기능을 유지하면서 `server`의 세부 로직(예: `username.strip()`)을 흡수하여 개선합니다.
- **점진적 확장**: `server2`에 없는 새로운 기능(예: 비밀번호 재설정)은 `server2`의 아키텍처 가이드라인에 따라 스키마, 서비스, 엔드포인트 순으로 점진적으로 구현합니다.

---

## 2. 엔드포인트별 마이그레이션 계획

### 2.1. 인증 (Authentication)

-   **`[대상] server2` 도메인:** `server2/app/domains/accounts`

#### 2.1.1. 사용자 등록

-   **`[원본] server` 엔드포인트:** `POST /register-owner`
    ```python
@router.post("/register-owner", response_model=schemas.User)
def register_owner(user_data: schemas.UserCreateOwner, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.register_owner(user_data)
    # ... email sending ...
    return user
    ```
-   **`[기존] server2` 현황:** `POST /users/` 엔드포인트와 `account_service.create_user`가 존재하나, 단순 사용자 생성 기능만 있음. 이메일 인증, 역할 할당 로직 부재.
-   **`[핵심] 모델 차이점:** `server2`의 `User` 모델은 `UserOrganizationRole`을 통해 역할(Role)과 연결됩니다. 단순 생성이 아닌, 역할 할당 관계를 함께 생성해야 합니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **서비스 수정 (`account_service.create_user`):**
        -   사용자 생성 시, `roles` 테이블에서 기본 'user' 역할을 조회합니다.
        -   `UserOrganizationRole` 테이블에 새 사용자와 기본 역할을 연결하는 레코드를 생성합니다 (조직이 없으므로 `organization_id=None`).
        -   `server`와 같이 이메일 인증 토큰(`email_verification_token`) 생성 로직을 추가합니다.
    2.  **엔드포인트 수정 (`api/endpoints_user.py`):**
        -   `create_user` 엔드포인트가 `BackgroundTasks`를 주입받아 서비스 계층으로 전달하여, 인증 이메일을 비동기 전송하도록 수정합니다.

---

#### 2.1.2. 로그인

-   **`[원본] server` 엔드포인트:** `POST /login`
    ```python
@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.login(form_data.username.strip(), form_data.password)
    ```
-   **`[기존] server2` 현황:** `POST /token` 엔드포인트와 `account_service.login`에 2단계 인증(2FA)을 포함한 더 고도화된 로그인 로직이 이미 구현되어 있습니다.
-   **`[핵심] 모델 차이점:** `server2`는 2FA 관련 필드(`is_two_factor_enabled`, `email_verification_token` 등)를 `User` 모델에서 직접 관리합니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **서비스 개선 (`account_service.login`):**
        -   `server2`의 고도화된 로직을 유지합니다.
        -   `server`의 로직에서 참고할 만한 `form_data.username.strip()`과 같은 사용자 경험 개선 코드를 `server2` 서비스에 적용합니다.

---

#### 2.1.3. 비밀번호 재설정

-   **`[원본] server` 엔드포인트:** `POST /forgot-password`, `POST /reset-password`
-   **`[기존] server2` 현황:** 해당 기능이 없습니다.
-   **`[핵심] 모델 차이점:** `server2`의 `User` 모델에 `reset_token`, `reset_token_expires_at` 필드가 이미 존재하여 기능 구현에 바로 사용할 수 있습니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **스키마 추가 (`accounts/schemas/token.py`):** `ForgotPasswordRequest`, `ResetPasswordRequest` Pydantic 스키마를 추가합니다.
    2.  **서비스 추가 (`account_service.py`):**
        -   `forgot_password`: 이메일을 받아 사용자를 찾고, `reset_token`을 생성/저장한 후 이메일로 발송하는 서비스 메소드를 추가합니다.
        -   `reset_password`: `reset_token`을 검증하고 새 비밀번호로 교체하는 서비스 메소드를 추가합니다.
    3.  **엔드포인트 추가 (`api/endpoints_auth.py`):** `/forgot-password` 및 `/reset-password` 엔드포인트를 추가하고, 위에서 만든 서비스 메소드를 각각 호출합니다.

---

### 2.2. 기기 관리 (Device Management)

-   **`[대상] server2` 도메인:** `server2/app/domains/devices`
-   **`[원본] server` 소스:** `server/app/api/routes/devices.py`

#### 2.2.1. 사용자 기기 목록 조회

-   **`[원본] server` 엔드포인트:** `GET /`
    ```python
@router.get("/", response_model=List[schemas.DeviceForUser])
def read_user_devices(db: Session = Depends(get_db), current_user: models.User = Depends(PermissionChecker("device:read"))):
    user_device_links = devices.get_user_devices(db=db, user_id=current_user.id)
    
    response = []
    for device, user_device in user_device_links:
        device_data = schemas.Device.model_validate(device)
        response.append(schemas.DeviceForUser(
            **device_data.model_dump(),
            nickname=user_device.nickname,
            role=user_device.role
        ))
    return response
    ```
-   **`[기존] server2` 현황:** `GET /devices` 엔드포인트와 `get_multi_devices_with_auth_check` 의존성이 존재합니다. 하지만 현재 `Device` 객체 목록만 반환하며, `nickname`과 같은 사용자별 정보를 포함하지 않습니다.
-   **`[핵심] 모델 차이점:** `server`는 `user_devices` 테이블을 직접 조회하여 `nickname`을 가져옵니다. `server2`는 `Device` 모델에 `users`라는 `relationship`을 통해 `UserDevice` 객체에 접근할 수 있습니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **스키마 수정/추가 (`devices/schemas/device.py`):**
        -   `server`의 `DeviceForUser`와 같이 `nickname`, `role`등 사용자-기기 연결 정보가 포함된 새로운 응답 스키마 `DeviceResponse`를 정의합니다.
    2.  **의존성 수정 (`dependencies/device_dependencies.py`):**
        -   `get_multi_devices_with_auth_check` 함수가 `Device`와 `UserDevice` 정보를 조합하여 새로 정의한 `DeviceResponse` 스키마에 맞는 데이터를 반환하도록 로직을 수정합니다.

---

#### 2.2.2. 기기 별명 수정

-   **`[원본] server` 엔드포인트:** `PUT /{device_id}/nickname`
    ```python
@router.put("/{device_id}/nickname", response_model=schemas.DeviceForUser)
def update_device_nickname_for_user(
    device_id: Annotated[int, Path()],
    nickname_in: schemas.NicknameUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="device:update"))
):
    updated_link = devices.update_user_device_nickname(db=db, user_id=current_user.id, device_id=device_id, nickname=nickname_in.nickname)
    
    # Retrieve the device object to construct the response
    device_obj = devices.get_device_by_id(db, device_id=device_id)
    if not device_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device_data = schemas.Device.model_validate(device_obj)
    return schemas.DeviceForUser(
        **device_data.model_dump(),
        nickname=updated_link.nickname,
        role=updated_link.role
    )
    ```

-   **`[기존] server2` 현황:** 해당 기능이 없습니다. `PUT /{device_id}`는 일반적인 기기 정보 업데이트만 처리합니다.
-   **`[핵심] 모델 차이점:** `server`와 `server2` 모두 `user_devices` 테이블(모델 `UserDevice`)에 `nickname` 필드가 존재하여 로직은 유사할 것입니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **스키마 추가 (`devices/schemas/device.py`):** `NicknameUpdate` Pydantic 스키마를 추가합니다.
    2.  **서비스 추가 (`services/device_service.py`):**
        -   `update_device_nickname` 메소드를 새로 추가합니다. 이 메소드는 `user_id`와 `device_id`로 `UserDevice` 레코드를 찾아 `nickname` 필드를 업데이트합니다.
    3.  **엔드포인트 추가 (`api/endpoints_device_management.py`):**
        -   `PUT /{device_id}/nickname` 엔드포인트를 추가하고, `update_device_nickname` 서비스 메소드를 호출합니다. 사용자 권한 확인을 위해 `DeviceAccessChecker`와 유사한 의존성 사용이 필요합니다.

#### 2.2.3. 기기 연결 해제 및 비활성화 (수정된 계획)

-   **`[원본] server` 엔드포인트:** `DELETE /{device_id}` (사용자-기기 연결 해제)
    ```python
@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device(
    device_id: Annotated[int, Path()],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="device:delete"))
):
    link = devices.unlink_user_from_device(db=db, user_id=current_user.id, device_id=device_id)
    if not link:
        raise HTTPException(status_code=404, detail="Device not found or not registered to your account.")
    return
    ```
-   **`[기존] server2` 현황:** `DELETE /devices/{device_id}` 엔드포인트와 `device_service.delete_device` (소프트 삭제)가 이미 존재합니다.
-   **`[핵심] 로직 분리 필요:** '사용자와 기기의 연결을 끊는 것(Unlink)'과 '기기 자체를 시스템에서 비활성화하는 것(Deactivate)'은 다른 시나리오입니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **서비스 메소드 분리 (`services/device_service.py`):**
        -   **`unlink_device_from_user` (신설):** `UserDevice` 테이블에서 레코드만 삭제하여, 요청한 사용자와 기기의 연결을 끊습니다. 이 메소드를 호출하는 엔드포인트는 기기의 소유자 또는 관리자만 접근할 수 있도록 권한 검사가 필요합니다.
            -   **관리자 요청 시 사용자 승인 프로세스 추가:** 관리자가 이 메소드를 호출하여 기기 소유자의 연결을 해제하려고 할 경우, 즉시 연결을 해제하지 않고 사용자에게 승인 요청(예: 알림, 이메일)을 보내야 합니다. 이를 위해 새로운 `UnlinkRequest` 모델과 승인/거부 엔드포인트가 필요할 수 있습니다.
        -   **`deactivate_device` (기존 `delete_device`에서 이름 변경):** 기기의 `is_active` 플래그를 `False`로 설정하여 시스템 전체에서 비활성화(소프트 삭제)합니다. 이 메소드는 관리자만 호출할 수 있도록 권한 검사가 필요합니다.
    2.  **엔드포인트 매핑 수정 (`api/endpoints_device_management.py`):**
        -   `DELETE /devices/{device_id}` 엔드포인트는 `unlink_device_from_user` 서비스 메소드를 호출하도록 변경합니다. 해당 엔드포인트는 `DeviceAccessChecker`와 같은 의존성을 통해 기기 소유자 또는 관리자 권한을 확인해야 합니다.
        -   관리자용 기기 비활성화 엔드포인트(예: `DELETE /admin/devices/{device_id}/deactivate`)를 별도로 구현하여 `deactivate_device`를 호출하도록 할 수 있습니다.

---

### 2.3. 기기 프로비저닝 (Device Provisioning)

-   **`[대상] server2` 도메인:** `server2/app/domains/devices`
-   **`[원본] server` 소스:** `server/app/api/routes/devices.py` (`/preregister`, `/claim`, `/credentials`)
-   **`[기존] server2` 현황:** 관련 기능이 전혀 없습니다.
-   **`[핵심] 모델 차이점:** `server`는 `hardware_blueprint_version` 문자열을 사용하지만, `server2`는 `hardware_blueprints` 테이블에 대한 외래 키(`hardware_blueprint_id`)를 사용합니다. 또한 `server2`는 인증서 관리를 위한 별도의 `certificates` 테이블이 있습니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **기능 신설:** `devices` 도메인에 프로비저닝 관련 기능을 전체적으로 새로 구현합니다.
    2.  **스키마 추가 (`devices/schemas/`):** `DevicePreRegisterRequest`, `DeviceClaimRequest`, `DeviceCredentials`, `DeviceForUser` 등 프로비저닝에 필요한 Pydantic 스키마를 새로 생성합니다.
    3.  **서비스 추가 (`services/device_service.py`):**
        -   `preregister_device`: `cpu_serial`과 `hardware_blueprint_version`을 받아 `hardware_blueprints` 테이블에서 ID를 조회한 후, `devices` 테이블에 새 레코드를 생성합니다.
        -   `claim_device`: `cpu_serial`로 사전 등록된 기기를 찾아, 요청한 사용자와 `UserDevice` 테이블을 통해 연결(소유권) 관계를 생성합니다.
        -   `get_device_credentials`: `cpu_serial`로 기기를 찾아, `certificates` 테이블과 연계하여 생성된 인증서 정보를 반환하는 로직을 구현합니다.
    4.  **엔드포인트 추가 (`api/endpoints_provisioning.py`):** `server2/app/domains/devices/api/` 경로에 `endpoints_provisioning.py` 파일을 생성하고, `/preregister`, `/claim`, `/credentials` 엔드포인트를 담아 위 서비스 메소드들을 호출하도록 구현합니다.

---

### 2.4. 데이터 조회 및 명령 (Data Retrieval & Commands)

-   **`[대상] server2` 도메인:** `server2/app/domains/data` 및 `server2/app/domains/devices`
-   **`[원본] server` 소스:** `server/app/api/routes/devices.py` (`/telemetry`, `/command`, `/change-wifi`)

#### 2.4.1. 텔레메트리 데이터 조회

-   **`[원본] server` 엔드포인트:** `GET /{device_id}/telemetry`
    ```python
@router.get("/{device_id}/telemetry")
def read_telemetry_data(
    device_id: Annotated[int, Path()],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="telemetry:read")),
    topic_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 1000
):
    db_telemetry = telemetry.get_telemetry_data(
        db=db, 
        device_id=device_id, 
        topic_filter=topic_filter, 
        start_date=start_date, 
        end_date=end_date, 
        skip=skip, 
        limit=limit
    )
    return filter_telemetry_payload(db_telemetry)
    ```

-   **`[기존] server2` 현황:** `data` 도메인은 아직 리팩토링되지 않았습니다. `server2`의 `TelemetryData` 모델이 존재합니다.
-   **`[핵심] 모델 차이점:** `server`는 `telemetry` CRUD에서 데이터를 조회합니다. `server2`는 `TelemetryData` 모델을 사용하며, `device_id`는 외래 키입니다. `server`의 `filter_telemetry_payload`는 `server2`의 `data` 도메인으로 옮겨져야 합니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **`data` 도메인 리팩토링:** `data` 도메인을 `accounts`와 유사한 방식으로 먼저 리팩토링합니다. `data_crud.py`, `data_service.py`, `data_dependencies.py`를 생성하고 `schemas`를 분리합니다.
    2.  **서비스 추가 (`data_service.py`):** `get_telemetry_data` 메소드를 구현하여 `TelemetryData` 모델을 사용하여 데이터를 조회합니다. `filter_telemetry_payload` 로직도 이 서비스로 옮깁니다.
    3.  **의존성 추가 (`data_dependencies.py`):** `get_telemetry_data_dependency`와 같이 텔레메트리 데이터 조회를 위한 의존성을 구현합니다. 이는 권한 확인과 필터링 파라미터 처리를 담당합니다.
    4.  **엔드포인트 추가 (`data/api/endpoints_telemetry.py`):** `GET /{device_id}/telemetry` 엔드포인트를 추가하고, 새로 만든 서비스 및 의존성을 사용합니다.

#### 2.4.2. 기기 명령 전송

-   **`[원본] server` 엔드포인트:** `POST /{device_id}/command`
    ```python
@router.post("/{device_id}/command")
def send_device_command(
    device_id: Annotated[int, Path()],
    command: schemas.DeviceCommand,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="command:send"))
):
    # ...
    target_device = devices.get_device_by_id(db, device_id=device_id)
    # ...
    topic = mqtt_utils.build_command_topic(user_email, str(device_uuid), command.component, command.action)
    payload = {"command": command.action, "duration": command.duration_seconds}
    success = publisher.publish_command(topic, payload)
    # ...
    ```

-   **`[기존] server2` 현황:** `devices` 도메인에 명령 전송 기능이 없습니다.
-   **`[핵심] 모델 차이점:** `server2`는 `Device` 모델을 통해 `current_uuid`에 접근하며, `User` 모델을 통해 `email`을 가져올 수 있습니다. MQTT 관련 유틸리티는 `server2/app/mqtt`에 별도로 존재합니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **스키마 추가 (`devices/schemas/`):** `DeviceCommand` Pydantic 스키마를 추가합니다.
    2.  **서비스 추가 (`services/device_service.py`):** `send_command` 메소드를 구현합니다. 이 메소드는 `device_id`, `command` 스키마, `current_user`를 받아 MQTT 토픽을 구성하고 메시지를 발행합니다.
    3.  **엔드포인트 추가 (`api/endpoints_device_management.py` 또는 `api/endpoints_commands.py`):** `POST /{device_id}/command` 엔드포인트를 추가하고, `device_service.send_command`를 호출하도록 구현합니다. `DeviceAccessChecker`와 유사한 의존성 사용이 필요합니다.

#### 2.4.3. Wi-Fi 변경

-   **`[원본] server` 엔드포인트:** `POST /{device_id}/change-wifi`
    ```python
@router.post("/{device_id}/change-wifi")
def change_device_wifi(
    device_id: Annotated[int, Path()],
    wifi_request: schemas.WifiChangeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="command:send"))
):
    # ...
    target_device = devices.get_device_by_id(db, device_id=device_id)
    # ...
    topic = mqtt_utils.build_command_topic(user_email, str(device_uuid), "system", "change_wifi")
    payload = {"ssid": wifi_request.ssid, "password": wifi_request.password}
    success = publisher.publish_command(topic, payload)
    # ...
    ```

-   **`[기존] server2` 현황:** `devices` 도메인에 Wi-Fi 변경 기능이 없습니다.
-   **`[핵심] 모델 차이점:** `server2`는 `Device` 모델을 통해 `current_uuid`에 접근하며, `User` 모델을 통해 `email`을 가져올 수 있습니다. MQTT 관련 유틸리티는 `server2/app/mqtt`에 별도로 존재합니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **스키마 추가 (`devices/schemas/`):** `WifiChangeRequest` Pydantic 스키마를 추가합니다.
    2.  **서비스 추가 (`services/device_service.py`):** `change_wifi` 메소드를 구현합니다. 이 메소드는 `device_id`, `wifi_request` 스키마, `current_user`를 받아 MQTT 토픽을 구성하고 메시지를 발행합니다.
    3.  **엔드포인트 추가 (`api/endpoints_device_management.py` 또는 `api/endpoints_commands.py`):** `POST /{device_id}/change-wifi` 엔드포인트를 추가하고, `device_service.change_wifi`를 호출하도록 구현합니다. `DeviceAccessChecker`와 유사한 의존성 사용이 필요합니다.

---

### 2.5. OTA 업데이트 (OTA Updates)

-   **`[대상] server2` 도메인:** `server2/app/domains/firmware` (새 도메인 필요) 및 `devices`
-   **`[원본] server` 소스:** `server/app/api/routes/devices.py` (`/ota-trigger`) 및 `server/app/api/routes/firmware_updates.py` (가정)

#### 2.5.1. OTA 업데이트 트리거

-   **`[원본] server` 엔드포인트:** `POST /{device_id}/ota-trigger`
    ```python
@router.post("/{device_id}/ota-trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_ota_update(
    device_id: Annotated[int, Path()],
    ota_request: schemas.OtaTriggerRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="device:update"))
):
    # ...
    target_device = devices.get_device_by_id(db, device_id=device_id)
    # ...
    firmware_update = firmware_updates.get_firmware_update_by_version(db, version=ota_request.version)
    # ...
    topic = mqtt_utils.build_command_topic(user_email, str(device_uuid), "ota", "notify")
    payload = {"version": firmware_update.version, "package_url": firmware_update.package_url, "package_hash": firmware_update.package_hash}
    success = publisher.publish_command(topic, payload)
    # ...
    ```

-   **`[기존] server2` 현황:** `devices` 도메인에 OTA 업데이트 트리거 기능이 없습니다. `firmware_updates` 모델은 `server2/app/models/objects/firmware_update.py`에 존재합니다.
-   **`[핵심] 모델 차이점:** `server2`의 `FirmwareUpdate` 모델을 사용하여 펌웨어 정보를 조회해야 합니다. `Device` 모델을 통해 `current_uuid`에 접근합니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **새 도메인 생성:** `firmware` 도메인을 `server2/app/domains`에 새로 생성하고, `firmware_crud.py`, `firmware_service.py`, `firmware_dependencies.py`, `firmware_schemas.py` 등을 구현합니다.
    2.  **스키마 추가 (`devices/schemas/` 또는 `firmware/schemas/`):** `OtaTriggerRequest` Pydantic 스키마를 추가합니다.
    3.  **서비스 추가 (`services/device_service.py`):** `trigger_ota_update` 메소드를 구현합니다. 이 메소드는 `device_id`, `ota_request` 스키마, `current_user`를 받아 펌웨어 정보를 조회하고 MQTT 메시지를 발행합니다.
    4.  **엔드포인트 추가 (`api/endpoints_device_management.py` 또는 `api/endpoints_ota.py`):** `POST /{device_id}/ota-trigger` 엔드포인트를 추가하고, `device_service.trigger_ota_update`를 호출하도록 구현합니다. `DeviceAccessChecker`와 유사한 의존성 사용이 필요합니다.

---

### 2.6. 사용자 관리 (User Management) (신규 계획)

-   **`[대상] server2` 도메인:** `server2/app/domains/accounts`
-   **`[원본] server` 소스:** `server/app/api/routes/users.py` (`/me`)
-   **`[참조] server2` 아키텍처:** `server2/docs/ARCHITECTURE/AUTH_ARCHITECTURE.md`

#### 2.6.1. 자기 계정 삭제

-   **`[원본] server` 엔드포인트:** `DELETE /me`
    ```python
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(db: Session = Depends(get_db), current_user: models.User = Depends(PermissionChecker("user:delete:self"))):
    users.delete_user(db=db, user_id=current_user.id)
    return
    ```
-   **`[기존] server2` 현황:** 해당 기능이 없습니다.
-   **`[핵심] 규칙:** `AUTH_ARCHITECTURE.md`에 따라, 모든 사용자는 자신의 계정을 삭제(비활성화)할 수 있습니다. 단, 관리자(스태프) 계정은 이 API로 삭제할 수 없습니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **서비스 추가 (`services/account_service.py`):** `delete_self` 메소드를 추가합니다.
        -   요청한 사용자가 `is_staff=True`인지 확인하고, 스태프일 경우 에러를 발생시켜 삭제를 막습니다.
        -   일반 사용자일 경우, 해당 사용자의 `is_active` 플래그를 `False`로 설정하여 소프트 삭제합니다.
    2.  **엔드포인트 추가 (`api/endpoints_user.py`):** `DELETE /users/me` 엔드포인트를 추가하고 `delete_self` 서비스를 호출합니다.

#### 2.6.2. 관리자의 스태프 계정 삭제

-   **`[원본] server` 엔드포인트:** 해당 기능이 없습니다. `server2`의 신규 기능입니다.
-   **`[기존] server2` 현황:** 해당 기능이 없습니다.
-   **`[핵심] 규칙:** `AUTH_ARCHITECTURE.md`에 정의된 복잡한 규칙을 따릅니다.
    -   `user:delete:staff` 권한이 있는 T0 관리자(`Prime_Admin`, `System_Admin`)만 호출 가능합니다.
    -   일반 사용자는 삭제할 수 없습니다.
    -   `Prime_Admin`은 `System_Admin`을 삭제할 수 없습니다.
    -   `System_Admin`은 `Prime_Admin`을 삭제할 수 있습니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **서비스 추가 (`services/account_service.py`):** `delete_staff_by_admin` 메소드를 새로 추가합니다.
        -   `AUTH_ARCHITECTURE.md`에 기술된 모든 권한 확인, 대상 확인, 상호 견제 로직을 구현합니다.
        -   조건을 통과하면 대상 스태프 계정을 소프트 삭제(`is_active=False`)합니다.
    2.  **엔드포인트 추가 (`api/admin_endpoints.py` 등):** 관리자 전용 경로(예: `DELETE /admin/users/{user_id}`)에 새 엔드포인트를 추가하고 `delete_staff_by_admin` 서비스를 호출합니다. 이 엔드포인트는 T0 역할 권한을 확인하는 별도의 의존성을 사용해야 합니다.