# Certificate Management Service Domain

## 1. 목적 (Purpose)

이 `certificate_management` 서비스 도메인은 시스템 내 모든 종류의 인증서(장치 인증서, CA 인증서 등)의 전체 생명주기를 관리하는 책임을 가집니다.

---

## 2. 핵심 아키텍처 (Core Architecture)

이 서비스는 유연성과 확장성을 위해 두 가지 핵심 패턴 위에 구축되었습니다.

### 2.1. 리포지토리 패턴 (Repository Pattern)

인증서가 실제 저장되는 위치(DB, Vault 등)에 서비스 계층이 종속되지 않도록, 데이터 저장 계층을 추상화하는 리포지토리 패턴을 사용합니다.

-   **`repositories/`**: 이 디렉토리 안에 실제 저장소와 통신하는 구현체들이 위치합니다.
    -   `vault_certificate_repository.py`: Vault의 PKI 엔진과 통신하여 실제 인증서를 생성, 폐기, **그리고 민감한 원본(예: 개인 키)을 조회**하는 역할을 담당합니다.
    -   `db_certificate_repository.py`: 발급된 인증서의 메타데이터(이름, 발급자, 만료일 등)를 애플리케이션 데이터베이스에 저장하고 조회하는 역할을 담당합니다.

### 2.2. CQRS (Command Query Responsibility Segregation)

서비스의 책임을 '상태를 변경하는 명령(Command)'과 '상태를 조회하는 조회(Query)'로 명확히 분리합니다.

-   **`services/certificate_command_service.py`**: 인증서를 생성하거나 폐기하는 등의 '명령' 책임을 가집니다. 이 서비스는 `VaultCertificateRepository`와 `DatabaseCertificateRepository`를 모두 사용하여, Vault에서 인증서를 생성한 후 그 결과를 DB에 저장하는 것과 같은 복합적인 작업을 조율(Orchestrate)합니다.
-   **`services/certificate_query_service.py`**: 데이터베이스에 저장된 인증서 메타데이터를 조회하는 책임을 가집니다. 이 서비스는 `DatabaseCertificateRepository`에만 의존합니다. **또한, 필요 시 Vault에 저장된 인증서 원본(개인 키 등)을 조회하는 책임도 가집니다.** 이 기능은 `VaultCertificateRepository`에 의존하며, 매우 엄격한 `Policy`에 의해서만 호출이 허용되어야 하는 민감한 작업입니다.

---

## 3. 기본 흐름: 인증서 생성 (Primary Flow: Certificate Creation)

`CertificateCommandService`는 다음과 같은 순서로 두 리포지토리를 조율하여 인증서를 생성합니다.

1.  `VaultCertificateRepository`를 호출하여 Vault로부터 실제 인증서(`private_key`, `certificate`)를 발급받습니다.
2.  `DatabaseCertificateRepository`를 호출하여 발급된 인증서의 공개 정보 및 메타데이터(예: `certificate_name`, `certificate_content`)를 애플리케이션 DB에 저장합니다.

---

## 4. 향후 목적 및 확장성 (Future Purpose & Scalability)

이 아키텍처의 주된 목적은 **보안성과 확장성**입니다.

현재는 모든 인증서 정보를 데이터베이스에만 저장할 수도 있지만, 이 구조는 향후 수백만 개의 장치 인증서를 관리해야 하는 프로덕션 환경을 대비하여 설계되었습니다.

미래에는 `CertificateCommandService`가 `VaultCertificateRepository`를 호출하여 각 장치마다 고유한 인증서를 동적으로 발급하고, 이 인증서의 공개 정보와 메타데이터만 `DatabaseCertificateRepository`를 통해 DB에 저장하게 될 것입니다. 서비스 계층의 코드는 그대로 유지된 채 리포지토리의 내부 구현만 변경하면 되므로, 서비스의 중단이나 큰 수정 없이 저장소 백엔드를 손쉽게 Vault로 확장할 수 있습니다.

---

## 5. 향후 확장 방향: 이벤트 발행 (Future Expansion: Event Publishing)

이 아키텍처는 Google Cloud Pub/Sub과 같은 외부 메시징 시스템과의 연동을 손쉽게 지원합니다. 예를 들어, 인증서가 발급되거나 폐기될 때마다 관련 이벤트를 발행해야 한다는 새로운 요구사항이 생길 경우, 다음과 같이 확장할 수 있습니다.

1.  Pub/Sub 메시지 발행을 책임지는 `GooglePubSubProvider`(가칭)를 생성합니다.
2.  `CertificateCommandService`의 메소드 내부 로직을 수정합니다.

```python
# services/certificate_command_service.py

class CertificateCommandService:
    def create_device_certificate(self, db: Session, *, common_name: str) -> Certificate:
        # 1. Vault에서 인증서 발급
        vault_cert_data = vault_certificate_repository.create_device_certificate(...)
        
        # 2. DB에 메타데이터 저장
        db_certificate = db_certificate_repository.create(...)

        # 3. (추가된 책임) Pub/Sub으로 이벤트 발행
        google_pub_sub_provider.publish(
            topic="certificate_events", 
            message={"event": "certificate_created", "certificate_id": db_certificate.id}
        )
        
        return db_certificate
```

위와 같이, `Service` 계층이 오케스트레이터(Orchestrator) 역할을 하므로, 기존 구조를 변경하지 않고 새로운 책임을 자연스럽게 추가하여 확장할 수 있습니다.
