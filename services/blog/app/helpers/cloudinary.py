import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.core.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB   = 5


async def upload_cover_image(file: UploadFile, post_id: str) -> dict:
    """
    Uploads a post cover image to soko/blog/covers/{post_id}.
    Returns { url, public_id }.
    Used for Post.image — the hero image shown on cards and at top of post.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename} must be jpeg, png or webp"
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {MAX_SIZE_MB}MB limit"
        )

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=f"soko/blog/covers/{post_id}",
            public_id="cover",
            overwrite=True,
            transformation=[
                {
                    "width":        1200,
                    "height":       630,    # standard OG image ratio
                    "crop":         "fill",
                    "gravity":      "auto",
                    "quality":      "auto:good",
                    "fetch_format": "auto",
                }
            ],
            # Thumbnail for card previews
            eager=[
                {
                    "width":        600,
                    "height":       400,
                    "crop":         "fill",
                    "gravity":      "auto",
                    "quality":      "auto",
                    "fetch_format": "auto",
                }
            ],
            eager_async=True,
        )
        return {
            "url":       result["secure_url"],
            "public_id": result["public_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover upload failed: {str(e)}")


async def upload_body_image(file: UploadFile, post_id: str, order: int) -> dict:
    """
    Uploads an inline body image to soko/blog/body/{post_id}.
    Returns { url, public_id }.
    Used for PostSection items where type='image'.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"{file.filename} must be jpeg, png or webp"
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds {MAX_SIZE_MB}MB limit"
        )

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder=f"soko/blog/body/{post_id}",
            public_id=f"image_{order}",
            overwrite=True,
            transformation=[
                {
                    "width":        900,
                    "crop":         "limit",   # never upscale
                    "quality":      "auto:good",
                    "fetch_format": "auto",
                }
            ],
        )
        return {
            "url":       result["secure_url"],
            "public_id": result["public_id"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Body image upload failed: {str(e)}")


def delete_post_images(post_id: str):
    """
    Deletes all Cloudinary images for a post — covers and body images.
    Called when a post is deleted.
    """
    for folder in (f"soko/blog/covers/{post_id}", f"soko/blog/body/{post_id}"):
        try:
            cloudinary.uploader.destroy(folder, resource_type="image", invalidate=True)
        except Exception:
            pass


def delete_image_by_public_id(public_id: str):
    """Deletes a single image by its Cloudinary public_id."""
    try:
        cloudinary.uploader.destroy(public_id, invalidate=True)
    except Exception:
        pass