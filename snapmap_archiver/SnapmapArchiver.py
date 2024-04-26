import json
import os
import re
import sys
import typing as t
from datetime import datetime
from time import sleep

import requests

from snapmap_archiver.coordinates import Coordinates
from snapmap_archiver.snap import Snap, SnapJSONEncoder
from snapmap_archiver.time import since_epoch

DEFAULT_RADIUS = 10_000
MAX_RADIUS = 85_000
ISSUES_URL = "https://github.com/king-millez/snapmap-archiver/issues/new/choose"
SNAP_PATTERN = re.compile(
    r"(?:https?:\/\/map\.snapchat\.com\/ttp\/snap\/)?(W7_(?:[a-zA-Z0-9\-_\+]{56})(?:\/?@-?[0-9]{1,3}\.?[0-9]{0,},-?[0-9]{1,3}\.?[0-9]{0,}(?:,[0-9]{1,3}\.?[0-9]{0,}z))?)"
)


class SnapmapArchiver:
    def __init__(
        self,
        *args: str,
        output_dir: str,
        input_file: t.Optional[str] = None,
        since_time: t.Optional[str] = None,
        locations: list[str] = [],
        radius: int = DEFAULT_RADIUS,
        write_json: bool = False,
        zoom_depth: int = 5,
    ) -> None:
        if sys.version_info < (3, 10):
            raise RuntimeError(
                "Python 3.10 or above is required to use snapmap-archiver!"
            )

        self.since_time = None
        if since_time:
            self.since_time = since_epoch(since_time)
            print(f"Skipping Snaps older than [{self.since_time}].")

        self.input_file = input_file
        self.arg_snaps = args

        self.write_json = write_json
        self.zoom_depth = zoom_depth
        self.all_snaps: dict[str, Snap] = {}

        if not locations and not args and not input_file:
            raise ValueError(
                "Some sort of input is required. Run snapmap-archiver with [-h] to see a list of options."
            )

        self.output_dir = os.path.expanduser(output_dir)
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        self.radius = MAX_RADIUS if radius > MAX_RADIUS else radius
        self.coords_list = [Coordinates(latlon) for latlon in locations]

    def download_snaps(self, group: t.Iterable[Snap]):
        for snap in group:
            fpath = os.path.join(self.output_dir, f"{snap.snap_id}.{snap.file_type}")

            if os.path.isfile(fpath):
                print(f" - [{fpath}] already exists.")
                continue

            with open(fpath, "wb") as f:
                f.write(requests.get(snap.url).content)

            print(f" - Downloaded [{fpath}].")

    def query_snaps(self, snaps: t.Iterable[str]) -> list[Snap]:
        to_query: list[str] = []
        for snap_id in snaps:
            rgx_match = re.search(
                SNAP_PATTERN,
                snap_id,
            )
            if not rgx_match:
                print(f" - [{snap_id}] is not a valid Snap URL or ID.")
                continue
            to_query.append(rgx_match.group(1))

        if not to_query:
            return []

        api_response = requests.post(
            "https://ms.sc-jpl.com/web/getStoryElements",
            json={"snapIds": to_query},
        )
        try:
            retl: list[Snap] = []
            for snap in api_response.json().get("elements", []):
                s = self._parse_snap(snap)
                if s:
                    retl.append(s)
            return retl
        except requests.exceptions.JSONDecodeError as e:
            print(
                f"Encountered error while querying Snap IDs:\n[{e}]. API Response: [{api_response.text}]."
            )
            return []

    def query_coords(self, coords: Coordinates):
        to_download: dict[str, Snap] = {}
        current_iteration = self.radius
        epoch = self._get_epoch()
        while current_iteration != 1:
            print(f"Querying with radius [{current_iteration}]...")
            json_data = None
            while not json_data:
                api_data = requests.post(
                    "https://ms.sc-jpl.com/web/getPlaylist",
                    headers={
                        "Content-Type": "application/json",
                    },
                    json={
                        "requestGeoPoint": {"lat": coords.lat, "lon": coords.long},
                        "zoomLevel": self.zoom_depth,
                        "tileSetId": {"flavor": "default", "epoch": epoch, "type": 1},
                        "radiusMeters": current_iteration,
                        "maximumFuzzRadius": 0,
                    },
                ).text

                if api_data:
                    if api_data.strip() == "Too many requests":
                        print("You have been rate limited. Sleeping for 1 minute.")
                        sleep(60)
                    else:
                        try:
                            json_data = json.loads(api_data)["manifest"]["elements"]
                        except requests.exceptions.JSONDecodeError:
                            print(
                                f"Unable to decode API response (likely a rate limit): [{api_data}] Sleeping for 1 minute."
                            )
                            sleep(60)

            for snap in json_data:
                if to_download.get(
                    snap["id"]
                ):  # Avoids downloading duplicates. Faster than a list because the Snap ID is indexed
                    continue

                parsed = self._parse_snap(snap)

                if not parsed:
                    continue

                to_download[snap["id"]] = parsed

            if current_iteration > 2000:
                current_iteration -= 2000
            elif current_iteration > 1000:
                current_iteration -= 100
            else:
                current_iteration = 1

        print(f"Found [{len(list(to_download.keys()))}] Snaps.")
        return to_download.values()

    def main(self):
        # Query provided coordinates
        for coords in self.coords_list:
            self.download_snaps(self.query_coords(coords))

        snap_ids = []

        # Download Snaps from input file
        if self.input_file:
            if os.path.isfile(self.input_file):
                with open(self.input_file, "r") as f:
                    snap_ids = [ln for ln in f.read().split("\n") if ln.strip()]
            else:
                raise FileNotFoundError(
                    f"Input file [{self.input_file}] does not exist."
                )

        snap_ids.extend(self.arg_snaps)

        # Download Snaps provided from the command line
        self.download_snaps(self.query_snaps(snap_ids))

        if self.write_json:
            with open(
                os.path.join(
                    self.output_dir, f"archive_{int(datetime.now().timestamp())}.json"
                ),
                "w",
            ) as f:
                json.dump(
                    list(self.all_snaps.values()),
                    f,
                    indent=2,
                    cls=SnapJSONEncoder,
                )

    def _parse_snap(
        self,
        snap: dict[
            str, t.Any
        ],  # I don't like the Any type but this dict is so dynamic there isn't much point hinting it accurately.
    ) -> Snap | None:
        if self.all_snaps.get(snap["id"]):
            return self.all_snaps[snap["id"]]

        file_type = (
            "mp4"
            if snap["snapInfo"].get("snapMediaType")
            else "jpg"
            if snap["snapInfo"].get("streamingMediaInfo")
            else "UNKNOWN"
        )

        url: str | None = snap["snapInfo"]["streamingMediaInfo"].get("mediaUrl")
        if not url:
            print(f'Media URL for snap [{snap["id"]}] could not be determined.')
            return None

        create_time = round(int(snap["timestamp"]) * 10**-3, 3)

        if (self.since_time) and (create_time < self.since_time):
            print(
                f" - [{snap['id']}] is older than the specified time of [{self.since_time}]. Snap timestamp: [{int(create_time)}]. Skipping."
            )
            return None

        s = Snap(
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

        self.all_snaps[snap["id"]] = s

        return s

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
