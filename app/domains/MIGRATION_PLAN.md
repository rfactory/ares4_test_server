# Server -> Server2 마이그레이션 계획

이 문서는 기존 `server`의 API 엔드포인트 로직을 `server2`의 새로운 아키텍처 및 데이터 모델로 이전하기 위한 구체적인 실행 계획을 정의합니다.

## 1. 핵심 원칙

- **`server2` 우선**: 마이그레이션은 `server`의 로직을 그대로 복사하는 것이 아니라, `server2`의 아키텍처(`4계층`, `도메인 분리`)와 "온톨로지화된" 데이터 모델에 맞게 **재작성**하는 것을 원칙으로 합니다.
- **기능 통합**: `server2`에 이미 존재하는 기능이 `server`의 기능보다 더 고도화된 경우(예: 2FA 로그인), `server2`의 기능을 유지하면서 `server`의 세부 로직(예: `username.strip()`)을 흡수하여 개선합니다.
- **점진적 확장**: `server2`에 없는 새로운 기능(예: 비밀번호 재설정)은 `server2`의 아키텍처 가이드라인에 따라 스키마, 서비스, 엔드포인트 순으로 점진적으로 구현합니다.
- **역할 기반 권한 검증 (Role-Based Permission-Checking):** 관리자용 엔드포인트는 단순 관리자 여부(`is_staff`)가 아닌, 구체적인 역할(Role)과 그에 부여된 권한(Permission)을 반드시 확인해야 한다.
- **서비스 계층 분리 (Service Layer Separation):** 서비스 계층의 메소드는 그 기능의 주요 사용자(User, Admin, Organization)에 따라 논리적으로 분리하여 책임과 역할을 명확히 한다. **인증 없이 접근 가능한 기능은 `Public (Anonymous)` 등으로 명확히 표기합니다.**
- **소유 기반 접근 제어 (Ownership-Based Access Control):** 일반 사용자(User)는 자신의 계정 및 소유한 리소스(예: 기기)에 대해서만 접근 및 수정이 가능하며, 조직(Organization)은 자신이 관리하는 리소스에 대해서만 접근 및 수정이 가능하다. 관리자는 역할 기반 권한 검증에 따라 더 넓은 범위의 접근 권한을 가질 수 있다.

---

## 2. 엔드포인트별 마이그레이션 계획

### 2.1. 인증 (Authentication)

-   **`[대상] server2` 도메인:** `server2/app/domains/accounts`

#### 2.1.1. 사용자 등록 (`POST /register-owner`)

-   **`[주요 사용자]`** 일반 가입자 (`/register-owner`)
-   **`[서비스 분리]`** `Public (Anonymous)`
-   **`[원본] server` 엔드포인트:** `POST /register-owner`
    ```python
@router.post("/register-owner", response_model=schemas.User)
def register_owner(user_data: schemas.UserCreateOwner, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user = auth_service.register_owner(user_data)
    # ... email sending ...
    return user
    ```
-   **`[기존] server2` 현황:** `POST /users/` 엔드포인트와 `account_service.create_user`가 존재하나, 단순 사용자 생성 기능만 있습니다. 이메일 인증, 역할 할당 로직이 없습니다.
-   **`[핵심] 모델 차이점:** `server2`의 `User` 모델은 `UserOrganizationRole`을 통해 역할(Role)과 연결됩니다.
-   **`[계획] 마이그레이션 전략:**
    1.  **서비스 수정 (`account_service.create_user`):**
        -   사용자 생성 시, `roles` 테이블에서 기본 'user' 역할을 조회합니다.
        -   `UserOrganizationRole` 테이블에 새 사용자와 기본 역할을 연결하는 레코드를 생성합니다.
        -   이메일 인증 토큰(`email_verification_token`) 생성 로직을 추가합니다.
    2.  **엔드포인트 수정 (`api/endpoints_user.py`):**
        -   `create_user` 엔드포인트가 `BackgroundTasks`를 주입받아 서비스 계층으로 전달하여, 인증 이메일을 비동기 전송하도록 수정합니다.

#### 2.1.2. 로그인 (`POST /login`)

-   **`[주요 사용자]`** 모든 사용자 (`/login`)
-   **`[서비스 분리]`** `Public (Anonymous)`
-   **`[원본] server` 엔드포인트:** `POST /login`
    ```python
@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.login(form_data.username.strip(), form_data.password)
    ```
-   **`[기존] server2` 현황:** `POST /token` 엔드포인트와 `account_service.login`에 2단계 인증(2FA)을 포함한 더 고도화된 로그인 로직이 이미 구현되어 있습니다.
-   **`[핵심] 모델 차이점:** `server2`는 2FA 관련 필드(`is_two_factor_enabled`, `email_verification_token` 등)를 `User` 모델에서 직접 관리합니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **서비스 개선 (`account_service.login`):** `server2`의 고도화된 로직을 유지하면서, `server`의 로직에서 참고할 만한 `form_data.username.strip()`과 같은 사용자 경험 개선 코드를 `server2` 서비스에 적용합니다.

#### 2.1.3. 비밀번호 재설정 (`POST /forgot-password`, `POST /reset-password`)

-   **`[주요 사용자]`** 모든 사용자 (`/forgot-password`, `/reset-password`)
-   **`[서비스 분리]`** `Public (Anonymous)`
-   **`[원본] server` 엔드포인트:** `POST /forgot-password`, `POST /reset-password`
-   **`[기존] server2` 현황:** 해당 기능이 없습니다.
-   **`[핵심] 모델 차이점:** `server2`의 `User` 모델에 `reset_token`, `reset_token_expires_at` 필드가 이미 존재하여 기능 구현에 바로 사용할 수 있습니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **스키마 추가 (`accounts/schemas/token.py`):** `ForgotPasswordRequest`, `ResetPasswordRequest` Pydantic 스키마를 추가합니다.
    2.  **서비스 추가 (`account_service.py`):**
        -   `forgot_password`: 이메일을 받아 사용자를 찾고, `reset_token`을 생성/저장한 후 이메일로 발송하는 서비스 메소드를 추가합니다.
        -   `reset_password`: `reset_token`을 검증하고 새 비밀번호로 교체하는 서비스 메소드를 추가합니다.
    3.  **엔드포인트 추가 (`api/endpoints_auth.py`):** `/forgot-password` 및 `/reset-password` 엔드포인트를 추가하고, 위에서 만든 서비스 메소드를 각각 호출합니다.

### 2.2. 사용자 정보 (`User Profile`)

-   **`[대상] server2` 도메인:** `server2/app/domains/accounts`

#### 2.2.1. 현재 사용자 정보 조회 (`GET /users/me`)

-   **`[주요 사용자]`** 모든 인증된 사용자 (`/users/me`)
-   **`[서비스 분리]`** `User` (`/users/me`)
-   **`[원본] server` 엔드포인트:** `GET /me`
    ```python
@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user
    ```
-   **`[기존] server2` 현황:** `GET /users/me` 엔드포인트가 이미 존재하며, 현재 사용자의 정보를 반환합니다.
-   **`[핵심] 모델 차이점:** `server2`의 `User` 모델은 `UserOrganizationRole`과 같은 관계를 포함하여 더 많은 정보를 담고 있습니다. 또한, `server2`의 응답 스키마는 민감한 정보를 노출하지 않도록 필터링해야 합니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **스키마 검토 및 수정 (`accounts/schemas/user.py`):** `User` 응답 스키마에서 민감한 정보(`email_verification_token` 등)를 포함하지 않도록 확인 및 수정합니다.
    2.  **엔드포인트 로직 유지:** `server2`의 `GET /users/me`는 이미 `server`의 기능과 동일한 역할을 하므로, 스키마 필터링 외에 특별한 로직 변경은 필요하지 않습니다.

#### 2.2.2. 현재 사용자 정보 업데이트 (`PUT /users/me`)

-   **`[주요 사용자]`** 모든 인증된 사용자 (`/users/me`)
-   **`[서비스 분리]`** `User` (`/users/me`)
-   **`[원본] server` 엔드포인트:** `PUT /me`
    ```python
@router.put("/me", response_model=schemas.User)
def update_user_me(user_in: schemas.UserUpdate, current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user = users.update_user(db, user=current_user, user_in=user_in)
    return user
    ```
-   **`[기존] server2` 현황:** `PUT /users/me` 엔드포인트가 이미 존재하며, 현재 사용자의 정보를 업데이트합니다.
-   **`[핵심] 모델 차이점:**
    - `server`의 `UserUpdate` 스키마는 비밀번호를 포함한 다양한 필드를 업데이트할 수 있습니다. `server2`의 `UserUpdate` 스키마는 더 제한적일 수 있으며, 비밀번호 변경은 별도의 엔드포인트로 처리하는 것이 좋습니다.
    - `server2`에는 `User` 모델에 `updated_at` 필드가 있으므로, 업데이트 시 이 필드가 자동으로 갱신되는지 확인해야 합니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **스키마 검토 (`accounts/schemas/user.py`):** `UserUpdate` 스키마가 `server`와 비교하여 적절한 필드(예: `full_name`)를 포함하고 있는지 확인합니다. 비밀번호 필드는 제외해야 합니다.
    2.  **서비스 로직 개선 (`account_service.update_user`):** `server`의 로직과 같이, 입력된 데이터(`user_in`)에서 `None`이 아닌 값만 추출하여 업데이트하도록 로직을 개선합니다 (`user_in.model_dump(exclude_unset=True)`).
    3.  **별도 비밀번호 변경 엔드포인트:** `server2`에 `PUT /users/me/password`와 같은 별도의 비밀번호 변경 엔드포인트가 있는지 확인하고, 없다면 이를 새로 계획에 추가해야 합니다. (이것은 다음 단계에서 별도로 논의할 수 있습니다.)

#### 2.2.3. 현재 사용자 계정 삭제 (`DELETE /users/me`)

-   **`[주요 사용자]`** 일반 사용자 (`/users/me`)
-   **`[서비스 분리]`** `User` (`/users/me`)
-   **`[원본] server` 엔드포인트:** `DELETE /me`
    ```python
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(db: Session = Depends(get_db), current_user: models.User = Depends(PermissionChecker("user:delete:self"))):
    users.delete_user(db=db, user_id=current_user.id)
    return
    ```
-   **`[기존] server2` 현황:** 해당 기능이 없습니다.
-   **`[핵심] 모델 차이점:** `server2`의 `User` 모델에 `is_active` 필드가 존재하여 소프트 삭제(soft delete)가 가능합니다. `AUTH_ARCHITECTURE.md`에 따르면 스태프(staff) 계정은 이 API로 삭제할 수 없습니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **서비스 추가 (`account_service.py`):** `delete_self` 메소드를 추가합니다.
        -   요청한 사용자가 `is_staff=True`인지 확인하고, 스태프일 경우 에러를 발생시켜 삭제를 막습니다.
        -   일반 사용자일 경우, 해당 사용자의 `is_active` 플래그를 `False`로 설정하여 소프트 삭제합니다.
    2.  **엔드포인트 추가 (`api/endpoints_user.py`):** `DELETE /users/me` 엔드포인트가 `delete_self` 서비스를 호출하도록 합니다.

### 2.3. 기기 관리 (Device Management)

-   **`[대상] server2` 도메인:** `server2/app/domains/devices`

#### 2.3.1. 사용자 기기 목록 조회 (`GET /devices`)

-   **`[주요 사용자]`** 기기 소유자 (`/devices`), 관리자 (`/devices`)
-   **`[서비스 분리]`** `User` (`/devices`), `Admin` (`/devices`)
-   **`[원본] server` 엔드포인트:** `GET /`
    ```python
@router.get("/", response_model=List[schemas.DeviceForUser])
def read_user_devices(db: Session = Depends(get_db), current_user: models.User = Depends(PermissionChecker("device:read"))):
    user_device_links = devices.get_user_devices(db=db, user_id=current_user.id)
    # ... (logic to combine device and user-device data)
    ```
-   **`[기존] server2` 현황:** `GET /devices` 엔드포인트와 `get_multi_devices_with_auth_check` 의존성이 존재합니다. 하지만 현재 `Device` 객체 목록만 반환하며, `nickname`과 같은 사용자별 정보를 포함하지 않습니다.
-   **`[핵심] 모델 차이점:** `server`는 `user_devices` 테이블을 직접 조회하여 `nickname`을 가져옵니다. `server2`는 `Device` 모델에 `users`라는 `relationship`을 통해 `UserDevice` 객체에 접근할 수 있습니다.
-   **`[설계 근거]`**
    -   **`nickname`:** `nickname`은 특정 사용자와 기기 간의 1:1 관계에 대한 속성이므로, 연결 테이블인 `UserDevice`에 직접 필드로 추가하는 것이 정규화 및 성능 면에서 가장 효율적입니다.
    -   **`role`:** `role`은 'Owner', 'Guest'와 같이 여러 관계에서 재사용될 수 있는 정형화된 데이터입니다. 별도의 `DeviceUserRole` 테이블로 분리하고 외래 키로 참조하면, 역할의 종류가 늘어나거나 각 역할의 권한이 변경될 때 관리가 용이해지며, 이는 `server2`의 '온톨로지화된' 설계 원칙과 부합합니다. 이를 통해 향후 '가족과 기기 공유' 같은 기능을 체계적으로 확장할 수 있습니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **DB 마이그레이션 (`alembic`):**
        -   새로운 `DeviceUserRole` 모델/테이블을 생성하여 'Owner', 'Guest' 등 기기-사용자 관계의 역할을 정의합니다.
        -   `UserDevice` 모델/테이블에 `nickname: str` 필드를 추가합니다.
        -   `UserDevice` 모델/테이블에 `device_user_role_id` 외래 키 필드를 추가하여 `DeviceUserRole`을 참조하게 합니다.
    2.  **스키마 수정/추가 (`devices/schemas/device.py`):** `nickname`, `role`등 사용자-기기 연결 정보가 포함된 새로운 응답 스키마 `DeviceResponse`를 정의합니다.
    3.  **의존성 수정 (`dependencies/device_dependencies.py`):** `Device`, `UserDevice`, `DeviceUserRole` 테이블을 JOIN하여 `DeviceResponse` 스키마에 맞는 데이터를 반환하도록 로직을 수정합니다.

#### 2.3.2. 기기 별명 수정 (`PUT /{device_id}/nickname`)

-   **`[주요 사용자]`** 기기 소유자 (`/devices/{device_id}/nickname`)
-   **`[서비스 분리]`** `User` (`/devices/{device_id}/nickname`)
-   **`[원본] server` 엔드포인트:** `PUT /{device_id}/nickname`
    ```python
@router.put("/{device_id}/nickname", response_model=schemas.DeviceForUser)
def update_device_nickname_for_user(
    device_id: Annotated[int, Path()],
    nickname_in: schemas.NicknameUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="device:update"))
):
    # ... (logic to update nickname)
    ```
-   **`[기존] server2` 현황:** 해당 기능이 없습니다.
-   **`[핵심] 모델 차이점:** 이전 `GET /devices` 계획에서 `UserDevice` 테이블에 `nickname` 필드를 추가하기로 했으므로, 이 엔드포인트는 해당 필드를 업데이트하는 역할을 합니다.
-   **`[설계 근거]`**
    -   기기 별명은 기기 자체의 속성이 아니라, 특정 사용자가 특정 기기를 어떻게 부를지에 대한 '관계'의 속성입니다. 따라서 `UserDevice` 테이블에 있는 `nickname` 필드를 수정하는 것이 올바른 설계입니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **스키마 추가 (`devices/schemas/device.py`):** `NicknameUpdate` Pydantic 스키마를 추가합니다.
    2.  **서비스 추가 (`services/device_service.py`):** `update_device_nickname` 메소드를 새로 추가합니다. 이 메소드는 `user_id`와 `device_id`로 `UserDevice` 레코드를 찾아 `nickname` 필드를 업데이트합니다.
    3.  **엔드포인트 추가 (`api/endpoints_device.py`):** `PUT /devices/{device_id}/nickname` 엔드포인트를 추가하고, `update_device_nickname` 서비스 메소드를 호출합니다. '소유 기반 접근 제어' 원칙에 따라 기기 소유자만 호출할 수 있도록 의존성에서 확인해야 합니다.

#### 2.3.3. 기기 연결 해제 (`DELETE /devices/{device_id}`)

-   **`[주요 사용자]`** 기기 소유자 (`/devices/{device_id}`), 관리자 (`/devices/{device_id}`, `/admin/devices/{device_id}/deactivate`)
-   **`[서비스 분리]`** `User` (`/devices/{device_id}`), `Admin` (`/devices/{device_id}`, `/admin/devices/{device_id}/deactivate`)
-   **`[원본] server` 엔드포인트:** `DELETE /{device_id}`
    ```python
@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def unregister_device(
    device_id: Annotated[int, Path()],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="device:delete"))
):
    # ... (logic to unlink user from device)
    ```
-   **`[기존] server2` 현황:** `DELETE /devices/{device_id}` 엔드포인트가 기기 자체를 소프트 삭제하는 로직으로 구현되어 있습니다. 이는 '기기 비활성화'에 더 가깝습니다.
-   **`[핵심] 로직 분리 및 신규 규칙 적용:**
    -   '사용자와 기기의 연결을 끊는 것(Unlink)'과 '기기 자체를 시스템에서 비활성화하는 것(Deactivate)'은 다른 시나리오이므로 명확히 분리해야 합니다.
    -   **사용자 규칙:** 소유자(Owner)가 연결을 해제하면, 해당 기기에 연결된 모든 게스트(Guest)의 연결 정보(`UserDevice` 레코드)는 영구적으로(hard delete) 삭제되어야 합니다.
-   **`[설계 근거]`**
    -   소유자가 없는 기기에 게스트만 남아있는 상태는 데이터 무결성을 해칠 수 있으므로, 소유권 해제 시 종속된 모든 관계를 정리하는 것이 안전합니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **서비스 메소드 분리 및 신설 (`services/device_service.py`):**
        -   **`unlink_device_from_user` (신설):**
            -   `user_id`와 `device_id`로 `UserDevice` 레코드를 조회하여, 요청한 사용자의 역할이 'Owner'인지 확인합니다.
            -   만약 Owner라면, 해당 기기(`device_id`)에 연결된 다른 모든 `UserDevice` 레코드(Guest들)를 hard delete 합니다.
            -   마지막으로 Owner의 `UserDevice` 레코드를 삭제합니다.
            -   요청한 사용자가 Owner가 아니라면(예: Guest), 자신의 `UserDevice` 레코드만 삭제합니다.
        -   **`deactivate_device` (기존 `delete_device`에서 이름 변경):** 기기의 `is_active` 플래그를 `False`로 설정하는 기존 로직을 유지합니다. 이것은 관리자 전용 기능입니다.
    2.  **엔드포인트 매핑 수정 (`api/endpoints_device_management.py`):**
        -   `DELETE /devices/{device_id}` 엔드포인트는 `unlink_device_from_user` 서비스 메소드를 호출하도록 변경합니다.
        -   관리자용 기기 비활성화 엔드포인트(예: `DELETE /admin/devices/{device_id}/deactivate`)를 별도로 구현하여 `deactivate_device`를 호출하도록 합니다.

### 2.4. 기기 프로비저닝 (Device Provisioning)

-   **`[대상] server2` 도메인:** `server2/app/domains/devices`

#### 2.4.1. 기기 사전 등록 및 소유권 주장 (`POST /preregister`, `POST /claim`)

-   **`[주요 사용자]`** 관리자 (`/preregister`, `/claim`), 일반 사용자 (`/claim`)
-   **`[서비스 분리]`** `Admin` (`/preregister`, `/claim`), `User` (`/claim`)
-   **`[원본] server` 엔드포인트:** `POST /preregister`, `POST /claim`
    ```python
@router.post("/preregister", response_model=schemas.Device)
def preregister_device(device: schemas.DevicePreRegisterRequest, db: Session = Depends(get_db)):
    # ... (logic to create a device entry)

@router.post("/claim", response_model=schemas.DeviceForUser)
def claim_device(
    claim_request: schemas.DeviceClaimRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # ... (logic to link user and device)
    ```
-   **`[기존] server2` 현황:** 관련 기능이 전혀 없습니다.
-   **`[핵심] 모델 차이점:**
    -   `server`는 `hardware_version`을 문자열로 저장하지만, `server2`는 `hardware_blueprints` 테이블에 대한 외래 키(`hardware_blueprint_id`)를 사용해야 합니다.
    -   `server`는 기기 생성 시 `uuid`를 직접 할당하지만, `server2`는 `Device` 모델 생성 시 자동으로 UUID가 할당될 수 있습니다.
-   **`[설계 근거]`**
    -   기기 프로비저닝 과정을 '사전 등록'과 '소유권 주장'으로 분리하면, 기기 출고 및 재고 관리(관리자)와 실제 사용자 등록(사용자)의 책임을 명확히 나눌 수 있습니다.
    -   `hardware_version` 대신 `hardware_blueprint_id` 외래 키를 사용하면 하드웨어 버전 정보가 변경되거나 상세 정보가 추가될 때 관리가 용이해지며, 데이터의 정합성을 보장합니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **스키마 추가 (`devices/schemas/provisioning.py`):** `DevicePreRegisterRequest`, `DeviceClaimRequest` Pydantic 스키마를 추가합니다.
    2.  **서비스 추가 (`services/device_provisioning_service.py`):** 프로비저닝 관련 로직을 별도 서비스 파일로 분리하는 것을 고려합니다.
        -   `preregister_device`: 관리자만 호출 가능. `cpu_serial`과 `hardware_blueprint_version`을 받아 `hardware_blueprints` 테이블에서 ID를 조회한 후, `devices` 테이블에 `is_active=False` 및 `is_claimed=False` 상태로 새 레코드를 생성합니다.
        -   `claim_device`: 인증된 사용자(User 또는 Admin)가 호출. `cpu_serial`로 사전 등록된 기기를 찾아, 요청한 사용자와 `UserDevice` 테이블을 통해 'Owner' 역할로 연결합니다. 기기의 `is_active` 및 `is_claimed` 상태를 `True`로 변경합니다.
    3.  **엔드포인트 추가 (`api/endpoints_provisioning.py`):** `/preregister` 및 `/claim` 엔드포인트를 새로 추가하고, 각각의 서비스 메소드를 호출합니다.

### 2.5. 데이터 조회 및 명령 (Data Retrieval & Commands)

#### 2.5.1. 기기 명령 전송 (`POST /devices/{device_id}/command`)

-   **`[주요 사용자]`** 기기 소유자 (`/devices/{device_id}/command`), 관리자 (`/devices/{device_id}/command`)
-   **`[서비스 분리]`** `User` (`/devices/{device_id}/command`), `Admin` (`/devices/{device_id}/command`)
-   **`[원본] server` 엔드포인트:** `POST /{device_id}/command`
    ```python
@router.post("/{device_id}/command")
def send_device_command(
    device_id: Annotated[int, Path()],
    command: schemas.DeviceCommand,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(DeviceAccessChecker(required_permission="command:send"))
):
    # ... (logic to build MQTT topic and publish command)
    ```
-   **`[기존] server2` 현황:** `devices` 도메인에 명령 전송 기능이 없습니다.
-   **`[핵심] 모델 차이점:**
    -   `server2`는 `Device` 모델을 통해 `current_uuid`에 접근하며, `User` 모델을 통해 `email`을 가져올 수 있습니다.
    -   MQTT 관련 유틸리티는 `server2/app/mqtt`에 별도로 존재합니다.
-   **`[설계 근거]`**
    -   기기에 명령을 전송하는 기능은 기기 제어의 핵심이며, '소유 기반 접근 제어' 원칙에 따라 기기 소유자 또는 관리자에게만 허용되어야 합니다.
    -   MQTT를 통한 비동기 명령 전송은 시스템 확장성과 효율성을 높이며, `server2`의 기존 MQTT 인프라를 활용합니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **스키마 추가 (`devices/schemas/command.py` 또는 `devices/schemas/device.py`):** `DeviceCommand` Pydantic 스키마를 추가합니다. (예: `component: str`, `action: str`, `duration_seconds: Optional[int]`)
    2.  **서비스 추가 (`services/device_command_service.py` 또는 `services/device_service.py`):** `send_command` 메소드를 구현합니다. 이 메소드는 `device_id`, `command` 스키마, `current_user`를 받아 MQTT 토픽을 구성하고 메시지를 발행합니다.
    3.  **엔드포인트 추가 (`api/endpoints_command.py` 또는 `api/endpoints_device_management.py`):** `POST /devices/{device_id}/command` 엔드포인트를 추가하고, 위에서 만든 서비스 메소드를 호출합니다. '소유 기반 접근 제어' 및 '역할 기반 권한 검증' 원칙에 따라 권한을 확인해야 합니다.

#### 2.5.2. 텔레메트리 데이터 조회 (`GET /{device_id}/telemetry`)

-   **`[주요 사용자]`** 기기 소유자 (`/devices/{device_id}/telemetry`), 관리자 (`/devices/{device_id}/telemetry`)
-   **`[서비스 분리]`** `User` (`/devices/{device_id}/telemetry`), `Admin` (`/devices/{device_id}/telemetry`)
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
    # ... (logic to get telemetry data and filter payload)
    ```
-   **`[기존] server2` 현황:** `data` 도메인은 아직 리팩토링되지 않았습니다. `server2`의 `TelemetryData` 모델이 존재합니다.
-   **`[핵심] 모델 차이점:**
    -   `server`는 `telemetry` CRUD에서 데이터를 조회합니다.
    -   `server2`는 `TelemetryData` 모델을 사용하며, `device_id`는 외래 키입니다.
    -   `server`의 `filter_telemetry_payload`는 `server2`의 `data` 도메인으로 옮겨져야 합니다.
-   **`[설계 근거]`**
    -   텔레메트리 데이터는 기기의 민감한 정보를 포함할 수 있으므로, '소유 기반 접근 제어' 원칙에 따라 기기 소유자 또는 관리자에게만 접근이 허용되어야 합니다.
    -   `server2`의 `data` 도메인으로 이관하여 데이터 관련 로직을 한 곳으로 집중시켜 관리 효율성을 높입니다.
    -   **데이터 무결성 및 불변성 (Data Integrity & Immutability):** 기기로부터 수신된 텔레메트리 데이터는 '진실의 원천(source of truth)'으로 간주된다. 데이터 무결성을 위해, 이 데이터는 API를 통해 **생성, 수정, 삭제가 절대 불가**하며, 오직 읽기만 허용된다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **`data` 도메인 리팩토링:** `data` 도메인을 `accounts`와 유사한 방식으로 먼저 리팩토링합니다. `data_crud.py`, `data_service.py`, `data_dependencies.py`를 생성하고 `schemas`를 분리합니다.
    2.  **서비스 추가 (`data_service.py`):** `get_telemetry_data` 메소드를 구현하여 `TelemetryData` 모델을 사용하여 데이터를 조회합니다. `filter_telemetry_payload` 로직도 이 서비스로 옮깁니다.
    3.  **의존성 추가 (`data_dependencies.py`):** `get_telemetry_data_dependency`와 같이 텔레메트리 데이터 조회를 위한 의존성을 구현합니다. 이는 권한 확인과 필터링 파라미터 처리를 담당합니다.
    4.  **엔드포인트 추가 (`data/api/endpoints_telemetry.py`):** `GET /{device_id}/telemetry` 엔드포인트를 추가하고, 새로 만든 서비스 및 의존성을 사용합니다.

### 2.6. 펌웨어 OTA (Firmware OTA)

-   **`[대상] server2` 도메인:** `server2/app/domains/firmware`

#### 2.6.1. OTA 업데이트 명령 (`PUT /devices/{device_id}/ota`)

-   **`[주요 사용자]`** 관리자 (`/devices/{device_id}/ota`)
-   **`[서비스 분리]`** `Admin` (`/devices/{device_id}/ota`)
-   **`[원본] server` 엔드포인트:** `PUT /{device_id}/ota`
    ```python
@router.put("/{device_id}/ota", response_model=schemas.Device)
def trigger_ota_update(
    device_id: int,
    ota_request: schemas.OtaRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # ... (logic to create firmware update record and publish MQTT message)
    ```
-   **`[기존] server2` 현황:** `firmware` 도메인은 아직 리팩토링되지 않았습니다. `FirmwareUpdate` 및 `Firmware` 모델이 존재합니다.
-   **`[핵심] 모델 차이점:**
    -   `server`는 `firmware_updates` 테이블을 직접 업데이트합니다.
    -   `server2`는 `FirmwareUpdate` 모델을 사용하여 OTA 상태를 추적해야 합니다.
    -   MQTT 관련 유틸리티는 `server2/app/mqtt`에 있습니다.
-   **`[설계 근거]`**
    -   OTA 업데이트는 기기의 안정성에 큰 영향을 미치므로, 오직 관리자만 이 기능을 사용할 수 있도록 제한해야 합니다.
    -   `FirmwareUpdate` 테이블을 통해 OTA 상태를 추적하면, 업데이트 성공 여부, 재시도 횟수 등을 관리할 수 있어 안정성이 향상됩니다.
-   **`[계획] 마이그레이션 전략:`**
    1.  **`firmware` 도메인 리팩토링:** `firmware` 도메인을 `accounts`와 유사한 방식으로 먼저 리팩토링합니다. (`firmware_crud.py`, `firmware_service.py` 등)
    2.  **스키마 추가 (`firmware/schemas/ota.py`):** `OTAUpdateRequest` Pydantic 스키마를 추가합니다. (예: `firmware_id: int`)
    3.  **서비스 추가 (`firmware/services/ota_service.py`):** `request_ota_update` 메소드를 구현합니다. 이 메소드는 `FirmwareUpdate` 테이블에 OTA 요청 레코드를 생성하고, MQTT를 통해 기기에 OTA 명령을 전송합니다.
    4.  **엔드포인트 추가 (`firmware/api/endpoints_ota.py`):** `PUT /devices/{device_id}/ota` 엔드포인트를 추가하고, `ota_service.request_ota_update`를 호출하도록 구현합니다. `역할 기반 권한 검증`에 따라 관리자 권한을 확인해야 합니다.