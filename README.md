# snapmap-archiver

A tool written in Python to download all Snapmaps content from a specific location.

![snapmap-archiver splash](/.github/img/Splash.png)

## Setup

`pip3 install snapmap-archiver`

[View on PyPI](https://pypi.org/project/snapmap-archiver/)

Install dependencies with `pip3`.

```sh
pip3 install -r requirements.txt
```

### Install [aria2c](http://aria2.github.io/)

Download `aria2c` from here:

[https://aria2.github.io/](https://aria2.github.io/)

This is the downloader used for the fastest Snap download speeds.

## Usage

```sh
python3 -m snapmap_archiver -o [OUTPUT DIR] -l="[LATITUDE],[LONGITUDE]"
```
Unfortunately you have to use the arbitrary `-l="lat,lon"` rather than just `-l "lat,lon"` when parsing negative numbers as `argsparse` interprets said numbers as extra arguments.

### Optional Arguments

#### Location

`-l` is not required if an input file or Snap URL is provided. It can also be used multiple times to download Snaps from multiple locations in one command.

E.g

```sh
python3 -m snapmap_archiver -o ~/Desktop/snap -l='123.123,123.123' -l '445.445,445.445'
```

#### Input File

With `-t`, you can specify a file containing a list of line-separated Snap URLs or IDs.

E.g

```sh
python3 -m snapmap_archiver -o ~/Desktop/snap -t ~/snaps.txt
```

Inside `snaps.txt`:

```
https://map.snapchat.com/ttp/snap/Example/@-33.643495,115.741281,11.86z
Example
https://map.snapchat.com/ttp/snap/Example/
https://map.snapchat.com/ttp/snap/Example/
```

#### Snap URL

You can also just pass 1 or more normal Snap URLs to the package to download it individually like this:

```sh
python3 -m snapmap_archiver -o ~/Desktop/snap 'https://map.snapchat.com/ttp/snap/Example/@-33.643495,115.741281,11.86z'
```

#### Export JSON

You can export a JSON file with info about downloaded snaps with the `--write-json` argument, which will contain information like the time the Snap was posted, and the Snap location.

#### Snap Radius

The radius from the coordinates you provide that will be included for downloads. `-r 20000` will download all Snaps within a 20km radius of your coordinates.

#### No Overlay

By default the script merges the video and the overlay file into one file. With the `--no-overlay` argument you can disable this and only download the raw video.  
