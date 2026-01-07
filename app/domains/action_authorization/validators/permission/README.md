# Permission Validator

이 Validator는 `app.core.authorization` 모듈의 `check_user_permission` 함수를 사용하여, 특정 사용자가 주어진 컨텍스트(조직 ID) 내에서 특정 권한(`permission_name`)을 가지고 있는지 확인합니다.

## 로직

1.  `authorization.check_user_permission` 함수를 호출하여 권한을 확인합니다.
2.  사용자가 해당 권한을 가지고 있으면 `(True, None)`을 반환합니다.
3.  권한이 없으면 `(False, error_message)`를 반환합니다.

## 사용 예시

`Policy` 계층에서 특정 작업을 수행하기 전에 사용자 권한을 검사할 때 사용됩니다.
