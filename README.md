# snapmap-archiver

A tool written in Python to download all Snapmaps content from a specific geolocation.

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