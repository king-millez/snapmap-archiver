# snapmap-archiver

A tool written in Python to download all Snapmaps content from a specific geolocation.

![snapmap-archiver splash](/.github/img/Splash.png)

## Setup

Install dependencies with `pip3`.

```sh
pip3 install -r requirements.txt
```

Install [aria2c](http://aria2.github.io/)

## Usage

```sh
python3 -m snapmap_archiver -o [OUTPUT DIR] -g="[LATITUDE],[LONGITUDE]"
```

Unfortunately you have to use the arbitrary `-g="lat,lon"` rather than just `-g "lat,lon"` when parsing negative numbers as `argsparse` interprets said numbers as extra arguments.

### Optional Arguments

#### Export JSON

You can export a JSON file with info about downloaded snaps with the `--write-json` argument, which will contain information like the time the Snap was posted, and the Snap location.