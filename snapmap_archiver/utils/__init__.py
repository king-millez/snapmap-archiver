import json

def organise_media(api_data):
    for entry in json.loads(api_data)['manifest']['elements']:
        try:
            print(entry['snapInfo']['streamingMediaInfo']['prefixUrl'] + 'media.mp4')
        except:
            print(entry['snapInfo']['publicMediaInfo']['publicImageMediaInfo']['mediaUrl'])