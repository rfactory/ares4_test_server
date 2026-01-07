# Organization Business Registration Uniqueness Validator

이 Validator는 제공된 사업자 등록 번호(`business_registration_number`)가 데이터베이스에 이미 존재하는지 확인하여, 조직의 사업자 등록 번호가 유일한지(unique)를 검증합니다.

## 로직

1.  `inter_domain`의 `organization_query_provider`를 사용하여 주어진 사업자 등록 번호로 조직을 조회합니다.
2.  조회된 조직이 **없으면** (유니크하면), `True`를 반환합니다.
3.  조회된 조직이 **있으면** (중복되면), `False`를 반환합니다.
