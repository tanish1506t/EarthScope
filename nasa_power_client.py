"""
NASA POWER API Client
Fetches daily point solar and meteorological data from the NASA POWER API v2.
Reference: https://power.larc.nasa.gov/docs/services/api/temporal/daily/point/
"""

import os
import json
import hashlib
import time
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple, Union
import requests

from earthscope.config import (
    NASA_POWER_BASE_URL,
    DEFAULT_COMMUNITY,
    NASA_FILL_VALUE,
    PARAMETERS_META
)

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")


class NASADataRetrievalError(Exception):
    """Custom exception raised when NASA API request or data parsing fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class NASAPowerClient:
    """
    Client for NASA POWER Daily Point API with caching, retry logic, and validation.
    """

    def __init__(self, cache_enabled: bool = True, cache_dir: str = CACHE_DIR, timeout_seconds: int = 25):
        self.cache_enabled = cache_enabled
        self.cache_dir = cache_dir
        self.timeout = timeout_seconds
        if self.cache_enabled:
            os.makedirs(self.cache_dir, exist_ok=True)

    def _generate_cache_key(self, lat: float, lon: float, start_str: str, end_str: str, parameters: List[str]) -> str:
        param_sorted = sorted(parameters)
        payload = f"{lat:.4f}_{lon:.4f}_{start_str}_{end_str}_{'_'.join(param_sorted)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _get_cache_path(self, cache_key: str) -> str:
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _read_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        if not self.cache_enabled:
            return None
        cache_path = self._get_cache_path(cache_key)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data["_from_cache"] = True
                    return data
            except Exception as e:
                logger.warning(f"Cache read error for key {cache_key}: {e}")
                return None
        return None

    def _write_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        if not self.cache_enabled:
            return
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to write cache key {cache_key}: {e}")

    @staticmethod
    def validate_inputs(lat: float, lon: float, start: Union[str, date, datetime], end: Union[str, date, datetime]) -> Tuple[str, str]:
        """Validates geographic coordinates and date ranges."""
        if not (-90.0 <= lat <= 90.0):
            raise ValueError(f"Latitude must be between -90 and 90 degrees. Received: {lat}")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError(f"Longitude must be between -180 and 180 degrees. Received: {lon}")

        def to_str(dt: Union[str, date, datetime]) -> str:
            if isinstance(dt, (date, datetime)):
                return dt.strftime("%Y%m%d")
            cleaned = str(dt).replace("-", "").strip()
            if len(cleaned) != 8 or not cleaned.isdigit():
                raise ValueError(f"Invalid date format: {dt}. Expected YYYYMMDD or YYYY-MM-DD.")
            return cleaned

        start_str = to_str(start)
        end_str = to_str(end)

        if start_str > end_str:
            raise ValueError(f"Start date ({start_str}) cannot be chronologically after end date ({end_str}).")

        # Sanity check year limits
        start_year = int(start_str[:4])
        end_year = int(end_str[:4])
        if start_year < 1981:
            raise ValueError(f"NASA POWER modern meteorological records start at 1981. Received: {start_year}")
        current_year = datetime.now().year + 1
        if end_year > current_year:
            raise ValueError(f"End year {end_year} exceeds current temporal coverage.")

        return start_str, end_str

    def fetch_daily_data(
        self,
        lat: float,
        lon: float,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime],
        parameters: Optional[List[str]] = None,
        force_refresh: bool = False,
        community: str = DEFAULT_COMMUNITY,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Fetches daily time-series from NASA POWER API.
        
        Returns parsed dictionary containing:
        - metadata: retrieval info, timestamps, units
        - parameters: dict of parameter name -> {YYYYMMDD: value}
        - status: success / cache / error details
        """
        if parameters is None:
            parameters = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN", "TS", "GWETROOT", "RH2M", "WS2M"]

        start_str, end_str = self.validate_inputs(lat, lon, start_date, end_date)
        cache_key = self._generate_cache_key(lat, lon, start_str, end_str, parameters)

        if not force_refresh:
            cached_data = self._read_from_cache(cache_key)
            if cached_data is not None:
                cached_data["_retrieval_mode"] = "cached"
                return cached_data

        params_joined = ",".join(parameters)
        query_params = {
            "parameters": params_joined,
            "community": community,
            "longitude": f"{lon:.4f}",
            "latitude": f"{lat:.4f}",
            "start": start_str,
            "end": end_str,
            "format": "JSON",
            "user": "EarthScopeCodeRex"
        }

        url = NASA_POWER_BASE_URL
        headers = {
            "User-Agent": "EarthScope-NASA-SpaceApps-2026/1.0 (Team CodeRex; Educational/Scientific)"
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                t0 = time.time()
                response = requests.get(url, params=query_params, headers=headers, timeout=self.timeout)
                elapsed = time.time() - t0

                if response.status_code == 200:
                    payload = response.json()
                    # Validate payload structure
                    if "properties" not in payload or "parameter" not in payload["properties"]:
                        messages = payload.get("messages", [])
                        raise NASADataRetrievalError(
                            f"NASA POWER API returned unexpected JSON structure. Messages: {messages}",
                            status_code=200,
                            details={"messages": messages}
                        )

                    payload["_retrieval_metadata"] = {
                        "retrieved_at": datetime.utcnow().isoformat() + "Z",
                        "elapsed_seconds": round(elapsed, 3),
                        "latitude": lat,
                        "longitude": lon,
                        "start_date": start_str,
                        "end_date": end_str,
                        "requested_parameters": parameters,
                        "api_url": response.url,
                        "source": "NASA Langley Research Center POWER Project"
                    }
                    payload["_retrieval_mode"] = "live_api"

                    self._write_to_cache(cache_key, payload)
                    return payload

                elif response.status_code in (400, 422):
                    # Client-side issue or parameter invalidation
                    err_msg = f"NASA POWER API rejected request (HTTP {response.status_code}): {response.text[:300]}"
                    raise NASADataRetrievalError(err_msg, status_code=response.status_code)

                elif response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"NASA POWER server returned {response.status_code}. Attempt {attempt}/{max_retries}. Retrying in {attempt * 2}s...")
                    time.sleep(attempt * 2)
                    last_error = f"HTTP {response.status_code}: {response.text[:150]}"
                    continue
                else:
                    raise NASADataRetrievalError(
                        f"NASA POWER API request failed with status code {response.status_code}: {response.text[:200]}",
                        status_code=response.status_code
                    )

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as net_err:
                logger.warning(f"Network error on attempt {attempt}/{max_retries}: {net_err}")
                last_error = str(net_err)
                if attempt < max_retries:
                    time.sleep(attempt * 2)
                    continue
                else:
                    raise NASADataRetrievalError(
                        f"Connection to NASA POWER API timed out after {max_retries} attempts. Check your internet connectivity or NASA API server status.",
                        details={"original_error": str(net_err)}
                    )

        raise NASADataRetrievalError(
            f"Failed to fetch data from NASA POWER API after {max_retries} attempts. Last error: {last_error}",
            details={"last_error": last_error}
        )

    def clear_cache(self) -> int:
        """Deletes all cached query responses and returns count of removed files."""
        if not os.path.exists(self.cache_dir):
            return 0
        count = 0
        for f in os.listdir(self.cache_dir):
            if f.endswith(".json"):
                try:
                    os.remove(os.path.join(self.cache_dir, f))
                    count += 1
                except Exception:
                    pass
        return count
