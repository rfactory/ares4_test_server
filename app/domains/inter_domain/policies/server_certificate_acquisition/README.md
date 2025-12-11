# `ServerCertificateAcquisitionPolicyProvider`

## 1. 개요 (Overview)
이 Provider는 `ServerCertificateAcquisitionPolicy`의 기능을 외부에 노출하는 인터페이스입니다. Policy가 단일 책임 원칙에 따라 하나의 비즈니스 워크플로우를 캡슐화하므로, Provider는 이 Policy의 메서드를 직접 호출하여 그 기능을 필요로 하는 다른 도메인이나 애플리케이션 계층에 제공합니다.

## 2. 역할 및 책임 (Role & Responsibility)
-   `ServerCertificateAcquisitionPolicy` 인스턴스를 직접 import합니다.
-   `acquire_valid_server_certificate`와 같은 Policy의 핵심 메서드들을 외부에 노출합니다.
-   Policy의 내부 구현 세부 사항을 호출자로부터 숨기고, 안정적인 호출 인터페이스를 제공합니다.

## 3. 사용처 (Usage)
-   `ServerMqttClientLifecyclePolicy`와 같은 상위 Policy에서 서버가 사용할 유효한 인증서를 획득하기 위해 호출됩니다.
