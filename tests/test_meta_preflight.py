import meta_preflight


def test_preflight_missing_env_masks_token_and_invalid_ids():
    result = meta_preflight.run_preflight(env={})
    assert result["token"] == "missing"
    assert result["fb_page_access_token"] == "missing"
    assert result["fb_page_id"] == "invalid"
    assert result["ig_business_id"] == "invalid"


def test_preflight_masks_token_and_validates(monkeypatch):
    def fake_graph_get(path, token, graph_version):
        assert graph_version == "v99.0"
        if "fields=id,name" in path:
            return True, {"id": "123", "name": "Page"}
        return True, {"id": "456", "username": "acct"}

    monkeypatch.setattr(meta_preflight, "_graph_get", fake_graph_get)
    result = meta_preflight.run_preflight(
        env={
            "META_ACCESS_TOKEN": "abcd1234wxyz9999",
            "FB_PAGE_ID": "123",
            "IG_BUSINESS_ID": "456",
            "META_GRAPH_VERSION": "v99.0",
        }
    )
    assert result["token"].startswith("set:")
    assert "1234" not in result["token"]
    assert result["graph_version"] == "v99.0"
    assert result["fb_page_id"] == "valid"
    assert result["ig_business_id"] == "valid"


def test_preflight_uses_fb_page_access_token_for_facebook_only(monkeypatch):
    calls = []

    def fake_graph_get(path, token, graph_version):
        calls.append((path, token, graph_version))
        return True, {"id": "123"}

    monkeypatch.setattr(meta_preflight, "_graph_get", fake_graph_get)
    result = meta_preflight.run_preflight(
        env={
            "META_ACCESS_TOKEN": "meta_token_12345678",
            "FB_PAGE_ACCESS_TOKEN": "fb_page_token_87654321",
            "FB_PAGE_ID": "123",
            "IG_BUSINESS_ID": "456",
            "META_GRAPH_VERSION": "v20.0",
        }
    )
    assert result["fb_page_id"] == "valid"
    assert result["ig_business_id"] == "valid"
    assert result["fb_page_access_token"].startswith("set:")
    fb_call = next(c for c in calls if "fields=id,name" in c[0])
    ig_call = next(c for c in calls if "fields=id,username" in c[0])
    assert fb_call[1] == "fb_page_token_87654321"
    assert ig_call[1] == "meta_token_12345678"
