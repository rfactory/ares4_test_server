# 중복 접근 요청 검증기 (Duplicate Permission Request Validator)

## 목적
이 검증기는 동일한 조건의 보류 중인(pending) 접근 요청이 시스템에 이미 존재하는지 확인하는 단일 책임을 가집니다. 이는 불필요하거나 중복된 요청이 처리되는 것을 방지합니다.

## 검증 로직
1.  주어진 `user_id`, `requested_role_id`, `organization_id` (시스템 역할 요청 시 `NULL`) 및 `status='pending'` 조건을 사용하여 `AccessRequest` 테이블을 조회합니다.
2.  이 조건들을 모두 만족하는 레코드가 존재하면, 이미 동일한 요청이 보류 중이므로 `(False, 에러 메시지)`를 반환합니다.
3.  일치하는 레코드가 없으면, `(True, None)`을 반환하여 검증을 통과시킵니다.

## 사용 범위
-   시스템 관리자 역할 요청
-   특정 기업/조직 내 역할 요청

두 경우 모두 `organization_id`의 값(NULL 또는 특정 ID)에 따라 적절하게 중복 요청 여부를 확인합니다.