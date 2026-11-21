from functools import lru_cache
from typing import BinaryIO
from uuid import UUID

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.models.report import Photo
from app.settings import settings


class StorageError(Exception):
    pass


class PhotoStore:
    def __init__(self):
        self.client = boto3.client(
            "s3", endpoint_url=settings.s3_endpoint_url, region_name=settings.s3_region,
            config=Config(
                s3={"addressing_style": "path"} if settings.s3_endpoint_url else None,
                connect_timeout=3, read_timeout=10, retries={"total_max_attempts": 2},
            ),
        )

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=settings.s3_bucket)
        except ClientError as error:
            if error.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
                raise
            parameters = {"Bucket": settings.s3_bucket}
            if settings.s3_region != "us-east-1":
                parameters["CreateBucketConfiguration"] = {"LocationConstraint": settings.s3_region}
            try:
                self.client.create_bucket(**parameters)
            except ClientError as create_error:
                if create_error.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
                    raise

    def put(self, report_id: UUID, photo: Photo, body: BinaryIO) -> None:
        try:
            self.client.put_object(
                Bucket=settings.s3_bucket, Key=f"{report_id}/{photo.id}", Body=body,
                ContentType=photo.content_type, ContentLength=photo.size_bytes,
            )
        except (BotoCoreError, ClientError) as error:
            raise StorageError("Photo upload failed") from error

    def read(self, report_id: UUID, photo: Photo) -> bytes:
        try:
            response = self.client.get_object(Bucket=settings.s3_bucket, Key=f"{report_id}/{photo.id}")
            with response["Body"] as body:
                data = body.read(photo.size_bytes + 1)
        except (BotoCoreError, ClientError) as error:
            raise StorageError("Photo download failed") from error
        if len(data) != photo.size_bytes:
            raise StorageError("Unexpected photo size")
        return data

    def remove(self, report_id: UUID, photo_id: UUID) -> None:
        try:
            self.client.delete_object(Bucket=settings.s3_bucket, Key=f"{report_id}/{photo_id}")
        except (BotoCoreError, ClientError) as error:
            raise StorageError("Photo cleanup failed") from error


@lru_cache
def get_photo_store() -> PhotoStore:
    return PhotoStore()
