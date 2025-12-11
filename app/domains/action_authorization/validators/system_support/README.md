# 시스템 지원 검증기

## 목적
이 검증기는 주어진 컴포넌트 타입이 시스템에서 공식적으로 인식되고 지원되는지 확인하는 역할을 담당합니다. `supported_components`의 마스터 카탈로그를 확인하여 알려지고 유효한 컴포넌트 타입만 처리되도록 보장합니다.

## 책임
- **컴포넌트 타입 인식**: `component_type`이 시스템의 `supported_components` 마스터 목록에 존재하는지 검증합니다.

## 내용
- `validator.py`: 이 검사를 구현하는 `SystemSupportValidator` 클래스를 포함합니다.