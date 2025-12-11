# EMQX 인증/인가 정책 (EMQX Auth Policy)

## 목적
이 Policy는 EMQX 브로커로부터 오는 인증(auth) 및 인가(acl) 웹훅 요청에 대한 최종 결정을 내리는 책임을 가집니다.

## 로직 흐름

### 1. 인증 (`handle_auth`)
1.  `inter_domain`을 통해 `user_identity_provider`를 호출하여 요청된 `username`에 해당하는 사용자 정보가 있는지 확인합니다.
2.  사용자가 존재하면, 제공된 `password`가 저장된 해시값과 일치하는지 검증합니다.
3.  모든 과정이 성공하면 `True`를, 그렇지 않으면 `False`를 반환합니다.

### 2. 인가 (`handle_acl`)
1.  `inter_domain`을 통해 `emqx_auth_validator`를 호출하여 해당 사용자/클라이언트가 슈퍼유저인지 먼저 확인합니다.
2.  슈퍼유저가 아니라면, 필요한 ACL 규칙을 `inter_domain`을 통해 관련 서비스에서 조회합니다. (현재는 정적 규칙 사용)
3.  조회된 규칙과 요청된 `topic`을 `emqx_auth_validator`의 `can_access_topic` 함수로 넘겨 최종 접근 가능 여부를 판별합니다.
4.  결과에 따라 `True`(허용) 또는 `False`(거부)를 반환합니다.

## 참고
-   이 Policy는 실제 비즈니스 로직(예: DB 조회)을 수행하지 않으며, 여러 Validator와 Service의 결과를 조합하여 최종 결정을 내리는 "뇌"의 역할을 합니다.
