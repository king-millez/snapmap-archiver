import os
import re
import sys
import argparse
from . import get_data
from .utils import organise_media, download_media, match_snap_id


def main():
    USAGE_MSG = 'snapmap_archiver -o [OUTPUT DIR] -l="[LATITUDE],[LONGITUDE]" [SNAP URL (optional)]'
    geo_msg = (
        "Use comma seperated values for " 'latitude/longitude, e.g: -l="35.0,67.0"'
    )
    parser = argparse.ArgumentParser(
        description="Download content from Snapmaps", usage=USAGE_MSG
    )
    parser.add_argument(
        "-o",
        dest="output_dir",
        type=str,
        help="Output directory for downloaded content.",
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
        "-z", dest="zoom_depth", type=float, help="Snapmaps zoom depth, default is 5."
    )
    parser.add_argument(
        "-r",
        dest="radius",
        type=int,
        help="Maximum Snap radius in meters, default is 30000.",
    )
    parser.add_argument(
        "--file",
        dest="input_file",
        type=str,
        help="File containing line-separated Snap URLs or IDs",
    )
    parser.add_argument(
        "--write-json",
        dest="write_json",
        action="store_true",
        default=False,
        help="Write Snap metadata JSON.",
    )
    parser.add_argument(
        "--no-overlay",
        dest="no_overlay",
        action="store_true",
        default=False,
        help="Do not use ffmpeg to merge graphical "
        "elements to video Snaps. Default is False",
    )
    args, unknown = parser.parse_known_args()

    snap_ids = []
    if unknown:
        snap_ids = [
            match_snap_id(i)
            for i in unknown
            if re.match(
                r"https?:\/\/map\.snapchat\.com\/ttp\/snap\/W7_(?:[aA-zZ0-9\-_\+]{22})(?:[aA-zZ0-9-_\+]{28})AAAAAA\/?(?:@-?[0-9]{1,3}\.?[0-9]{0,},-?[0-9]{1,3}\.?[0-9]{0,}(?:,[0-9]{1,3}\.?[0-9]{0,}z))?",
                i,
            )
        ]

    if args.input_file:
        if os.path.isfile(args.input_file):
            with open(args.input_file, "r") as f:
                to_format = f.read().split("\n")
                for candidate in to_format:
                    if len(candidate) > 0:
                        try:
                            snap_ids.append(match_snap_id(candidate))
                        except Exception:
                            print(f"{candidate} is not a valid Snap URL or ID.")
        else:
            sys.exit("Input file does not exist.")

    if not args.output_dir:
        print("Output directory (-o) is required.")
        sys.exit(USAGE_MSG)

    if not args.location and not snap_ids and not args.input_file:
        print("No form of input was supplied.")
        sys.exit(USAGE_MSG)

    if args.location:
        for coords in args.location:
            if "," not in coords[0]:
                sys.exit(f"{geo_msg}\n{coords} is not valid.")

    if not os.path.isdir(args.output_dir):
        try:
            os.mkdir(args.output_dir)
        except PermissionError:
            sys.exit(f'Could not create directory "{args.output_dir}"')

    if not args.radius:
        args.radius = 30000
    elif args.radius > 85000:
        print(
            "Supplied radius value is too large " "(above 85,000). Defaulting to 85000."
        )
        args.radius = 85000

    if args.location:
        for coords in args.location:
            try:
                geo_data = coords[0].split(",", 1)
            except Exception:
                sys.exit(geo_msg)
            api_response = get_data.api_query(
                float(geo_data[0]), float(geo_data[1]), max_radius=args.radius
            )
            download_media(
                args.output_dir,
                organise_media(api_response),
                args.write_json,
                args.no_overlay,
            )

    if snap_ids:
        download_media(
            args.output_dir,
            organise_media(
                get_data.api_query(snap_ids=snap_ids, mode="snap")["elements"]
            ),
            args.write_json,
            args.no_overlay,
        )
