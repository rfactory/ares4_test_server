# Hmac Integrity Validator

## 목적 (Purpose)
이 Validator는 메시지의 '무결성'을 검증하는 단일 책임을 가집니다. '무결성'이란, '메시지 내용이 위변조되지 않았음'을 암호학적으로 증명하는 것을 의미합니다.

## Validation Steps
HMAC 서명 검증은 Vault Transit Engine을 통해 수행됩니다.
1.  페이로드에서 HMAC 서명을 추출합니다.
2.  HMAC 검증 대상 페이로드(HMAC 필드 제외)를 준비합니다.
3.  `hmac_query_provider`를 통해 Vault에 검증을 위임하고, 결과를 받습니다.

## Inputs
- `db: Session`: 데이터베이스 세션 (Provider에게 전달됨).
- `device: DeviceWithSecret`: 미리 조회된, `hmac_key_name`을 포함해야 하는 기기의 Pydantic 스키마 객체.
- `payload: dict`: `hmac` 서명이 포함될 것으로 예상되는 메시지 페이로드.

## Output
- `Tuple[bool, Optional[str]]`: 메시지가 무결하면 `(True, None)`을, 그렇지 않으면 `(False, "오류 메시지")`를 반환합니다.

## Architectural Principle
이 Validator는 "신경" 원칙을 구현합니다. 특정하고 원자적인 검사를 수행하고, 데이터가 아닌 '판단'(`True` 또는 `False`)만 반환합니다. `Policy` 계층은 `device` 객체를 가져오고 이 Validator를 호출하는 오케스트레이션 책임을 집니다.
