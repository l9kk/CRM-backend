import logging
from django.core.mail import send_mail
from decouple import config
from .models import ProjectComment

logger = logging.getLogger('app')


def create_comment_and_notify(project, comment_text, author_name, email_subject):

    comment = ProjectComment.objects.create(
        project=project,
        comment_text=comment_text,
        author_name=author_name
    )

    send_mail(
        subject=email_subject,
        message=comment_text,
        from_email=config('EMAIL_HOST_USER'),
        recipient_list=[project.contact_email],
        fail_silently=False
    )
    logger.info(
        f"Comment added to project '{project.title}' by {author_name}: {comment_text}"
    )

    return comment
