from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, object_mapper
from app.core.config import settings
from datetime import datetime

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    def as_dict(self):
        """SQLAlchemy 모델 객체를 딕셔너리로 변환하는 헬퍼 메소드"""
        d = {}
        for c in object_mapper(self).columns:
            val = getattr(self, c.key)
            if isinstance(val, datetime):
                d[c.key] = val.isoformat()
            else:
                d[c.key] = val
        return d
