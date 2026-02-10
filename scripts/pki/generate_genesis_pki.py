# server2/scripts/pki/generate_genesis_pki.py
# Root CA 절대권력을 가진 인증서 만드는 기능
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# 저장 위치 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent # server2/
OUTPUT_DIR = BASE_DIR / "offline_storage"
ROOT_CA_DIR = OUTPUT_DIR / "root_ca"
FIRMWARE_KEY_DIR = OUTPUT_DIR / "firmware_keys"

def ensure_dir(path: Path):
    if not path.exists():
        os.makedirs(path)

def load_root_ca():
    """저장된 Root CA 키와 인증서를 불러옵니다."""
    key_path = ROOT_CA_DIR / "root_ca.key"
    cert_path = ROOT_CA_DIR / "root_ca.crt"
    
    with open(key_path, "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    with open(cert_path, "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())
    return key, cert

def sign_vault_csr(csr_pem: str) -> str:
    """
    [핵심 연결 고리]
    Vault에서 생성한 CSR(문자열)을 받아서, Offline Root CA 키로 서명한 뒤
    인증서(PEM 문자열)를 반환합니다.
    """
    root_key, root_cert = load_root_ca()
    csr = x509.load_pem_x509_csr(csr_pem.encode('utf-8'))

    # Builder 생성
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(csr.subject)
    builder = builder.issuer_name(root_cert.subject)
    builder = builder.public_key(csr.public_key())
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.now(timezone.utc))
    builder = builder.not_valid_after(datetime.now(timezone.utc) + timedelta(days=365 * 5)) # 5년
    
    # [추가된 부분] Vault 필수 요구사항: SKI & AKI 확장 기능
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
        critical=False
    )
    builder = builder.add_extension(
        x509.AuthorityKeyIdentifier.from_issuer_public_key(root_cert.public_key()),
        critical=False
    )

    # 기본 제약 조건 (Intermediate CA이므로 ca=True)
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=0), critical=True,
    )
    
    # 키 사용 용도
    builder = builder.add_extension(
        x509.KeyUsage(
            digital_signature=True,
            content_commitment=False,
            key_encipherment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=True,
            crl_sign=True,
            encipher_only=False,
            decipher_only=False,
        ), critical=True,
    )

    # 서명
    cert = builder.sign(private_key=root_key, algorithm=hashes.SHA256())
    return cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')

def main():
    print(f"=== Ares4 Genesis Key Generator ===")
    print(f"[Location] {OUTPUT_DIR}")
    ensure_dir(ROOT_CA_DIR)
    ensure_dir(FIRMWARE_KEY_DIR)

    # 1. Root CA 생성 (이전과 동일)
    root_key_path = ROOT_CA_DIR / "root_ca.key"
    root_cert_path = ROOT_CA_DIR / "root_ca.crt"

    if not root_key_path.exists():
        print("[Step 1] Generating Root CA...")
        root_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        with open(root_key_path, "wb") as f:
            f.write(root_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"Ares4 Offline Root CA"),
        ])
        cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(root_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc)).not_valid_after(datetime.now(timezone.utc) + timedelta(days=365*20)).add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).add_extension(x509.KeyUsage(digital_signature=True, content_commitment=False, key_encipherment=False, data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False), critical=True).sign(root_key, hashes.SHA256())
        
        with open(root_cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        print(f"   >> Created: {root_cert_path}")
    else:
        print("[Step 1] Root CA already exists.")

    # 2. Firmware Key 생성 (이전과 동일)
    fw_key_path = FIRMWARE_KEY_DIR / "master.key"
    if not fw_key_path.exists():
        print("[Step 2] Generating Firmware Master Key...")
        fw_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        with open(fw_key_path, "wb") as f:
            f.write(fw_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption()))
        with open(FIRMWARE_KEY_DIR / "master.pub", "wb") as f:
            f.write(fw_key.public_key().public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo))
        print(f"   >> Created: {fw_key_path}")
    else:
        print("[Step 2] Firmware Key already exists.")

if __name__ == "__main__":
    main()