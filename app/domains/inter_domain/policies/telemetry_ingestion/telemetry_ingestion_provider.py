from app.domains.action_authorization.policies.telemetry_ingestion.telemetry_ingestion_policy import telemetry_ingestion_policy

class TelemetryIngestionPolicyProvider:
    """
    수치 데이터 처리 정책(Policy)을 도메인 외부에서 
    호출할 수 있게 해주는 inter_domain 제공자입니다.
    """
    def ingest(self, db, *, device_uuid_str, topic, payload):
        # 내부 도메인의 실제 '뇌(Policy)'에게 처리를 맡깁니다.
        return telemetry_ingestion_policy.ingest(
            db=db, 
            device_uuid_str=device_uuid_str, 
            topic=topic, 
            payload=payload
        )

# 다른 곳에서 바로 사용할 수 있도록 인스턴스화해서 내보냅니다.
telemetry_ingestion_policy_provider = TelemetryIngestionPolicyProvider()