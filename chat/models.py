import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

def validate_chat_attachment(file):
    max_size_mb = 15.0
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Attachment file size cannot exceed {max_size_mb}MB.")

def chat_attachment_upload_path(instance, filename):
    # Store per-conversation in segregated directories
    ext = os.path.splitext(filename)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    return f"chat_attachments/{instance.conversation.id}/{unique_filename}"


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @classmethod
    def get_or_create_direct_chat(cls, user_a, user_b):
        if user_a == user_b:
            raise ValueError("Users cannot start a conversation with themselves.")
        conversations = cls.objects.filter(participants=user_a).filter(participants=user_b)
        for conv in conversations:
            if conv.participants.count() == 2:
                return conv, False
        conv = cls.objects.create()
        conv.participants.add(user_a, user_b)
        return conv, True

    def get_other_participant(self, current_user):
        return self.participants.exclude(id=current_user.id).first()

    def __str__(self):
        return f"Conversation {self.id}"


class Message(models.Model):
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    )

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=2000, blank=True, default='')
    
    # Attachment fields
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    attachment = models.FileField(
        upload_to=chat_attachment_upload_path,
        blank=True,
        null=True,
        validators=[validate_chat_attachment]
    )
    attachment_name = models.CharField(max_length=255, blank=True, default='')
    attachment_size = models.PositiveIntegerField(default=0, help_text="Size in bytes")

    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender', 'is_read']),
        ]

    @property
    def is_image(self):
        if not self.attachment:
            return False
        ext = os.path.splitext(self.attachment.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

    def formatted_size(self):
        if not self.attachment_size:
            return ""
        size_kb = self.attachment_size / 1024
        if size_kb < 1024:
            return f"{size_kb:.1f} KB"
        return f"{size_kb / 1024:.2f} MB"

    def __str__(self):
        return f"Msg from {self.sender.username} ({self.message_type}) at {self.timestamp.strftime('%H:%M')}"