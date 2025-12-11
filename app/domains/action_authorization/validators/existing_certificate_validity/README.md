# `ExistingCertificateValidityValidator`

## 1. 개요 (Overview)
이 Validator는 MQTT 클라이언트 (Publisher 또는 Listener)가 현재 가지고 있는 인증서 데이터의 유효성을 검사합니다. 특히 인증서의 만료 시각(expiration date)이 현재 시각을 기준으로 미리 설정된 임계값(예: 1시간) 내로 임박했는지 여부를 판단하여, 인증서 갱신이 필요한지 여부를 결정하는 데 사용됩니다.

## 2. 역할 및 책임 (Role & Responsibility)
-   입력된 인증서 데이터(`IssuedCertificateRead` 스키마에 해당하는 딕셔너리)의 구조가 유효한지 확인합니다.
-   인증서의 만료 시각을 파싱하여 현재 시각과 비교합니다.
-   인증서가 이미 만료되었는지, 또는 만료 임박 임계값 내에 있는지 판단합니다.
-   판단 결과(유효성 여부)와 필요시 에러 메시지를 반환합니다.

## 3. 사용처 (Usage)
-   `ServerCertificateAcquisitionPolicy`와 같은 Policy에서, 기존 인증서를 계속 사용할지 아니면 새로운 인증서를 발급받아야 할지 결정하는 '판단' 로직의 핵심 컴포넌트로 사용됩니다.

## 4. 향후 개선 방향 (Future Improvements)
-   현재 이 Validator는 인증서 데이터의 '존재 여부'와 '만료 기간'을 모두 확인하고 있습니다. 이는 '사용 적합성'이라는 단일 책임으로 볼 수 있습니다.
-   하지만 만약 이 Validator의 로직이 미래에 더 복잡해진다면, SRP(단일 책임 원칙)를 더욱 엄격하게 적용하기 위해 다음과 같이 두 개의 Validator로 분리하는 것을 고려할 수 있습니다:
    -   `CertificateDataExistenceValidator`: 데이터 존재 여부 및 기본 구조만 확인.
    -   `CertificateExpirationValidator`: 만료 기간만 확인.
