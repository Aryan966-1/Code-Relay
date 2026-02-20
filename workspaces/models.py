from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# =========================
# Workspace Model
# =========================
class Workspace(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_workspaces"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Automatically make creator the owner
        if is_new:
            WorkspaceMembership.objects.create(
                workspace=self,
                user=self.created_by,
                role=WorkspaceMembership.Role.OWNER
            )

    def __str__(self):
        return self.name


# =========================
# Workspace Membership Model
# =========================
class WorkspaceMembership(models.Model):

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        EDITOR = "editor", "Editor"
        VIEWER = "viewer", "Viewer"

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="memberships"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_memberships"
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("workspace", "user")
        indexes = [
            models.Index(fields=["workspace", "user"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.workspace.name} ({self.role})"


# =========================
# Tag Model
# =========================
class Tag(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="tags"
    )

    name = models.CharField(max_length=50)

    class Meta:
        ordering = ["name"]
        unique_together = ("workspace", "name")
        indexes = [
            models.Index(fields=["workspace", "name"]),
        ]

    def __str__(self):
        return self.name


# =========================
# Article Model
# =========================
class Article(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="workspace_articles"
    )

    title = models.CharField(max_length=255)
    content = models.TextField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_articles"
    )

    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name="articles"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["created_at"]),
        ]

    def clean(self):
        # Ensure tags belong to same workspace
        for tag in self.tags.all():
            if tag.workspace != self.workspace:
                raise ValidationError(
                    "Tag must belong to the same workspace as the article."
                )

    def __str__(self):
        return self.title


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

    # Google Drive integration
    drive_file_id = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    drive_link = models.URLField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version_number"]
        unique_together = ("article", "version_number")
        indexes = [
            models.Index(fields=["article", "is_current"]),
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():

            # Auto-generate version number
            if not self.version_number:
                last_version = ArticleVersion.objects.filter(
                    article=self.article
                ).order_by("-version_number").first()

                self.version_number = (
                    last_version.version_number + 1
                    if last_version else 1
                )

            # Ensure only one current version
            if self.is_current:
                ArticleVersion.objects.filter(
                    article=self.article,
                    is_current=True
                ).update(is_current=False)

            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.article.title} - v{self.version_number}"


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

    # Google Drive metadata
    file_name = models.CharField(max_length=255)

    drive_file_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )

    drive_link = models.URLField()

    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["uploaded_by"]),
        ]

    def __str__(self):
        return self.file_name