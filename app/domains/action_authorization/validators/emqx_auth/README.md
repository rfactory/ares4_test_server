# EMQX 인증/권한 검증기 (EMQX Auth Validator)

## 목적
이 검증기는 EMQX 브로커가 HTTP 웹훅을 통해 전달하는 인증(Authentication) 및 인가(Authorization, ACL) 요청에 대한 개별 규칙들을 판별하는 책임을 가집니다.

## 검증 로직

### 1. 슈퍼유저 판별 (`is_superuser`)
-   주어진 `username` 또는 `client_id`가 시스템에 정의된 슈퍼유저 규칙과 일치하는지 확인합니다.
-   슈퍼유저로 판별되면 `True`를 반환하며, `Policy` 계층은 이 결과를 바탕으로 모든 토픽에 대한 접근을 허용할 수 있습니다.

### 2. 토픽 접근 판별 (`can_access_topic`)
-   데이터베이스에서 조회된 특정 사용자의 ACL 규칙(`rule_topic`)과, 실제 접근하려는 토픽(`actual_topic`)을 비교합니다.
-   MQTT 토픽 와일드카드(+, #)를 지원하는 규칙에 따라, 접근이 허용되면 `True`, 그렇지 않으면 `False`를 반환합니다.

## 참고
-   이 Validator는 최종적인 "allow" 또는 "deny" 결정을 내리지 않습니다. 오직 주어진 규칙에 대한 `True/False` 판별 결과만 반환합니다.
-   최종 결정은 `Policy` 계층에서 이 Validator의 결과를 조합하여 내립니다.
