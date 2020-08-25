import re

from django.conf import settings
from django.core import mail
from django.core.mail import get_connection
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import EmailMessage
from django.template.loader import get_template
from huey.contrib.djhuey import task


def remove_extra_line_breaks(text):
    """
    Replaces multiple line breaks with just one.

    Useful to suppress empty line breaks generated by Django's template tags
    in emails text templates.
    """
    return re.sub(r"\n{3,}", "\n\n", text)


def get_email_text_template(template, context):
    context.update(
        {
            "itou_protocol": settings.ITOU_PROTOCOL,
            "itou_fqdn": settings.ITOU_FQDN,
            "itou_email_contact": settings.ITOU_EMAIL_CONTACT,
            "itou_environment": settings.ITOU_ENVIRONMENT,
        }
    )
    return remove_extra_line_breaks(get_template(template).render(context).strip())


def get_email_message(to, context, subject, body, from_email=settings.DEFAULT_FROM_EMAIL, bcc=None):
    subject_prefix = "[DEMO] " if settings.ITOU_ENVIRONMENT == "DEMO" else ""
    return mail.EmailMessage(
        from_email=from_email,
        to=to,
        bcc=bcc,
        subject=subject_prefix + get_email_text_template(subject, context),
        body=get_email_text_template(body, context),
    )


# EXPERIMENTAL:
# ---
# Custom async email backends


@task(retries=100, retry_delay=10)
def _async_proces_email(email_message):
    """
    Idiotic email sender: print raw messages, retries 100 times every 10 sec.
    """
    print(f"From: {email_message.from_email}")
    print(f"To: {email_message.to}")
    print(f"Subject: {email_message.subject}")
    print(f"Body:\n{email_message.body}")


class DummyAsyncEmailBackend(BaseEmailBackend):
    def open(self):
        pass

    def close(self):
        pass

    def send_messages(self, email_messages):
        if not email_messages:
            return

        nb_sent = 0

        for message in email_messages:
            _async_proces_email(message)
            nb_sent += 1

        return nb_sent


def _serializeEmailMessage(email_message):
    return {
        "subject": email_message.subject,
        "to": email_message.to,
        "from_email": email_message.from_email,
        "cc": email_message.cc,
        "bcc": email_message.bcc,
        "body": email_message.body,
    }


def _deserializeEmailMessage(serialized_email_message):
    return EmailMessage(connection=get_connection(backend=settings.ASYNC_EMAIL_BACKEND), **serialized_email_message)


@task(retries=settings.SEND_EMAIL_NB_RETRIES, retry_delay=settings.SEND_EMAIL_RETRY_DELAY)
def _async_send_messages(serializable_email_messages):
    count = 0

    for message in [_deserializeEmailMessage(email) for email in serializable_email_messages]:
        message.send()
        count += 1

    return count


class AsyncEmailBackend(BaseEmailBackend):
    """Decorating a method does not work (no object context)
       Only functions can be Huey tasks
       This workaround exposes the default email backend `send_messages` method to Huey scheduler.
    """

    def send_messages(self, email_messages):
        # Turn emails into something serializable
        if not email_messages:
            return

        emails = [_serializeEmailMessage(email) for email in email_messages]

        return _async_send_messages(emails)
