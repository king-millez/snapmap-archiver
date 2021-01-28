import json

def organise_media(api_data):
    to_download = []
    for entry in json.loads(api_data)['manifest']['elements']:
        data_dict = {'folder': entry['id'], 'create_time': entry['timestamp'], 'media': {}}
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