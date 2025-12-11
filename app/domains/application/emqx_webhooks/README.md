# EMQX Webhooks Application

## 목적
이 Application은 EMQX HTTP 플러그인으로부터 오는 인증(Authentication) 및 인가(Authorization/ACL) 웹훅 요청을 수신하고 처리하는 HTTP 엔드포인트를 제공합니다.

## 책임
- HTTP 요청/응답 처리: EMQX가 보내는 `POST` 요청의 Body를 파싱하고, 정해진 형식에 따라 `allow` 또는 `deny`를 포함한 JSON 응답을 반환합니다.
- 비즈니스 로직 위임: 실제 인증/인가에 대한 결정은 직접 처리하지 않고, `inter_domain` provider를 통해 `action_authorization` 도메인의 `Policy` 계층으로 위임합니다.
