# 조직 존재 여부 검증기 (Organization Existence Validator)

## 목적
이 검증기는 주어진 사업자 등록 번호(`business_registration_number`)를 가진 조직이 시스템에 이미 등록되어 있는지 확인하는 단일 책임을 가집니다.

## 검증 로직
1.  `organization_providers`를 통해 특정 사업자 등록 번호를 가진 조직을 데이터베이스에서 조회합니다.
2.  조직이 존재하면 `(True, organization_object)`를 반환합니다.
3.  조직이 존재하지 않으면 `(False, None)`을 반환하고, 경고 로그를 남깁니다.