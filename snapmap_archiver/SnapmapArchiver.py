import os
import re
import sys
import json
import requests
from time import sleep
from typing import Iterable, Any
from datetime import datetime

from snapmap_archiver.coordinates import Coordinates
from snapmap_archiver.snap import Snap, SnapJSONEncoder


class SnapmapArchiver:
    MAX_RADIUS = 85_000
    ISSUES_URL = "https://github.com/king-millez/snapmap-archiver/issues/new/choose"
    SNAP_PATTERN = re.compile(
        r"(?:https?:\/\/map\.snapchat\.com\/ttp\/snap\/)?(W7_(?:[aA-zZ0-9\-_\+]{22})(?:[aA-zZ0-9-_\+]{28})AAAAA[AQ])(?:\/?@-?[0-9]{1,3}\.?[0-9]{0,},-?[0-9]{1,3}\.?[0-9]{0,}(?:,[0-9]{1,3}\.?[0-9]{0,}z))?"
    )

    def __init__(self, *args, **kwargs) -> None:
        if sys.version_info < (3, 10):
            raise RuntimeError(
                "Python 3.10 or above is required to use snapmap-archiver!"
            )

        self.write_json = kwargs.get("write_json")
        self.all_snaps: dict[str, Snap] = {}
        self.arg_snaps = args
        self.coords_list = []
        self.radius = 10_000
        self.zoom_depth = (
            kwargs.get("zoom_depth") or 5
        )  # TODO change this 5 to a default const somewhere?
        self.input_file = ""

        if not kwargs["locations"] and not args and not kwargs["input_file"]:
            raise ValueError(
                "Some sort of input is required; location (-l), input file (-f), and raw Snap IDs are all valid options."
            )

        if not kwargs["output_dir"]:
            raise ValueError("Output directory (-o) is required.")

        self.output_dir = os.path.expanduser(kwargs["output_dir"])

        if not os.path.isdir(self.output_dir):
            os.makedirs(
                self.output_dir, exist_ok=True
            )  # Python's exception handling has us covered here

        if kwargs.get("radius"):
            self.radius = (
                self.MAX_RADIUS
                if kwargs["radius"] > self.MAX_RADIUS
                else kwargs["radius"]
            )

        # Query provided coordinates for Snaps
        if kwargs.get("locations"):
            self.coords_list = [
                Coordinates(latlon[0]) for latlon in kwargs["locations"]
            ]

        # Check input file for Snap IDs
        if kwargs.get("input_file"):
            self.input_file = kwargs["input_file"]

    def download_snaps(self, group: list[Snap] | Snap):
        if isinstance(group, Snap):
            group = [group]
        for snap in group:
            fpath = os.path.join(self.output_dir, f"{snap.snap_id}.{snap.file_type}")
            if os.path.isfile(fpath):
                print(f" - {fpath} already exists.")
                continue
            with open(fpath, "wb") as f:
                f.write(requests.get(snap.url).content)
            print(f" - Downloaded {fpath}.")

    def query_snaps(self, snaps: str | Iterable[str]) -> list[Snap]:
        if isinstance(snaps, str):
            snaps = [
                snaps
            ]  # The Snap query endpoint can take multiple IDs, so here we can query 1 or more snaps with ease.
        to_query = []
        for snap_id in snaps:
            rgx_match = re.search(
                self.SNAP_PATTERN,
                snap_id,
            )
            if not rgx_match:
                print(f"{snap_id} is not a valid Snap URL or ID.")
                continue
            to_query.append(rgx_match.group(1))
        try:
            retl = []
            for snap in requests.post(
                "https://ms.sc-jpl.com/web/getStoryElements",
                json={"snapIds": to_query},
            ).json()["elements"]:
                s = self._parse_snap(snap)
                if s:
                    retl.append(s)
            return retl
        except requests.exceptions.JSONDecodeError:
            return []

    def query_coords(self, coords: Coordinates):
        to_download: dict[str, Snap] = {}
        current_iteration = self.radius
        epoch = self._get_epoch()
        while current_iteration != 1:
            print(f"Querying with radius {current_iteration}...")
            while True:
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
                            break
                        except requests.exceptions.JSONDecodeError:
                            print("You have been rate limited. Sleeping for 1 minute.")
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

        print(f"Found {len(list(to_download.keys()))} Snaps")
        return self._transform_index(to_download)

    def main(self):
        # Query provided coordinates
        if self.coords_list:
            for coords in self.coords_list:
                self.download_snaps(self.query_coords(coords))

        # Download Snaps from input file
        if self.input_file:
            if os.path.isfile(self.input_file):
                with open(self.input_file, "r") as f:
                    to_format = [ln for ln in f.read().split("\n") if ln.strip()]
                self.download_snaps(self.query_snaps(to_format))
            else:
                raise FileNotFoundError("Input file does not exist.")

        # Download Snaps provided from the command line
        self.download_snaps(self.query_snaps(self.arg_snaps))

        if self.write_json:
            with open(
                os.path.join(
                    self.output_dir, f"archive_{int(datetime.now().timestamp())}.json"
                ),
                "w",
            ) as f:
                f.write(
                    json.dumps(
                        self._transform_index(self.all_snaps),
                        indent=2,
                        cls=SnapJSONEncoder,
                    )
                )

    def _transform_index(self, index: dict[str, Snap]):
        return [v for v in index.values()]

    def _parse_snap(
        self,
        snap: dict[
            str, Any
        ],  # I don't like the Any type but this dict is so dynamic there isn't much point hinting it accurately.
    ) -> Snap | None:
        data_dict = {
            "create_time": round(int(snap["timestamp"]) * 10**-3, 3),
            "snap_id": snap["id"],
        }
        if snap["snapInfo"].get("snapMediaType"):
            data_dict["file_type"] = "mp4"
        elif snap["snapInfo"].get("streamingMediaInfo"):
            data_dict["file_type"] = "jpg"
        else:
            print(
                f'**Unknown Snap type detected!**\n\tID: {snap["id"]}\n\tSnap data: {json.dumps(snap)}\nPlease report this at {self.ISSUES_URL}\n'
            )
            return None
        url = snap["snapInfo"]["streamingMediaInfo"].get("mediaUrl")
        if not url:
            return None
        data_dict["url"] = url
        s = Snap(**data_dict)
        if not self.all_snaps.get(snap["id"]):
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
                f"The API epoch could not be obtained.\n\nPlease report this at {self.ISSUES_URL}"
            )

    class MissingEpochError(Exception):
        pass
