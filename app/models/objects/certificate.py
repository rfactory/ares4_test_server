# app/models/objects/certificate.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from ..base_model import TimestampMixin

class Certificate(Base, TimestampMixin):
    """
    인증서 정보를 저장하는 모델입니다.
    장치 인증서 및 CA(인증 기관) 인증서와 같은 다양한 유형의 공개 인증서를 관리합니다.
    """
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True) # 인증서의 고유 ID
    certificate_name = Column(String(255), unique=True, index=True, nullable=False) # "인증서의 고유 이름"
    certificate_content = Column(Text, nullable=False) # "인증서의 공개 키 내용"
    
    # --- Relationships ---
    device_as_device_cert = relationship("Device", foreign_keys="Device.device_certificate_id", back_populates="device_certificate") # 이 인증서를 장치 인증서로 사용하는 장치 목록
    device_as_ca_cert = relationship("Device", foreign_keys="Device.ca_certificate_id", back_populates="ca_certificate") # 이 인증서를 CA 인증서로 사용하는 장치 목록

    def __repr__(self):
        return f"<Certificate(name='{self.certificate_name}')>"