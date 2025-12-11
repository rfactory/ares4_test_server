# 사용자-조직-역할 연결 검증기 (User-Organization-Role Link Validator)

## 목적
이 검증기는 특정 사용자가 특정 조직 내에서 **요청된 특정 역할**을 이미 가지고 있는지 확인하는 단일 책임을 가집니다. 이는 사용자가 동일한 역할에 대해 중복된 요청을 하거나, 이미 할당된 역할을 재요청하는 것을 방지합니다.

## 검증 로직
1.  주어진 `user.id`, `organization.id`, `requested_role_id`를 사용하여 `UserOrganizationRole` 모델을 조회합니다.
2.  해당 조합의 관계 레코드가 존재하면, 사용자가 이미 해당 역할을 가지고 있으므로 `(False, 에러 메시지)`를 반환합니다.
3.  관계 레코드가 존재하지 않으면, `(True, None)`을 반환하여 검증을 통과시킵니다.

## 참고
-   이 검증기는 `organization_id`가 `NULL`인 시스템 역할에 대한 연결은 확인하지 않습니다. 오직 특정 조직과의 연결 여부만 확인합니다.
-   `policy` 계층에서 `user`와 `organization` 객체 및 `requested_role_id`가 유효하게 제공될 때 사용되어야 합니다.