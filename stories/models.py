from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def story_expiry():
    return timezone.now() + timedelta(hours=24)


class Story(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    author     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories"
    )
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    media_file = models.FileField(upload_to="stories/media/")
    audio_file = models.FileField(upload_to="stories/audio/", blank=True, null=True)
    caption    = models.CharField(max_length=200, blank=True)
    trim_start = models.FloatField(default=0)
    trim_end   = models.FloatField(default=0)   # 0 = full length
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=story_expiry)
    viewers    = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="viewed_stories"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author.username} — {self.media_type}"

    @property
    def is_active(self):
        return timezone.now() < self.expires_at

    @property
    def view_count(self):
        return self.viewers.count()