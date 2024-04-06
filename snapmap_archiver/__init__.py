import argparse

from snapmap_archiver.SnapmapArchiver import SnapmapArchiver


def main():
    parser = argparse.ArgumentParser(
        description="Download content from Snapmaps",
        usage='snapmap_archiver -o [OUTPUT DIR] -l="[LATITUDE],[LONGITUDE]"\n\nUse -h to display more options.',
    )
    parser.add_argument(
        "-o",
        dest="output_dir",
        type=str,
        help="Output directory for downloaded content.",
    )
    parser.add_argument(
        "-z",
        dest="zoom_depth",
        type=float,
        help="Snapmaps zoom depth, default is 5.",
        default=5,
    )
    parser.add_argument(
        "-r",
        dest="radius",
        type=int,
        help="Maximum Snap radius in meters, default is 30,000.",
        default=30_000,
    )
    parser.add_argument(
        "--write-json",
        dest="write_json",
        action="store_true",
        default=False,
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
    args, unknown = parser.parse_known_args()

    sm_archiver = SnapmapArchiver(
        *unknown,
        radius=args.radius,
        output_dir=args.output_dir,
        locations=[location for location, in args.location],
        zoom_depth=args.zoom_depth,
        write_json=args.write_json,
        input_file=args.input_file,
    )
    sm_archiver.main()
