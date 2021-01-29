import sys, json, subprocess, os

def organise_media(api_data):
    to_download = []
    print(f'Found {len(api_data)} Snaps.')
    for entry in api_data:
        data_dict = {'id': entry['id'], 'create_time': entry['timestamp'], 'media': {}}
        for locale in entry['snapInfo']['title']['strings']:
            if(locale['locale'] == 'en'):
                data_dict['location'] = locale['text']
        try:
            data_dict['media']['raw_url'] = entry['snapInfo']['streamingMediaInfo']['prefixUrl'] + 'media.mp4'
            try:
                data_dict['media']['video_overlay'] = entry['snapInfo']['streamingMediaInfo']['prefixUrl'] + 'overlay.png'
            except:
                data_dict['media']['video_overlay'] = None
        except:
            data_dict['media']['raw_url'] = entry['snapInfo']['publicMediaInfo']['publicImageMediaInfo']['mediaUrl']
        to_download.append(data_dict)
    return(to_download)

def download_media(output_dir, organised_data, dl_json=False):
    for index,snap in enumerate(organised_data):
        DL_MSG = f'Snap {index + 1}/{len(organised_data)} downloading...'

        filename = snap['location'] + ' - ' + snap['create_time'] + ' - ' + snap['id']
        if(dl_json):
            with open(f'{output_dir}/' + filename + '.info.json', 'w') as json_file:
                json_file.write(json.dumps(snap, indent=2))
        if(sys.platform == 'win32'):
            cmd = ['aria2c.exe', snap['media']['raw_url'], '-d', output_dir, '-o']
        else:
            cmd = ['aria2c', snap['media']['raw_url'], '-d', output_dir, '-o']
        
        if(snap['media']['raw_url'][-3:] == 'mp4'):
            if(os.path.exists(f'{cmd[-2]}/' + filename + '.mp4')):
                print(f'Snap {index + 1}/{len(organised_data)} already downloaded.')
            else:
                print(DL_MSG + f' - {filename}.mp4')
                subprocess.run(cmd + [filename + '.mp4'], capture_output=True)
        else:
            if(os.path.exists(f'{cmd[-2]}/' + filename + '.jpg')):
                print(f'Snap {index + 1}/{len(organised_data)} already downloaded.')
            else:
                print(DL_MSG + f' - {filename}.jpg')
                subprocess.run(cmd + [filename + '.jpg'], capture_output=True)