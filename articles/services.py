import os
from django.db.models import Max
from django.utils import timezone
from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .models import ArticleVersion


# ---------------- GOOGLE DRIVE CONFIG ---------------- #

SCOPES = ['https://www.googleapis.com/auth/drive']

SERVICE_ACCOUNT_FILE = os.path.join(
    settings.BASE_DIR,
    'config',
    'credentials.json'
)


def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    service = build('drive', 'v3', credentials=credentials)
    return service


def upload_file_to_drive(file_path, file_name, folder_id=None):

    service = get_drive_service()

    file_metadata = {
        'name': file_name
    }

    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return file


# ---------------- VERSION LOGIC + DRIVE ---------------- #

def create_new_version(article, title, content, user, summary="", folder_id=None):

    # 1️⃣ Get latest version number
    latest_version = article.versions.aggregate(
        Max("version_number")
    )["version_number__max"] or 0

    # 2️⃣ Set old current version to False
    article.versions.filter(is_current=True).update(is_current=False)

    # 3️⃣ Create temporary file
    file_name = f"{article.title}_v{latest_version + 1}.txt"
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n\n")
        f.write(content)

    # 4️⃣ Upload to Drive
    drive_response = upload_file_to_drive(
        file_path=file_path,
        file_name=file_name,
        folder_id=folder_id
    )

    # 5️⃣ Save version in DB
    version = ArticleVersion.objects.create(
        article=article,
        title=title,
        content=content,
        version_number=latest_version + 1,
        edited_by=user,
        is_current=True,
        change_summary=summary,
        drive_file_id=drive_response.get("id"),
        drive_link=drive_response.get("webViewLink")
    )

    # 6️⃣ Update article timestamp
    article.updated_at = timezone.now()
    article.save()

    return version


# ------------------------------------------------------ #

def update_article(article, title, content, user, folder_id=None):

    latest_version = article.versions.aggregate(
        Max('version_number')
    )['version_number__max'] or 0

    article.versions.filter(is_current=True).update(is_current=False)

    file_name = f"{article.title}_v{latest_version + 1}.txt"
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n\n")
        f.write(content)

    drive_response = upload_file_to_drive(
        file_path=file_path,
        file_name=file_name,
        folder_id=folder_id
    )

    version = ArticleVersion.objects.create(
        article=article,
        title=title,
        content=content,
        version_number=latest_version + 1,
        edited_by=user,
        is_current=True,
        drive_file_id=drive_response.get("id"),
        drive_link=drive_response.get("webViewLink")
    )

    article.updated_at = timezone.now()
    article.save()

    return version