from app.domains.services.send_email.schemas.send_email_command import EmailSchema
from app.domains.services.send_email.services.send_email_command_service import send_email_command_service

class SendEmailCommandProvider:
    """
    SendEmail Command 서비스에 대한 공개 인터페이스입니다.
    """
    async def send_email(self, *, email_data: EmailSchema) -> bool:
        return await send_email_command_service.send_email(email_data=email_data)

send_email_command_provider = SendEmailCommandProvider()
