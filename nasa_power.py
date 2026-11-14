"""
NASA POWER API Service
Handles network requests to NASA Langley Research Center POWER API v2
with intelligent disk and memory TTL caching, bounded retries, and strict validation.
"""

import os
import json
import time
import hashlib
import calendar
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import httpx

from backend.app.config import settings, PARAMETERS_META

logger = logging.getLogger(__name__)

# In-memory fast cache with TTL
_MEMORY_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

class NASAPowerService:
    def __init__(self):
        self.cache_dir = settings.CACHE_DIR
        self.ttl = settings.CACHE_TTL_SECONDS
        os.makedirs(self.cache_dir, exist_ok=True)

    def _generate_cache_key(self, lat: float, lon: float, start: int, end: int, params: List[str], resolution: str) -> str:
        param_sorted = sorted(params)
        raw_key = f"{lat:.4f}_{lon:.4f}_{start}_{end}_{'_'.join(param_sorted)}_{resolution}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def _read_cache(self, key: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        # 1. Check memory cache
        if key in _MEMORY_CACHE:
            ts, data = _MEMORY_CACHE[key]
            if now - ts < self.ttl:
                data_copy = json.loads(json.dumps(data))
                data_copy["_from_cache"] = True
                data_copy["_cache_tier"] = "memory"
                return data_copy
            else:
                del _MEMORY_CACHE[key]

        # 2. Check disk cache
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_path):
            try:
                mtime = os.path.getmtime(cache_path)
                if now - mtime < self.ttl:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["_from_cache"] = True
                        data["_cache_tier"] = "disk"
                        _MEMORY_CACHE[key] = (now, data)
                        return data
                else:
                    # Expired
                    os.remove(cache_path)
            except Exception as e:
                logger.warning(f"Error reading disk cache {key}: {e}")
        return None

    def _write_cache(self, key: str, data: Dict[str, Any]) -> None:
        now = time.time()
        _MEMORY_CACHE[key] = (now, data)
        cache_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to write disk cache {key}: {e}")

    def get_cache_count(self) -> int:
        count = 0
        if os.path.exists(self.cache_dir):
            count = len([f for f in os.listdir(self.cache_dir) if f.endswith(".json")])
        return count

    async def fetch_monthly_data(
        self,
        lat: float,
        lon: float,
        start_year: int,
        end_year: int,
        parameters: Optional[List[str]] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieves monthly point data from NASA POWER API.
        """
        if parameters is None:
            parameters = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M", "TS", "WS2M"]

        cache_key = self._generate_cache_key(lat, lon, start_year, end_year, parameters, "monthly")
        if not force_refresh:
            cached = self._read_cache(cache_key)
            if cached:
                return cached

        params_joined = ",".join(parameters)
        url = settings.NASA_POWER_MONTHLY_URL
        query_params = {
            "parameters": params_joined,
            "community": settings.NASA_DEFAULT_COMMUNITY,
            "longitude": f"{lon:.4f}",
            "latitude": f"{lat:.4f}",
            "start": str(start_year),
            "end": str(end_year),
            "format": "JSON",
            "user": "EarthScopeApp"
        }

        headers = {
            "User-Agent": "EarthScope-NASA-SpaceApps-2026/2.0 (Scientific; FastAPI)"
        }

        t0 = time.time()
        async with httpx.AsyncClient(timeout=25.0) as client:
            last_err = None
            for attempt in range(1, 4):
                try:
                    resp = await client.get(url, params=query_params, headers=headers)
                    elapsed = time.time() - t0
                    if resp.status_code == 200:
                        payload = resp.json()
                        if "properties" not in payload or "parameter" not in payload["properties"]:
                            raise ValueError("Unexpected NASA POWER API JSON response structure")

                        payload["_retrieval_metadata"] = {
                            "retrieved_at": datetime.now(timezone.utc).isoformat(),
                            "elapsed_seconds": round(elapsed, 3),
                            "latitude": lat,
                            "longitude": lon,
                            "start_year": start_year,
                            "end_year": end_year,
                            "requested_parameters": parameters,
                            "source": "NASA Langley Research Center POWER Project",
                            "api_endpoint": str(resp.url)
                        }
                        self._write_cache(cache_key, payload)
                        return payload

                    elif resp.status_code in (400, 422):
                        raise RuntimeError(f"NASA POWER API validation error: {resp.text[:200]}")
                    else:
                        last_err = f"HTTP {resp.status_code}: {resp.text[:150]}"
                        time.sleep(attempt * 1.5)
                except httpx.RequestError as exc:
                    last_err = f"Request error: {exc}"
                    time.sleep(attempt * 1.5)

        # If live fetch fails, check if we have any stale cache or raise clear exception
        stale_cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(stale_cache_path):
            try:
                with open(stale_cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_from_cache"] = True
                    data["_stale_fallback"] = True
                    return data
            except Exception:
                pass

        raise RuntimeError(f"NASA POWER API unreachable after 3 attempts. Detail: {last_err}")

    async def check_api_health(self) -> bool:
        """Pings NASA POWER API to verify live upstream connectivity."""
        try:
            test_url = f"{settings.NASA_POWER_MONTHLY_URL}?parameters=T2M&community=AG&longitude=73.7898&latitude=19.9975&start=2024&end=2024&format=JSON"
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(test_url)
                return res.status_code == 200
        except Exception:
            return False

nasa_service = NASAPowerService()
