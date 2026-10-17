from django.conf import settings
from django.core.exceptions import ValidationError
from PIL import Image

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "WEBP"}


def validate_image_upload(file) -> None:
    """
    Reject oversized files and anything that is not a real raster image.

    Saving a file to an ImageField does not validate it, so without this an
    "avatar" could be HTML or SVG served back from our own media domain.
    """
    max_bytes = settings.MAX_IMAGE_UPLOAD_BYTES
    if file.size > max_bytes:
        raise ValidationError(f"Image is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.")

    try:
        with Image.open(file) as image:
            image_format = image.format
            image.verify()
    except Exception:
        raise ValidationError("Upload a valid JPEG, PNG, GIF or WebP image.") from None
    finally:
        file.seek(0)

    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Upload a valid JPEG, PNG, GIF or WebP image.")
