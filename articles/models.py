from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.workspaces.models import Workspace

User = get_user_model()


# =========================
# Tag Model
# =========================
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================
# Article Model
# =========================
class Article(models.Model):

    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("ARCHIVED", "Archived"),
    )

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="articles_IN_WORKSPACE"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="created_articles"
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="DRAFT",
        db_index=True
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_articles"
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def approve(self, reviewer):
        self.status = "APPROVED"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def archive(self):
        self.status = "ARCHIVED"
        self.archived_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Article {self.id}"


# =========================
# Article Version Model
# =========================
class ArticleVersion(models.Model):

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="versions"
    )

    title = models.CharField(max_length=255)
    content = models.TextField()

    version_number = models.PositiveIntegerField()

    edited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="article_versions"
    )

    edited_at = models.DateTimeField(auto_now_add=True)

    is_current = models.BooleanField(default=True)

    change_summary = models.TextField(blank=True)
    # NEW FIELDS 👇
    drive_file_id = models.CharField(max_length=255, blank=True, null=True)
    drive_link = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
class Meta:
    ordering = ['-version_number']
    unique_together = ('article', 'version_number')
    indexes = [
        models.Index(fields=["article", "is_current"]),
        ]

    def save(self, *args, **kwargs):
        """
        Automatically mark previous versions as not current
        """
        if self.is_current:
            ArticleVersion.objects.filter(
                article=self.article,
                is_current=True
            ).update(is_current=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.article.id} - v{self.version_number}"


# =========================
# Document Model
# =========================
class Document(models.Model):

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    file = models.FileField(upload_to="documents/")

    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

class Meta:
    ordering = ['-created_at']
    indexes = [
        models.Index(fields=["workspace"]),
        models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.file.name