# Organization Type Existence Validator

이 Validator는 제공된 `organization_type_id`가 데이터베이스에 실제로 존재하는 유효한 조직 유형인지를 검증합니다.

## 로직

1.  `inter_domain`의 `organization_query_provider`를 사용하여 주어진 `id`로 조직 유형을 조회합니다.
2.  조회된 조직 유형이 **있으면** (유효하면), `True`를 반환합니다.
3.  조회된 조직 유형이 **없으면** (유효하지 않으면), `False`를 반환합니다.
