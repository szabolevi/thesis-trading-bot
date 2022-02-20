import smtplib

from core.config import EMAIL_ADDRESS, EMAIL_PASSWORD


def send_notification(message):
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        subject = "Bot erteites"
        full_msg = f"Subject: {subject}\n\n{message}"

        smtp.sendmail(EMAIL_ADDRESS, "szabo.levi96@gmail.com", full_msg)
