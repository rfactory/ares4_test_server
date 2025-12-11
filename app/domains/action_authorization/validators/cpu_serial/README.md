# CPU 시리얼 검증기 (CPU Serial Validator)

## 목적
이 검증기는 전달받은 장치(`DeviceRead`) 객체의 `cpu_serial`과 페이로드(`payload`)에 포함된 `cpu_serial`이 일치하는지 확인하는 단일 책임을 가집니다. 이는 SD 카드 복제/교체 공격을 방지하기 위한 중요한 보안 검증 단계입니다.

## 검증 로직
1.  `payload`에서 `cpu_serial` 값을 가져옵니다.
2.  `device` 객체의 `cpu_serial` 값과 비교합니다.
3.  두 값이 일치하지 않으면 `(False, 에러 메시지)`를 반환하고, 심각한 보안 경고 로그를 남깁니다.
4.  두 값이 일치하면 `(True, None)`을 반환하여 검증을 통과시킵니다.