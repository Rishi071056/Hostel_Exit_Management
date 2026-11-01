import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from backend.config import (
    BREVO_API_KEY,
    BREVO_SENDER_EMAIL,
    BREVO_SENDER_NAME
)


def send_email_otp(receiver_email: str, otp: str):
    configuration = sib_api_v3_sdk.Configuration()

    configuration.api_key["api-key"] = BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    sender = sib_api_v3_sdk.SendSmtpEmailSender(
        email=BREVO_SENDER_EMAIL,
        name=BREVO_SENDER_NAME
    )

    email = sib_api_v3_sdk.SendSmtpEmail(
        sender=sender,

        to=[
            {
                "email": receiver_email
            }
        ],

        subject="Hostel Exit Management - Email Verification OTP",

        html_content=f"""
        <html>
            <body>
                <h2>Email Verification</h2>

                <p>Your OTP is:</p>

                <h1>{otp}</h1>

                <p>This OTP is valid for 5 minutes.</p>

                <p>
                    If you did not request this registration,
                    please ignore this email.
                </p>
            </body>
        </html>
        """
    )

    try:
        response = api_instance.send_transac_email(email)
        return response

    except ApiException as e:
        print("Brevo email error:", e)
        raise