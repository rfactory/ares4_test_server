import redis

class GovernanceCommandService:
    EMERGENCY_MODE_KEY = "system:emergency_mode_active"

    def update_emergency_mode(self, redis_client: redis.Redis, *, prime_admin_count: int):
        """Prime_Admin 수를 기반으로 비상 모드 상태를 업데이트합니다."""
        if prime_admin_count == 0:
            redis_client.set(self.EMERGENCY_MODE_KEY, "true")
            print(f"[GOVERNANCE] EMERGENCY MODE ACTIVATED: No Prime_Admins found.")
        else:
            existed = redis_client.delete(self.EMERGENCY_MODE_KEY)
            if existed:
                print(f"[GOVERNANCE] EMERGENCY MODE DEACTIVATED: {prime_admin_count} Prime_Admin(s) found.")

governance_command_service = GovernanceCommandService()
