# Device Attachment Validator

## 목적
이 검증기는 특정 부품(supported component)이 특정 장치에 연결되도록 사용자가 설정했는지 확인하는 단일 책임을 가집니다.

## 검증 로직
1.  `device_component_instance_crud`를 통해 `device_id`와 `supported_component_id`에 해당하는 연결 인스턴스(component instance)가 데이터베이스에 존재하는지 조회합니다.
2.  해당 인스턴스가 존재하지 않으면 검증에 실패합니다.