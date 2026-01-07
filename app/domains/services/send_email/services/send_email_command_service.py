from fastapi_mail import FastMail, MessageSchema, MessageType
from ..schemas.send_email_command import EmailSchema
from app.core.email import conf

class SendEmailCommandService:
    """
    이메일 발송에 대한 단일 책임을 갖는 서비스입니다.
    fastapi-mail 라이브러리를 사용하여 실제로 이메일을 발송합니다.
    """
    async def send_email(self, *, email_data: EmailSchema):
        """
        주어진 데이터로 이메일을 비동기적으로 발송합니다.
        """
        message = MessageSchema(
            subject=email_data.subject,
            recipients=[email_data.to],
            template_body=email_data.context,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        try:
            await fm.send_message(message, template_name=email_data.template_name)
            return True
        except Exception as e:
            # In a real app, you'd want to log this error more robustly
            print(f"Failed to send email: {e}")
            return False

send_email_command_service = SendEmailCommandService()
