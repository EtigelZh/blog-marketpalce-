import json
from io import BytesIO
from uuid import uuid4

from minio import Minio

from src.app.config.settings import settings


class StorageService:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def create_bucket(self) -> None:
        if self.client.bucket_exists(settings.minio_bucket):
            return

        self.client.make_bucket(settings.minio_bucket)

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [
                        f"arn:aws:s3:::{settings.minio_bucket}/*",
                    ],
                },
            ],
        }

        self.client.set_bucket_policy(
            settings.minio_bucket,
            json.dumps(policy),
        )

    def upload_image(
        self,
        content: bytes,
        filename: str,
        content_type: str,
    ) -> str:
        self.create_bucket()

        extension = filename.rsplit(".", 1)[-1].lower()

        object_name = f"{uuid4()}.{extension}"

        self.client.put_object(
            settings.minio_bucket,
            object_name,
            BytesIO(content),
            length=len(content),
            content_type=content_type,
        )

        return (
            f"{settings.minio_public_endpoint}/"
            f"{settings.minio_bucket}/"
            f"{object_name}"
        )