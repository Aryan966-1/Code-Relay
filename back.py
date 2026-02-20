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
    







    created_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,  # ADD THIS
    related_name="created_articles"
)
    








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

    # 🔥 Google Drive fields
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
        if self.is_current:
            ArticleVersion.objects.filter(
                article=self.article,
                is_current=True
            ).update(is_current=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.article.id} - v{self.version_number}"
    





    file = models.FileField(...)







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

    # 🔥 Google Drive metadata
    file_name = models.CharField(max_length=255)
    drive_file_id = models.CharField(max_length=255, db_index=True)
    drive_link = models.URLField()

    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["workspace"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["uploaded_by"]),
        ]

    def __str__(self):
        return self.file_name
    




    GOOGLE_DRIVE_FOLDER_ID = "https://drive.google.com/drive/u/0/folders/1gO1lUtprekkTv8ZaSVioChO494w4PJGT"