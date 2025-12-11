# 장치 존재 여부 검증기 (Device Existence Validator)

## 목적
이 검증기는 주어진 UUID를 가진 장치가 시스템에 존재하는지 확인하는 단일 책임을 가집니다.

## 검증 로직
1.  `device_management_query_provider`를 통해 특정 UUID에 해당하는 장치를 데이터베이스에서 조회합니다.
2.  장치가 존재하면 `(True, device_object)`를 반환하여, Policy 계층에서 해당 장치 객체를 재사용할 수 있도록 합니다.
3.  장치가 존재하지 않으면 `(False, None)`을 반환합니다.