# Ares4 Immutable Fortress Architecture (Design Blueprint)

Ares4 프로젝트의 보안 및 프로비저닝 아키텍처 가이드라인입니다. 하드웨어 양산 효율성과 강력한 보안 성능 확보를 목표로 합니다.

## 1. 파티션 설계 (Storage Partitioning)
전체 저장 공간을 3가지 구역으로 분리하여 OS의 불변성과 데이터의 연속성을 동시에 확보합니다.

* **Partition A & B (Immutable RootFS)**
    * **상태**: Read-Only (콘크리트 봉인).
    * **내용**: 리눅스 커널, 시스템 라이브러리, 도커 엔진(Docker Engine).
    * **운용**: A/B 듀얼 뱅크 구조. OTA 업데이트 시 새로운 OS 이미지를 통째로 교체하며 상호 백업 역할을 수행합니다.
* **Partition C (Persistent Data Store)**
    * **상태**: Read-Write (쓰기 가능 구역).
    * **내용**: 기기 고유 신분증(`identity.json`), mTLS 인증서, 도커 이미지(MSA 서비스 코드), 시스템 로그.
    * **특징**: OS가 업데이트(A↔B 전환)되어도 이 영역의 데이터는 유지됩니다.

## 2. 공장 프로비저닝 (Factory Provisioning)
사람의 개입을 최소화하고 보안을 극대화한 자동화 등록 방식입니다.

* **골든 이미지 (Golden Image)**: 부트로더와 도커 환경이 세팅된 '박제된 이미지'를 대량 복제하여 SD 카드에 굽습니다.
* **자기 파괴형 부트로더 (Self-Destruct Bootloader)**:
    1.  기기가 공장에서 처음 켜질 때 실행되는 1회성 `root` 프로세스입니다.
    2.  하드웨어 CPU 시리얼을 읽어 서버의 공장 전용 엔드포인트에 전달합니다.
    3.  서버는 공장 내부 IP 화이트리스트를 통해 승인된 장소인지 확인 후 UUID와 초기 인증서를 발급합니다.
    4.  등록을 마친 부트로더는 신분증을 **Partition C**에 봉인한 뒤, 자신의 소스 코드와 서비스를 영구 삭제합니다.

## 3. 현장 클레임 및 운용 (Field Claim & MSA)
* **BLE Provisioning**: 설치 기사가 모바일 앱(블루투스)으로 접속하여 현장 Wi-Fi 정보를 주입하고 서버에 해당 기기를 클레임(Claim)합니다.
* **MSA Orchestration**: 서버는 기기의 UUID를 확인하고 해당 위치에 맞는 도커 이미지(설계도)를 할당합니다.
* **Identity Sanctum**: 발급받은 신분증은 `root` 권한으로도 수정 불가능하도록 Immutable Bit (`chattr +i`) 처리되어 물리적/네트워크 침입으로부터 보호됩니다.

## 4. 보안 철학 (Security Philosophy)
* **공간의 봉인**: 계정 권한이 뚫리더라도 발을 딛고 있는 '공간(RootFS)'이 콘크리트(Read-Only)라 시스템 변조가 불가능합니다.
* **최소 노출**: 부트로더는 태어날 때만 존재하고 사라지며, 평상시에는 오직 필요한 데이터만 도커에 '읽기 전용'으로 제공됩니다.
* **신뢰 체인**: 기존 인증서로 암호화된 채널이 형성되어야만 새로운 인증서 교체가 가능한 mTLS 구조를 유지합니다.