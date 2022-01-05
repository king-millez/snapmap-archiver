import sys
import json
import subprocess
import os
import re


def match_snap_id(url: str) -> str:
    return re.search(
        r'(W7_(?:[aA-zZ0-9\-_\+]{22})(?:[aA-zZ0-9-_\+]{28})AAAAAA)',
        url).group(1)


def organise_media(api_data):
    to_download = []
    print(f'Found {len(api_data)} Snaps.')
    for entry in api_data:
        data_dict = {
            'id': entry['id'],
            'create_time': entry['timestamp'],
            'media': {}
        }
        try:
            for locale in entry['snapInfo']['title']['strings']:
                if locale['locale'] == 'en':
                    data_dict['location'] = locale['text']
        except KeyError:
            data_dict['location'] = \
                entry['snapInfo']['localitySubtitle']['fallback']
        try:
            data_dict['media']['overlayText'] = \
                entry['snapInfo']['overlayText']
        except KeyError:
            data_dict['media']['overlayText'] = None
        try:
            data_dict['media']['raw_url'] = \
                entry['snapInfo']['streamingMediaInfo']['prefixUrl'] + 'media.mp4'
            data_dict['media']['filetype'] = "mp4"
            try:
                data_dict['media']['video_overlay'] = \
                    entry['snapInfo']['streamingMediaInfo']['prefixUrl'] + \
                    entry['snapInfo']['streamingMediaInfo']['overlayUrl']
            except KeyError:
                data_dict['media']['video_overlay'] = None
        except KeyError:
            try:
                data_dict['media']['raw_url'] = \
                    entry['snapInfo']['publicMediaInfo']\
                         ['publicImage''MediaInfo']['mediaUrl']
                data_dict['media']['filetype'] = "jpg"
            except KeyError:
                for i in entry['snapInfo'].items():
                    if i[0] == 'streamingThumbnailInfo':  # For some reason JSON throws an error if you just query this key directly, so you have to do it this way.
                        data_dict['media']['raw_url'] = \
                            i[1]['infos'][-1]['thumbnailUrl']
                if len(data_dict['media']) == 0:
                    continue  # If there's no video file and no video/image thumbnail, just skip the snap since there's nothing to download
        to_download.append(data_dict)
    return(to_download)


def download_media(
        output_dir, organised_data, dl_json=False, no_overlay=False):
    for index, snap in enumerate(organised_data):
        DL_MSG = f'Snap {index + 1}/{len(organised_data)} downloading...'

        filename = snap['location'] + ' - ' + \
            snap['create_time'] + ' - ' + snap['id']
        if dl_json:
            with open(f'{output_dir}/' + filename +
                      '.info.json', 'w') as json_file:
                json_file.write(json.dumps(snap, indent=2))
        if sys.platform == 'win32':
            cmd = [
                'aria2c.exe',
                snap['media']['raw_url'],
                '-d',
                output_dir,
                '-o'
            ]
        else:
            cmd = ['aria2c', snap['media']['raw_url'], '-d', output_dir, '-o']
        if snap['media']['raw_url'][-3:] == 'mp4':
            if os.path.exists(f'{cmd[-2]}/' + filename + '.mp4'):
                print(f'Snap {index + 1}/{len(organised_data)} '
                      'already downloaded.')
            else:
                print(DL_MSG + f' - {filename}.mp4')
                # Download snap without overlay
                if no_overlay:
                    subprocess.run(
                        cmd + [filename + '.mp4'], capture_output=True)
                else:
                    if snap['media']['video_overlay'] is not None:
                        merge_overlay = [
                            'ffmpeg',
                            "-y",
                            "-i",
                            snap['media']['raw_url'],
                            "-i",
                            snap['media']['video_overlay'],
                            "-filter_complex",
                            "[1][0]scale2ref[i][m];[m][i]overlay[v]",
                            "-map",
                            "[v]",
                            "-map",
                            "0:a?",
                            "-ac",
                            "2"
                        ]
                        # Merge video and overlay to one file using ffmpeg
                        subprocess.run(
                            merge_overlay + [f"{cmd[-2]}/{filename}.mp4"],
                            capture_output=True)
                        # Delete temp file
                    else:
                        subprocess.run(
                            cmd + [filename + '.mp4'], capture_output=True)

        else:
            if os.path.exists(f'{cmd[-2]}/' + filename + '.jpg'):
                print(f'Snap {index + 1}/{len(organised_data)} '
                      'already downloaded.')
            else:
                print(DL_MSG + f' - {filename}.jpg')
                subprocess.run(
                    cmd + [filename + '.jpg'], capture_output=True)
