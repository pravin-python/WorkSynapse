"""
Notification Background Tasks
"""
from celery import shared_task
from app.core.logging import logger

@shared_task(bind=True, max_retries=3)
def send_email_notification(self, user_id: int, subject: str, body: str):
    """Send email notification."""
    try:
        logger.info(f"Sending email to user {user_id}: {subject}")
        # TODO: Integrate with email service (SendGrid, SES, etc.)
        return {"status": "sent", "user_id": user_id}
    except Exception as e:
        logger.error(f"Email send error: {e}")
        raise self.retry(exc=e)

@shared_task(bind=True, max_retries=3)
def send_push_notification(self, user_id: int, title: str, message: str):
    """Send push notification to desktop/mobile."""
    try:
        logger.info(f"Sending push to user {user_id}: {title}")
        # TODO: Integrate with push service (FCM, OneSignal, etc.)
        return {"status": "sent", "user_id": user_id}
    except Exception as e:
        logger.error(f"Push send error: {e}")
        raise self.retry(exc=e)

@shared_task
def send_task_assignment_notification(assignee_id: int, task_id: int, assigner_name: str):
    """Notify user when assigned a task."""
    logger.info(f"Task {task_id} assigned to user {assignee_id}")
    # Send both email and push
    send_email_notification.delay(
        assignee_id,
        "New Task Assigned",
        f"You have been assigned a new task by {assigner_name}"
    )
    send_push_notification.delay(
        assignee_id,
        "New Task",
        f"Task assigned by {assigner_name}"
    )

@shared_task
def send_mention_notification(mentioned_user_id: int, mentioner_name: str, channel_id: str):
    """Notify user when mentioned in chat."""
    logger.info(f"User {mentioned_user_id} mentioned by {mentioner_name}")
    send_push_notification.delay(
        mentioned_user_id,
        "You were mentioned",
        f"{mentioner_name} mentioned you in chat"
    )
