import boto3
from botocore.config import Config
from ..config import (
    R2_ACCOUNT_ID,
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME,
    R2_ENDPOINT_URL,
    R2_CUSTOM_DOMAIN
)
import os
import traceback

class R2Service:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

    def upload_file(self, file_path, object_name):
        """上传文件到 R2"""
        try:
            self.s3_client.upload_file(file_path, R2_BUCKET_NAME, object_name)
            if R2_CUSTOM_DOMAIN:
                return f"https://{R2_CUSTOM_DOMAIN}/{object_name}"
            return f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{object_name}"
        except Exception as e:
            print(f"[R2 ERROR] upload_file failed: {type(e).__name__}: {e}")
            traceback.print_exc()
            return None

    def upload_content(self, content: bytes, object_name: str, content_type: str = "image/png"):
        """直接上传二进制数据到 R2"""
        try:
            self.s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=object_name,
                Body=content,
                ContentType=content_type
            )
            if R2_CUSTOM_DOMAIN:
                return f"https://{R2_CUSTOM_DOMAIN}/{object_name}"
            return f"{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/{object_name}"
        except Exception as e:
            print(f"Error uploading content to R2: {e}")
            return None

    def delete_file(self, object_name):
        """从 R2 删除文件"""
        try:
            self.s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=object_name)
            return True
        except Exception as e:
            print(f"Error deleting from R2: {e}")
            return False

r2_service = R2Service()
