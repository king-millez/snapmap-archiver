import sys, json, subprocess
from requests import get

def organise_media(api_data):
    to_download = []
    for entry in json.loads(api_data)['manifest']['elements']:
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
    for snap in organised_data:
        if(dl_json):
            with open(f'{output_dir}/{snap["id"]}.info.json', 'w') as json_file:
                json_file.write(json.dumps(snap, indent=2))
        if(sys.platform == 'win32'):
            cmd = ['aria2c.exe', snap['media']['raw_url'], '-d', output_dir, '-o']
        else:
            cmd = ['aria2c', snap['media']['raw_url'], '-d', output_dir, '-o']

        if(snap['media']['raw_url'][-3:] == 'mp4'):
            subprocess.run(cmd + [snap['id'] + '.mp4'])
        else:
            subprocess.run(cmd + [snap['id'] + '.jpg'])