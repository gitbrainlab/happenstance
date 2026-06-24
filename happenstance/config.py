import copy
import json
import os
from pathlib import Path
from typing import Any, Dict

from .env import load_project_env

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config_logic.json"


def _load_raw_config() -> Dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(profile: str | None = None) -> Dict[str, Any]:
    """Load a profile configuration and apply environment overrides."""
    load_project_env()
    raw = _load_raw_config()
    profiles = raw.get("profiles", {})
    selected = profile or os.getenv("PROFILE") or "default"
    if selected not in profiles:
        raise ValueError(f"Profile '{selected}' not found in config.")

    config = copy.deepcopy(profiles[selected])
    live_search_mode = os.getenv("LIVE_SEARCH_MODE")
    if live_search_mode:
        config.setdefault("live_search", {})
        config["live_search"]["mode"] = live_search_mode

    event_window = os.getenv("EVENT_WINDOW_DAYS")
    if event_window:
        try:
            config["event_window_days"] = int(event_window)
        except ValueError as err:
            raise ValueError(f"EVENT_WINDOW_DAYS must be an integer, got: {event_window}") from err
    else:
        config["event_window_days"] = config.get("event_window_days", 14)

    base_url = os.getenv("BASE_URL")
    if base_url:
        config["base_url"] = base_url

    restaurant_source = os.getenv("RESTAURANT_SOURCE")
    if restaurant_source:
        config.setdefault("data_sources", {})
        config["data_sources"]["restaurants"] = restaurant_source

    event_source = os.getenv("EVENT_SOURCE")
    if event_source:
        config.setdefault("data_sources", {})
        config["data_sources"]["events"] = event_source

    target_area = os.getenv("TARGET_AREA")
    target_zip = os.getenv("TARGET_ZIP")
    target_label = target_area or target_zip
    target_lat = os.getenv("TARGET_LAT")
    target_lng = os.getenv("TARGET_LNG")
    if target_label or (target_lat and target_lng):
        live_search = config.setdefault("live_search", {})
        if target_area:
            live_search["target_area"] = target_area
        if target_zip:
            live_search["target_zip"] = target_zip

        center = _resolve_target_center(config, target_label)
        if target_lat and target_lng:
            try:
                center = {"lat": float(target_lat), "lng": float(target_lng)}
            except ValueError as err:
                raise ValueError("TARGET_LAT and TARGET_LNG must be numbers") from err
        if center:
            live_search["center"] = center

    search_radius = os.getenv("SEARCH_RADIUS_KM")
    if search_radius:
        try:
            config.setdefault("live_search", {})
            config["live_search"]["radius_km"] = float(search_radius)
        except ValueError as err:
            raise ValueError(f"SEARCH_RADIUS_KM must be a number, got: {search_radius}") from err

    search_radius_miles = os.getenv("SEARCH_RADIUS_MILES")
    if search_radius_miles:
        try:
            miles = float(search_radius_miles)
            config.setdefault("live_search", {})
            config["live_search"]["radius_miles"] = miles
            config["live_search"]["radius_km"] = miles * 1.609344
        except ValueError as err:
            raise ValueError(f"SEARCH_RADIUS_MILES must be a number, got: {search_radius_miles}") from err

    config["profile"] = selected
    return config


def _resolve_target_center(config: Dict[str, Any], target: str | None) -> Dict[str, float] | None:
    if not target:
        return None

    needle = target.strip().lower()
    for area in config.get("target_areas", []):
        names = [area.get("id", ""), area.get("name", ""), *area.get("aliases", []), *area.get("zips", [])]
        if needle in {str(name).strip().lower() for name in names if name}:
            center = area.get("center")
            if isinstance(center, dict) and "lat" in center and "lng" in center:
                return {"lat": float(center["lat"]), "lng": float(center["lng"])}
    return None
