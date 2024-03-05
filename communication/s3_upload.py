import config
import boto3
import magic
from inboicing_system.settings import logger


def s3_upload_file(
    file_name, bucket=config.S3_BUCKET, object_name=None, remove_tmp=False
):
    """
    Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket to upload to
        :param object_name: S3 object name. If not specified then file_name is used
        :param remove_tmp: For Removing tmp from file url
        :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name
        if remove_tmp:
            file_split = file_name.split("/tmp")
            if len(file_split) > 1:
                object_name = file_split[1]
    try:
        mime = magic.Magic(mime=True)
    except Exception:
        mime = None

    # object name already has preceding / (file_separator)
    object_name = "local" + object_name
    # Upload the file
    # todo calculate mimetype in future
    mimetype = mime.from_file(file_name)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=config.S3_AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.S3_AWS_SECRET_ACCESS_KEY,
        region_name=config.S3_REGION_NAME,
    )
    try:
        response = s3_client.upload_file(
            file_name,
            bucket,
            object_name,
            ExtraArgs={"ContentType": mimetype, "ContentDisposition": "attachment"},
        )
        object_name = "/" + object_name
    except Exception as e:
        object_name = "/" + object_name
        logger.error(msg="s3_file_upload_error", extra={"error": str(e)})
        return {"success": False, "file_path": object_name}
    return {"success": True, "file_path": object_name}
