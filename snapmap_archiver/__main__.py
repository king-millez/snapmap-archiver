import argparse
import sys

from loguru import logger
from loguru._logger import Logger

from snapmap_archiver import (
    DEFAULT_RADIUS,
    DEFAULT_WRITE_JSON,
    DEFAULT_ZOOM_DEPTH,
    ISSUES_URL,
    SNAP_PATTERN,
    default_output_dir,
)
from snapmap_archiver.coordinates import Coordinates
from snapmap_archiver.SnapmapArchiver import SnapmapArchiver

parser = argparse.ArgumentParser(
    description="Download content from Snapmaps",
    usage='snapmap_archiver -o [OUTPUT DIR] -l="[LATITUDE],[LONGITUDE]"\n\nUse -h to display more options.',
)

parser.add_argument(
    "-o",
    dest="output_dir",
    type=str,
    help="Output directory for downloaded content.",
    default=default_output_dir,
)
parser.add_argument(
    "-z",
    dest="zoom_depth",
    type=float,
    help="Snapmaps zoom depth, default is 5.",
    default=DEFAULT_ZOOM_DEPTH,
)
parser.add_argument(
    "-r",
    dest="radius",
    type=int,
    help="Maximum Snap radius in meters, default is 30,000.",
    default=DEFAULT_RADIUS,
)
parser.add_argument(
    "--write-json",
    dest="write_json",
    action="store_true",
    default=DEFAULT_WRITE_JSON,
    help="Write Snap metadata JSON.",
)
parser.add_argument(
    "-l",
    "--location",
    dest="location",
    type=str,
    help="Latitude/longitude of desired area. Can be used multiple times",
    action="append",
    nargs="*",
)
parser.add_argument(
    "-f",
    "--file",
    dest="input_file",
    type=str,
    help="File containing line-separated Snap URLs or IDs",
)
parser.add_argument(
    "-t",
    "--since-time",
    dest="since_time",
    type=str,
    help="Remove any Snaps older than the passed time. Either a 10 digit UTC Unix timestamp or [n = number of][m = minutes | h = hours | d = days] (e.g., 1d, 15h, 30m).",
    default=None,
)
parser.add_argument(
    "-d",
    "--debug",
    dest="debug_mode",
    help="Enable debug logging.",
    action="store_true",
)


def valid_unique_snap_ids(raw_ids: list[str], logger: Logger):
    unique_snap_ids = set(raw_ids)

    valid_snap_ids = set(
        [
            SNAP_PATTERN.search(snap_id).group(1)  # type: ignore
            for snap_id in unique_snap_ids
            if SNAP_PATTERN.search(snap_id)
        ]
    )

    invalid_snap_ids = valid_snap_ids ^ unique_snap_ids
    if invalid_snap_ids:
        logger.warning(
            f"The following [{len(invalid_snap_ids)}] invalid snap IDs were provided:"
        )
        for invalid_id in invalid_snap_ids:
            logger.warning(f" - [{invalid_id}].")
        logger.warning(
            f"If you think this was a mistake, open an issue at [{ISSUES_URL}].\n"
        )

    return valid_snap_ids


def main():
    args, snap_ids = parser.parse_known_args()

    logger.remove(0)
    logger.add(
        sys.stdout, level="DEBUG" if args.debug_mode else "INFO", serialize=False
    )

    if args.input_file:
        with open(args.input_file, "r") as f:
            snap_ids.extend(f.readlines())

    valid_snap_ids: set[str] = valid_unique_snap_ids(snap_ids, logger)  # type: ignore

    coordinates = [
        Coordinates(location) for location, in (args.location if args.location else [])
    ]

    if not valid_snap_ids and not coordinates:
        logger.error(
            "Some kind of input is required. Run [snapmap-archiver -h] for help."
        )
        sys.exit(1)

    sm_archiver = SnapmapArchiver(
        logger=logger,  # type: ignore
        output_dir=args.output_dir,
        write_json=args.write_json,
        since_time=args.since_time,
    )

    for coordinate_set in coordinates:
        sm_archiver.query_coords(
            coords=coordinate_set,
            zoom_depth=args.zoom_depth,
            requested_radius=args.radius,
        )

    sm_archiver.query_snaps(valid_snap_ids)
    sm_archiver.download_cached_snaps()


if __name__ == "__main__":
    main()
