# Blueprint Compatibility Validator

## 목적
이 검증기는 특정 부품(supported component)이 주어진 하드웨어 청사진에 대해 유효한지를 확인하는 단일 책임을 가집니다.

## 검증 로직
1.  `hardware_blueprint_query_providers`를 통해 특정 블루프린트 ID에 연결될 수 있는 모든 유효 부품 ID의 목록을 조회합니다.
2.  검증하려는 부품의 ID가 이 목록에 포함되어 있는지 확인합니다.