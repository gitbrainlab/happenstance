from typing import Dict, Mapping


def build_live_search_params(config: Mapping) -> Dict:
    live_cfg = dict(config.get("live_search", {}))
    params = {
        "mode": live_cfg.get("mode", "local"),
        "radius_km": live_cfg.get("radius_km", 5),
        "radius_miles": live_cfg.get("radius_miles", live_cfg.get("radius_km", 5) / 1.609344),
        "limit": live_cfg.get("limit", 10),
    }
    for key in ["query", "target_area", "target_zip", "center"]:
        if key in live_cfg:
            params[key] = live_cfg[key]
    return params
