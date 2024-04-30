import asyncio
import json
import os
import sys
import typing as t
from datetime import datetime
from time import sleep

import aiofiles
import httpx
import requests
from alive_progress import alive_bar
from loguru._logger import Logger

from snapmap_archiver import (
    DEFAULT_API_HOST,
    DEFAULT_RADIUS,
    DEFAULT_WRITE_JSON,
    DEFAULT_ZOOM_DEPTH,
    ISSUES_URL,
    default_output_dir,
)
from snapmap_archiver.coordinates import Coordinates
from snapmap_archiver.snap import Snap, SnapJSONEncoder
from snapmap_archiver.time import since_epoch

MAX_RADIUS = 85_000


class SnapmapArchiver:
    def __init__(
        self,
        logger: Logger,
        output_dir: str = default_output_dir,
        since_time: t.Optional[str] = None,
        write_json: bool = DEFAULT_WRITE_JSON,
        api_host: str = DEFAULT_API_HOST,
    ) -> None:
        if sys.version_info < (3, 10):
            raise RuntimeError(
                "Python 3.10 or above is required to use snapmap-archiver!"
            )

        self.logger = logger
        self.api_host = api_host
        self.output_dir = os.path.expanduser(output_dir)
        self.write_json = write_json

        self.since_time = None
        if since_time:
            self.since_time = since_epoch(since_time.lower())
            self.logger.info(f"Skipping Snaps older than [{self.since_time}].")

        self.snap_cache: dict[str, Snap] = {}

        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def _is_cached(self, snap_id: str) -> bool:
        return snap_id in self.snap_cache

    async def _batched_download(
        self, snap_url: str, output_path: str, bar: t.Any, client: httpx.AsyncClient
    ):
        if os.path.isfile(output_path):
            self.logger.debug(f" - [{output_path}] already exists.")
            bar()
            return

        async with aiofiles.open(output_path, "wb") as f:
            await f.write((await client.get(snap_url)).content)

        self.logger.debug(f" - Downloaded [{output_path}].")
        bar()

    def download_cached_snaps(self):
        with alive_bar(
            len(self.snap_cache), title=f"Downloading to [{self.output_dir}]..."
        ) as bar:
            all_snaps = list(self.snap_cache.values())
            client = httpx.AsyncClient()
            for snap_chunk in [
                all_snaps[i : i + 20]
                for i in range(
                    0, len(all_snaps), 20
                )  # 20 connections seems to be ok with rate limits.
            ]:
                asyncio.get_event_loop().run_until_complete(
                    asyncio.gather(
                        *[
                            self._batched_download(
                                snap.url,
                                os.path.join(
                                    self.output_dir, f"{snap.snap_id}.{snap.file_type}"
                                ),
                                bar,
                                client,
                            )
                            for snap in snap_chunk
                        ]
                    )
                )

        if self.write_json:
            with open(
                os.path.join(
                    self.output_dir, f"archive_{int(datetime.now().timestamp())}.json"
                ),
                "w",
            ) as f:
                json.dump(
                    list(self.snap_cache.values()),
                    f,
                    indent=2,
                    cls=SnapJSONEncoder,
                )

    def query_snaps(self, snaps: t.Iterable[str]) -> list[Snap]:
        to_query = [snap_id for snap_id in snaps if not self._is_cached(snap_id)]
        if not to_query:
            return []

        api_response = requests.post(
            f"{self.api_host}/web/getStoryElements",
            json={"snapIds": to_query},
        )

        try:
            parsed_snaps: list[Snap] = []
            for snap in api_response.json().get("elements", []):
                s = self._parse_snap(snap)
                if s:
                    parsed_snaps.append(s)
            return parsed_snaps
        except requests.exceptions.JSONDecodeError as e:
            self.logger.warning(
                f"Encountered error while querying Snap IDs:\n[{e}]. API Response: [{api_response.text}]."
            )
            return []

    def query_coords(
        self,
        coords: Coordinates,
        zoom_depth: int = DEFAULT_ZOOM_DEPTH,
        requested_radius: int = DEFAULT_RADIUS,
    ) -> list[Snap]:
        if requested_radius > MAX_RADIUS:
            radius = MAX_RADIUS
            self.logger.info(
                f"Radius cannot be larger than [{MAX_RADIUS}]. Using [{MAX_RADIUS}] as the radius value."
            )
        else:
            radius = requested_radius

        current_iteration = radius
        epoch = self._get_epoch()
        found_snaps = []
        with alive_bar(
            radius, manual=True, title=f"Location: {coords.__repr__()}"
        ) as bar:
            while current_iteration != 1:
                snaps_from_coords = None
                while not snaps_from_coords:
                    api_response = requests.post(
                        f"{self.api_host}/web/getPlaylist",
                        headers={
                            "Content-Type": "application/json",
                        },
                        json={
                            "requestGeoPoint": {"lat": coords.lat, "lon": coords.long},
                            "zoomLevel": zoom_depth,
                            "tileSetId": {
                                "flavor": "default",
                                "epoch": epoch,
                                "type": 1,
                            },
                            "radiusMeters": current_iteration,
                            "maximumFuzzRadius": 0,
                        },
                    ).text

                    if not api_response:
                        self._coordinate_query_failure("No response received.")
                    elif api_response.strip() == "Too many requests":
                        self._coordinate_query_failure("You have been rate limited.")
                    else:
                        try:
                            snaps_from_coords = json.loads(api_response)["manifest"][
                                "elements"
                            ]
                        except json.JSONDecodeError:
                            self._coordinate_query_failure(
                                f"Unable to decode API response (likely a rate limit): [{api_response}]."
                            )

                for snap in snaps_from_coords:
                    if self._is_cached(snap["id"]):
                        found_snaps.append(self.snap_cache[snap["id"]])
                        continue

                    parsed = self._parse_snap(snap)
                    if not parsed:
                        continue

                    self.snap_cache[snap["id"]] = parsed
                    found_snaps.append(parsed)

                if current_iteration > 2000:
                    current_iteration -= 2000
                elif current_iteration > 1000:
                    current_iteration -= 100
                else:
                    current_iteration = 1
                bar(
                    (radius - current_iteration) / radius
                    if current_iteration != 1
                    else 1
                )

        return found_snaps

    def _coordinate_query_failure(self, msg: str, sleep_seconds: int = 60):
        self.logger.warning(f"{msg} Sleeping for [{sleep_seconds}] seconds...")
        sleep(sleep_seconds)

    def _parse_snap(
        self,
        snap: dict[
            str, t.Any
        ],  # I don't like the Any type but this dict is so dynamic there isn't much point hinting it accurately.
    ) -> Snap | None:
        if self.snap_cache.get(snap["id"]):
            return self.snap_cache[snap["id"]]

        file_type = (
            "mp4"
            if snap["snapInfo"].get("snapMediaType")
            else "jpg"
            if snap["snapInfo"].get("streamingMediaInfo")
            else "UNKNOWN"
        )

        url: str | None = snap["snapInfo"]["streamingMediaInfo"].get("mediaUrl")
        if not url:
            self.logger.warning(
                f'Media URL for snap [{snap["id"]}] could not be determined.'
            )
            return None

        create_time = round(int(snap["timestamp"]) * 10**-3, 3)

        if (self.since_time) and (create_time < self.since_time):
            self.logger.debug(
                f" - [{snap['id']}] is older than the specified time of [{self.since_time}]. Snap timestamp: [{int(create_time)}]. Skipping."
            )
            return None

        parsed_snap = Snap(
            create_time=create_time,  # type: ignore
            snap_id=snap["id"],
            url=url,
            file_type=file_type,
            location=snap["snapInfo"]
            .get("title", {})
            .get(
                "fallback",
                snap["snapInfo"].get("localitySubtitle", {}).get("fallback", "UNKNOWN"),
            ),
        )

        self.snap_cache[snap["id"]] = parsed_snap

        return parsed_snap

    def _get_epoch(self):
        epoch_endpoint = requests.post(
            "https://ms.sc-jpl.com/web/getLatestTileSet",
            headers={"Content-Type": "application/json"},
            json={},
        ).json()

        if epoch_endpoint:
            for entry in epoch_endpoint["tileSetInfos"]:
                if entry["id"]["type"] == "HEAT":
                    return entry["id"]["epoch"]
        else:
            raise self.MissingEpochError(
                f"The API epoch could not be obtained.\n\nPlease report this at [{ISSUES_URL}]."
            )

    class MissingEpochError(Exception):
        pass
