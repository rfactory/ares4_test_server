# Ares4 Security Architecture Specification v1.1

**Project Name:** Ares4 Smart Farm IoT  
**Version:** 1.1 (Revised)  
**Status:** Approved Draft  
**Author:** Daniel & Gemini  

---

## 1. 개요 (Overview)
본 문서는 Ares4 스마트팜 IoT 시스템의 보안 인증, 키 관리, 재해 복구 및 단말 위변조 방지 기술을 정의한다. 본 아키텍처는 다음 3대 원칙을 기반으로 설계되었다.

1.  **Zero Trust**: 아무도 믿지 않는다 (서버도, 기기도 검증 대상).
2.  **Air-Gap**: 최상위 권한(Root)은 인터넷과 물리적으로 분리한다.
3.  **Hardware Binding**: 소프트웨어는 특정 하드웨어에서만 동작한다.

---

## 2. 키 관리 체계 (PKI Hierarchy)

시스템은 **통신용(Operational)**과 **관리용(Management)** 채널을 엄격히 분리하여 운영한다.

### 2.1. 통신용 체계 (Operational Channel - TLS/MQTT)
기기의 일상적인 데이터 전송 및 제어를 담당한다.

| 키(Key) | 위치 | 형태 | 역할 및 특징 |
| :--- | :--- | :--- | :--- |
| **Root CA (A)** | **Offline USB** | Private Key | 최상위 신뢰 구간. Intermediate CA 서명용. **절대 인터넷 연결 불가.** |
| **Intermediate CA** | **Cloud Vault** | Private Key | 기기 인증서(Device Cert) 발급 담당. **CSR 방식**으로 생성(Vault 내부 생성 → Root 서명). |
| **Device Key** | **Raspberry Pi** | Private Key | mTLS 상호 인증용. 기기 내부에서 생성 및 암호화 저장. |

### 2.2. 관리/복구용 체계 (Management Channel - Firmware/Bootstrap)
기기의 생명주기 관리 및 비상 복구를 담당한다.

| 키(Key) | 위치 | 형태 | 역할 및 특징 |
| :--- | :--- | :--- | :--- |
| **Master Key (B)** | **Offline USB** | Private Key | 펌웨어 **코드 서명(Code Signing)**용. 시스템 전체를 리셋할 수 있는 'God Mode' 권한. |
| **Bootstrap Key** | **Raspberry Pi** | Private Key | 기기 출하 시 생성. Device Key 분실/탈취 시 **1회용 재발급 요청**에 사용. |

---

## 3. 주요 프로토콜 (Protocols)

### 3.1. 기기 인증 및 수명주기 (Lifecycle)

1.  **Normal State (정상)**
    * `Operational Key`를 사용하여 mTLS 통신.
    * 유효기간: 단기 (1~3개월).

2.  **Compromised - 1st Strike (1차 탈취)**
    * 서버: 기존 키 Revoke(폐기).
    * 기기: `Bootstrap Key`를 사용하여 재발급 요청.
    * 서버: 검증 후 새 키 발급. **DB에서 Bootstrap Key 상태를 'USED'로 변경** (재사용 불가).

3.  **Compromised - 2nd Strike (2차 탈취)**
    * 기기: `Bootstrap Key`가 이미 소진됨. 자동 복구 불가.
    * 상태: **Lockdown Mode (잠금)** 진입.

4.  **Manual Recovery (OTP 복구)**
    * 관리자: 사용자 신원 확인 후 OTP 발급.
    * 기기: OTP 입력 → 서버 검증 → 잠금 해제 및 키 전체(Bootstrap 포함) 리셋.

### 3.2. Air-Gap 키 관리 프로세스 (Vault Workflow)
Root CA의 비밀키를 노출하지 않기 위해 **CSR(Certificate Signing Request)** 방식을 준수한다.

1.  **생성**: Vault가 내부에서 `Intermediate Key` 생성 (외부 유출 없음).
2.  **요청**: Vault가 `CSR`(신청서) 출력.
3.  **이동**: 관리자가 CSR을 USB에 담아 오프라인 PC(Root CA)로 이동.
4.  **서명**: Root CA가 서명하여 `Certificate`(인증서) 생성.
5.  **등록**: 관리자가 Certificate를 다시 Vault에 업로드하여 활성화.

### 3.3. 재해 복구 (The "God Mode")
서버(A) 및 기기 키가 모두 탈취된 최악의 상황 시 대응 시나리오.

1.  관리자가 오프라인 PC에서 **새 서버 주소(C)**가 담긴 펌웨어 생성.
2.  `Master Key B`로 펌웨어 서명.
3.  서명된 펌웨어 배포 (해킹된 망을 통해 전송 가능).
4.  기기는 내장된 `Master B Public Key`로 서명 검증.
5.  검증 성공 시 기존 키/설정 삭제 후 **서버 C로 강제 이주(Migration)**.

---

## 4. 단말 보안 및 복제 방지 (Device Hardening)

물리적 탈취(SD카드 복제) 및 원격 침투를 방지하기 위한 **4중 방어막(요새화 전략)**을 구축한다.

### 4.1. 하드웨어 바인딩 (Hardware Binding)
* **식별자**: 단순 UUID가 아닌 **CPU Serial (OTP 영역/Mailbox)**을 물리적 ID로 사용.
* **Key Wrapping (키 봉인)**:
    * `Device Private Key`는 평문으로 저장하지 않음.
    * `AES_Encrypt(Key, Password=CPU_Serial)` 형태로 저장.
    * 타 기기(다른 Serial)에서 실행 시 복호화 실패로 구동 불가.

### 4.2. 코드 난독화 (Obfuscation)
* **도구**: `PyArmor` (또는 동급).
* **적용**: 주요 보안 로직(키 관리, 하드웨어 조회)을 바이너리로 컴파일.
* **실행 제한**: 라이선스 파일을 통해 지정된 하드웨어 외 실행 원천 차단.

### 4.3. 운영체제 요새화 (OS Level Hardening)
* **Access Control (문 없애기)**:
    * SSH 서비스 비활성화 또는 포트 변경.
    * Root 계정 잠금 (`passwd -l root`) 및 쉘 접근 차단 (`/sbin/nologin`).
* **Process Execution (내부 실행)**:
    * `Systemd` 서비스를 통해 사용자 로그인 없이 Root 권한으로 어플리케이션 자동 실행.
* **Secure Storage (파일 잠금)**:
    * 키 저장소 위치: `/etc/ares4/secrets/` (Root Only).
    * 불변 속성 설정 (`chattr +i`)으로 Root 권한으로도 삭제/수정 방지.

### 4.4. Docker 보안 (Container Hardening)
* **이미지**: Private Key 포함 금지. 난독화된 코드만 포함.
* **런타임 검증**:
    * 컨테이너 실행 시 호스트의 하드웨어 정보 접근을 위해 제한적 마운트.
    * 예: `--device /dev/vchiq` (Mailbox Interface) 또는 `/proc/cpuinfo` (Read-only).

---

## 5. 데이터베이스 스키마 (Governance)

`Governance` DB - `devices` 테이블 확장 스키마.

```sql
CREATE TABLE devices (
    -- 1. 기본 식별 정보
    uuid UUID PRIMARY KEY,            -- 논리적 ID
    device_name VARCHAR(100),
    
    -- 2. 하드웨어 바인딩 (Anti-Cloning)
    cpu_serial VARCHAR(64) NOT NULL,  -- 물리적 ID (복제 방지 검증용)
    
    -- 3. 보안 키 관리
    bootstrap_public_key TEXT,        -- 비상용 키의 공개키 (서명 검증용)
    bootstrap_key_status VARCHAR(20) DEFAULT 'ACTIVE', -- 상태: ACTIVE | USED | REVOKED
    
    -- 4. 상태 및 리스크 관리
    status VARCHAR(20) DEFAULT 'ONLINE',
    is_locked BOOLEAN DEFAULT FALSE,  -- 2회 이상 사고 시 True (Lockdown)
    compromise_count INT DEFAULT 0,   -- 사고 횟수 카운트
    
    -- 5. 메타 데이터
    firmware_version VARCHAR(20),
    last_active TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);