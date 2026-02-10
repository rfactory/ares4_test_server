from app.domains.application.ingestion.ingestion_dispatcher import ingestion_dispatcher

class IngestionDispatcherProvider:
    """
    Application 계층의 디스패처를 외부 도메인이나 게이트웨이에서 
    사용할 수 있도록 노출하는 inter_domain 제공자입니다.
    """
    def dispatch(self, db, *, topic, payload):
        # 복잡한 비즈니스 조합 로직이 있는 Dispatcher로 토스합니다.
        return ingestion_dispatcher.dispatch(db=db, topic=topic, payload=payload)

ingestion_dispatcher_provider = IngestionDispatcherProvider()