import os

def upload_image(img_path, config):
    # If serving images locally, just return the public URL
    img_url = config['IMG_PUBLIC_URL_BASE'] + os.path.basename(img_path)
    return img_url
