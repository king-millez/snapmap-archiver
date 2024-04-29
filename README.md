# snapmap-archiver

Download all Snap Map content from a specific location.

![snapmap-archiver splash](/.github/img/Splash.png)

[View on PyPI](https://pypi.org/project/snapmap-archiver/)

## Installation (for general usage)

Install with `pip` or `pipx` or whatever trendy Python package manager you use:

```sh
pip install snapmap-archiver
```

## Local Development Setup

Install Poetry with `pip` or `pipx`:

```sh
pip install poetry
```

Install the project dependencies:

```sh
poetry install
```

Run the app with Poetry:

```sh
poetry run python3 main.py [...args]
```

## Usage

```sh
snapmap-archiver -o [OUTPUT DIR] -l="[LATITUDE],[LONGITUDE]"
```

Unfortunately you have to use the arbitrary `-l="lat,lon"` rather than just `-l "lat,lon"` when parsing negative numbers as `argsparse` interprets said numbers as extra arguments.

### Optional Arguments

#### Location

`-l` is not required if an input file or Snap URL is provided. It can also be used multiple times to download Snaps from multiple locations in one command.

E.g

```sh
snapmap-archiver -o ~/Desktop/snap -l='123.123,123.123' -l '445.445,445.445'
```

#### Input File

With `-f` or `--file`, you can specify a file containing a list of line-separated Snap URLs or IDs.

E.g

```sh
snapmap-archiver -o ~/Desktop/snaps -f ~/Desktop/snaps.txt
```

Inside `snaps.txt`:

```
https://map.snapchat.com/ttp/snap/Example/@-33.643495,115.741281,11.86z
Example
https://map.snapchat.com/ttp/snap/Example/
https://map.snapchat.com/ttp/snap/Example/
```

#### Snap URL

You can also just pass 1 or more normal Snap URLs or IDs to the package to download it individually like this:

```sh
snapmap-archiver -o ~/Desktop/snap 'https://map.snapchat.com/ttp/snap/Example/@-33.643495,115.741281,11.86z' 'Example'
```

#### Time Filter

Use the `-t` flag with a Unix timestamp or day, hour, or minute interval to skip the download of any snaps older than that point.

Example with a Unix timestamp:

```sh
snapmap-archiver -t 1714392291 -l '-123,123'
```

Examples with a dynamic time filter:

```sh
snapmap-archiver -t 3d -l '-123,123'  # Removes anything older than 3 days
snapmap-archiver -t 5h -l '-123,123'  # Removes anything older than 5 hours
snapmap-archiver -t 30m -l '-123,123'  # Removes anything older than 30 minutes
```

#### Export JSON

You can export a JSON file with info about downloaded snaps with the `--write-json` argument, which will contain information like the time the Snap was posted, and the Snap location.

It will write `archive.json` to the specified output directory.

#### Snap Radius

The radius from the coordinates you provide that will be included for downloads. `-r 20000` will download all Snaps within a 20km radius of your coordinates.

#### Zoom Depth

You can input a custom zoom depth value (`-z`) that correlates to a zoom level in the GUI. ArcGIS has documentation about this [here](https://developers.arcgis.com/documentation/glossary/zoom-level/), but essentially the lower the number, the further zoomed-out you are. `5` is the default and shouldn't cause any issues.
