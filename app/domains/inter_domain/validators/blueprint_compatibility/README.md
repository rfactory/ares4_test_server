# Blueprint Compatibility Validator Provider

## 목적 (Purpose)
이 Provider는 `BlueprintCompatibilityValidator`의 기능을 다른 도메인(특히 Policy 계층)에 노출합니다.

## 제공되는 메서드 (Provided Methods)
- `validate(db: Session, blueprint_id: int, supported_component_id: int) -> Tuple[bool, Optional[str]]`
  - 특정 부품이 하드웨어 청사진과 호환되는지 검증합니다.

## 아키텍처 원칙 (Architectural Principle)
이 Provider는 "도메인 내부 Provider" 원칙을 준수합니다. `BlueprintCompatibilityValidator`가 이를 호출하는 Policy와 동일한 `action_authorization` 도메인에 속하더라도, 모든 컴포넌트 간 상호 작용에서 느슨한 결합과 아키텍처 일관성을 강화하기 위해 이 Provider를 통해 통신이 중재됩니다.
