from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime, timezone # timezone 추가

class IssuedCertificateRead(BaseModel):
    """
    Vault PKI Secrets Engine으로부터 발급되거나 조회된 인증서 정보를 나타내는 스키마입니다.
    이 스키마는 Vault API 응답의 'data' 필드 구조에 대응됩니다.
    """
    certificate: str = Field(..., description="발급된 PEM 형식의 클라이언트 인증서")
    private_key: str = Field(..., description="발급된 PEM 형식의 클라이언트 개인 키")
    issuing_ca: str = Field(..., description="인증서를 발급한 CA(인증 기관)의 PEM 형식 인증서")
    serial_number: str = Field(..., description="발급된 인증서의 고유 시리얼 번호")
    common_name: Optional[str] = Field(None, description="인증서의 Common Name (CN)")
    issued_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="인증서 발급 시각"
    ) # 수정
    expiration: Optional[datetime] = Field(None, description="인증서 만료 시각 (Unix Timestamp)")
    # Vault 응답에 포함될 수 있는 다른 필드들이 있다면 여기에 추가합니다.
    # 예: ca_chain: Optional[List[str]] = None
    #     private_key_type: Optional[str] = None

# 필요하다면 이외의 스키마들도 정의할 수 있습니다.
# 예를 들어, Vault가 반환하는 raw 데이터를 위한 스키마 등.
