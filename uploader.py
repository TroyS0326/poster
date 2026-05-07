import os


def upload_image(local_path: str, config):
    if not config.img_public_url_base:
        raise ValueError("IMG_PUBLIC_URL_BASE is required")
    base = config.img_public_url_base.rstrip("/") + "/"
    return base + os.path.basename(local_path)
