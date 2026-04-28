import requests

def post_to_meta(caption, image_url, config):
    # Post to Facebook Page
    fb_endpoint = f"https://graph.facebook.com/v20.0/{config['FB_PAGE_ID']}/photos"
    fb_payload = {
        "caption": caption,
        "url": image_url,
        "access_token": config['META_ACCESS_TOKEN']
    }
    fb_resp = requests.post(fb_endpoint, data=fb_payload).json()

    # Post to Instagram (container, then publish)
    ig_container_url = f"https://graph.facebook.com/v20.0/{config['IG_BUSINESS_ID']}/media"
    ig_publish_url = f"https://graph.facebook.com/v20.0/{config['IG_BUSINESS_ID']}/media_publish"
    media_payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": config['META_ACCESS_TOKEN']
    }
    media_resp = requests.post(ig_container_url, data=media_payload).json()
    creation_id = media_resp.get("id")
    publish_resp = {}
    if creation_id:
        publish_resp = requests.post(ig_publish_url, data={
            "creation_id": creation_id,
            "access_token": config['META_ACCESS_TOKEN']
        }).json()
    return {"fb": fb_resp, "ig": publish_resp}
