import os
import requests

GRAPH_VERSION = os.getenv("META_GRAPH_VERSION", "v20.0")


def _mask_token(token: str) -> str:
    if not token:
        return "missing"
    if len(token) <= 8:
        return "set:****"
    return f"set:{token[:4]}...{token[-4:]}"


def _graph_get(path: str, token: str, graph_version: str) -> tuple[bool, dict]:
    url = f"https://graph.facebook.com/{graph_version}/{path.lstrip('/')}"
    try:
        res = requests.get(url, params={"access_token": token}, timeout=20)
        data = res.json()
    except Exception as exc:
        return False, {"error": str(exc)}
    if not res.ok or (isinstance(data, dict) and data.get("error")):
        return False, data
    return True, data


def run_preflight(env: dict | None = None) -> dict:
    env = os.environ if env is None else env
    graph_version = env.get("META_GRAPH_VERSION", os.getenv("META_GRAPH_VERSION", "v20.0"))
    token = env.get("META_ACCESS_TOKEN", "")
    fb = env.get("FB_PAGE_ID", "")
    ig = env.get("IG_BUSINESS_ID", "")
    out = {
        "token": _mask_token(token),
        "graph_version": graph_version,
        "fb_page_id": "invalid",
        "ig_business_id": "invalid",
    }
    if not token or not fb or not ig:
        return out
    fb_ok, fb_data = _graph_get(f"{fb}?fields=id,name", token, graph_version)
    ig_ok, ig_data = _graph_get(f"{ig}?fields=id,username", token, graph_version)
    out["fb_page_id"] = "valid" if fb_ok and fb_data.get("id") else "invalid"
    out["ig_business_id"] = "valid" if ig_ok and ig_data.get("id") else "invalid"
    return out


def main() -> int:
    result = run_preflight()
    print(f"META_ACCESS_TOKEN: {result['token']}")
    print(f"graph version: {result['graph_version']}")
    print(f"FB_PAGE_ID: {result['fb_page_id']}")
    print(f"IG_BUSINESS_ID: {result['ig_business_id']}")
    return 0 if result["fb_page_id"] == "valid" and result["ig_business_id"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
