import meta_preflight


def test_preflight_missing_env_masks_token_and_invalid_ids():
    result = meta_preflight.run_preflight(env={})
    assert result["token"] == "missing"
    assert result["fb_page_id"] == "invalid"
    assert result["ig_business_id"] == "invalid"


def test_preflight_masks_token_and_validates(monkeypatch):
    def fake_graph_get(path, token):
        if "fields=id,name" in path:
            return True, {"id": "123", "name": "Page"}
        return True, {"id": "456", "username": "acct"}

    monkeypatch.setattr(meta_preflight, "_graph_get", fake_graph_get)
    result = meta_preflight.run_preflight(env={"META_ACCESS_TOKEN": "abcd1234wxyz9999", "FB_PAGE_ID": "123", "IG_BUSINESS_ID": "456"})
    assert result["token"].startswith("set:")
    assert "1234" not in result["token"]
    assert result["fb_page_id"] == "valid"
    assert result["ig_business_id"] == "valid"
