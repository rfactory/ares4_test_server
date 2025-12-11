import logging
import re

logger = logging.getLogger(__name__)

class EmqxAuthValidator:
    """EMQX 인증/권한 부여에 대한 개별 규칙을 판별하는 Validator입니다."""

    def is_superuser(self, username: str) -> bool:
        """사용자가 슈퍼유저인지 판별합니다."""
        # 여기에 슈퍼유저 규칙을 정의합니다. (예: username == 'admin')
        return False

    def can_access_topic(self, rule_topic: str, actual_topic: str) -> bool:
        """
        주어진 ACL 규칙이 특정 토픽에 대한 접근을 허용하는지 판별합니다.
        MQTT 토픽 와일드카드(+, #)를 지원합니다.
        """
        logger.debug(f'''[Validator] Matching rule_topic="{rule_topic}" with actual_topic="{actual_topic}"''')

        # '$'로 시작하는 시스템 토픽은 '#' 와일드카드와 매치되지 않는 것이 표준입니다.
        if rule_topic == '#' and not actual_topic.startswith('$'):
            logger.debug('[Validator] Rule is "#", allowing access (non-system topic). Result: True')
            return True
        
        # MQTT 필터를 정규식으로 변환합니다.
        # '+' -> 한 레벨의 토픽과 매치 ([^/]+)
        # '/+' -> /(한 레벨의 토픽)
        # '/#' -> 토픽 끝에서 0개 이상의 하위 레벨과 매치 (?:/.*)?
        # '#' -> 모든 레벨과 매치 (위에서 처리됨)
        
        # 정규식 특수 문자를 이스케이프하고 와일드카드를 변환합니다.
        regex = rule_topic.replace('+', '[^/]+')
        if regex.endswith('/#'):
            # 예: a/b/# -> a/b 또는 a/b/anything
            regex = regex[:-2] + '(?:/.*)?'
        
        # 정규식 전체가 일치해야 하므로 ^와 $를 추가합니다.
        regex = f'^{regex}$'

        try:
            match = re.fullmatch(regex, actual_topic) is not None
            logger.debug(f'''[Validator] Regex matching: pattern="{regex}", topic="{actual_topic}". Result: {match}''')
            return match
        except re.error as e:
            logger.error(f"Invalid regex pattern created from rule '{rule_topic}': {e}")
            return False

emqx_auth_validator = EmqxAuthValidator()