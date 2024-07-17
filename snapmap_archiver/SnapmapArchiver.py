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
        debug_mode=False,
    ) -> None:
        if sys.version_info < (3, 10):
            raise RuntimeError(
                "Python 3.10 or above is required to use snapmap-archiver!"
            )

        self.debug_mode = debug_mode
        self.logger = logger
        self.api_host = api_host
        self.output_dir = os.path.expanduser(output_dir)
        self.write_json = write_json

        self.since_time = None
        if since_time:
            self.since_time = since_epoch(since_time.lower())
            self.logger.info(f"Skipping Snaps older than [{self.since_time}].")

        self.snap_cache: dict[str, Snap] = {}

        # Debug metrics
        self.query_count = 0
        self.download_count = 0
        self.direct_query_count = 0

        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def _is_cached(self, snap_id: str) -> bool:
        if snap_id in self.snap_cache:
            self.logger.debug(f"[{snap_id}] found in cache.")
            return True

        return False  # Sometimes you have to make the code ugly for logs :(

    async def _batched_download(
        self, snap_url: str, output_path: str, bar: t.Any, client: httpx.AsyncClient
    ):
        self.logger.debug(f"Downloading [{snap_url}] to [{output_path}]; download count this session: [{self.download_count}]...")
        if os.path.isfile(output_path):
            self.logger.debug(f"[{output_path}] already exists.")
            bar()
            return

        async with aiofiles.open(output_path, "wb") as f:
            await f.write((await client.get(snap_url)).content)

        self.download_count += 1

        self.logger.debug(f"Downloaded [{output_path}].")
        bar()

    def download_cached_snaps(self):
        with alive_bar(
            len(self.snap_cache),
            title=f"Downloading to [{self.output_dir}]...",
            disable=self.debug_mode,
        ) as bar:
            all_snaps = list(self.snap_cache.values())
            self.logger.debug(
                f"Attempting to download [{len(all_snaps)}] cached Snaps..."
            )

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
            json_output_path = os.path.join(
                self.output_dir, f"archive_{int(datetime.now().timestamp())}.json"
            )
            self.logger.debug(f"Dumping output JSON to [{json_output_path}]...")
            with open(
                json_output_path,
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

        self.logger.debug(f"Uncached snap IDs to query: [{to_query}].")

        if not to_query:
            return []

        request_object = {
            "url": f"{self.api_host}/web/getStoryElements",
            "json": {"snapIds": to_query},
        }

        self.logger.debug(
            f"Running direct query with [{request_object=}]; direct queries this session: [{self.direct_query_count}]..."
        )

        api_response = requests.post(**request_object)

        self.direct_query_count += 1

        try:
            parsed_snaps: list[Snap] = []
            response_list = api_response.json().get("elements", [])
            self.logger.debug(
                f"Retrieved [{len(response_list)}] Snaps via direct query."
            )
            for snap in response_list:
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
            radius,
            manual=True,
            title=f"Location: {coords.__repr__()}",
            disable=self.debug_mode,
        ) as bar:
            while current_iteration != 1:
                self.logger.debug(f"[{current_iteration=}].")
                snaps_from_coords = None

                while snaps_from_coords is None:
                    request_object = {
                        "url": f"{self.api_host}/web/getPlaylist",
                        "headers": {
                            "Content-Type": "application/json",
                        },
                        "json": {
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
                    }
                    self.logger.debug(
                        f"Running snap query with [{request_object=}]; query count this session: [{self.query_count}]..."
                    )

                    api_response = requests.post(**request_object).text

                    self.query_count += 1

                    if not api_response:
                        self._coordinate_query_failure("No response received.")
                    elif api_response.strip() == "Too many requests":
                        self._coordinate_query_failure(
                            f"Received [{api_response.strip()}] from API."
                        )
                    else:
                        try:
                            snaps_from_coords = json.loads(api_response)["manifest"][
                                "elements"
                            ]
                            self.logger.debug(
                                f"Received [{len(snaps_from_coords)}] Snaps from query."
                            )
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
            else "jpg" if snap["snapInfo"].get("streamingMediaInfo") else "UNKNOWN"
        )

        self.logger.debug(f'[{snap["id"]}] file type [{file_type}].')

        url: str | None = snap["snapInfo"]["streamingMediaInfo"].get("mediaUrl")
        if not url:
            self.logger.warning(
                f'Media URL for snap [{snap["id"]}] could not be determined.'
            )
            return None

        self.logger.debug(f'[{snap["id"]}] media URL [{url}].')

        create_time = round(int(snap["timestamp"]) * 10**-3, 3)

        self.logger.debug(f'[{snap["id"]}] create time [{create_time}].')

        if (self.since_time) and (create_time < self.since_time):
            self.logger.debug(
                f"[{snap['id']}] is older than the specified time of [{self.since_time}]. Snap timestamp: [{int(create_time)}]. Skipping."
            )
            return None

        snap_location = (
            snap["snapInfo"]
            .get("title", {})
            .get(
                "fallback",
                snap["snapInfo"].get("localitySubtitle", {}).get("fallback", "UNKNOWN"),
            )
        )

        self.logger.debug(f'[{snap["id"]}] location [{snap_location}].')

        parsed_snap = Snap(
            create_time=create_time,  # type: ignore
            snap_id=snap["id"],
            url=url,
            file_type=file_type,
            location=snap_location,
        )

        self.snap_cache[snap["id"]] = parsed_snap

        self.logger.debug(f'Cached [{snap["id"]}].')

        return parsed_snap

    def _get_epoch(self):
        epoch_endpoint = "https://ms.sc-jpl.com/web/getLatestTileSet"

        self.logger.debug(f"Requesting [{epoch_endpoint}]...")

        epoch_response = requests.post(
            epoch_endpoint,
            headers={"Content-Type": "application/json"},
            json={},
        ).json()

        if epoch_response:
            self.logger.debug(f"[{epoch_response=}].")

            for entry in epoch_response["tileSetInfos"]:
                if entry["id"]["type"] == "HEAT":
                    self.logger.debug(f'Found epoch [{entry["id"]["epoch"]}].')
                    return entry["id"]["epoch"]

        raise self.MissingEpochError(
            f"The API epoch could not be obtained.\n\nPlease report this at [{ISSUES_URL}]. Include [{epoch_response=}] in your issue.."
        )

    def __repr__(self) -> str:
        return json.dumps(
            {
                "api_host": self.api_host,
                "output_dir": self.output_dir,
                "write_json": self.write_json,
                "since_time": self.since_time,
                "snap_cache": self.snap_cache,
                "debug_mode": self.debug_mode,
            },
            cls=SnapJSONEncoder,
        )

    class MissingEpochError(Exception):
        pass
