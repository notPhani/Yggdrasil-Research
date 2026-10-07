from ygg.config import cfg_hash, load_config


def test_cfg_hash_is_stable_and_ignores_paths():
    a = load_config()
    b = load_config()
    assert cfg_hash(a) == cfg_hash(b)
    b["paths"]["data_dir"] = "/elsewhere"
    assert cfg_hash(a) == cfg_hash(b)
    b["replay"]["start"] = "2024-12-17"
    assert cfg_hash(a) != cfg_hash(b)
