from typing import Dict, List
import requests
import random
import json
import pathlib
import sys


req_headers = {
    'User-Agent': random.choice(
        json.loads(open(f'{pathlib.Path(__file__).parent.absolute()}/utils/use'
                        'r-agents.json', 'r').read())),
    'Host': 'ms.sc-jpl.com',
    'Accept': '*/*',
    'Accept-Language': 'en-US',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://map.snapchat.com/@0,0,7.67z',
    'Content-Type': 'application/json',
    'Origin': 'https://map.snapchat.com',
    'Content-Length': '2',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Sec-GPC': '1',
    'TE': 'Trailers',
}


def get_epoch():
    for entry in json.loads(requests.post(
        'https://ms.sc-jpl.com/web/getLatestTileSet',
            headers=req_headers, json={}).text)['tileSetInfos']:
        if(entry['id']['type'] == 'HEAT'):
            return(entry['id']['epoch'])


def api_query(lat: float = 0, lon: float = 0.0, zl: int = 5, max_radius: int = 10000, mode: str = 'loc', snap_ids: list = []) -> Dict[str, List]:
    if mode == 'loc':
        available_snaps = []
        current_iteration = max_radius
        _epoch = get_epoch()
        try:
            print('Querying Snaps...')
            while current_iteration != 1:
                print(f'Querying with radius {current_iteration}...')
                payload = {
                    "requestGeoPoint": {
                        "lat": lat,
                        "lon": lon
                    },
                    "zoomLevel": zl,
                    "tileSetId": {
                        "flavor": "default",
                        "epoch": _epoch,
                        "type": 1
                    },
                    "radiusMeters": current_iteration,
                    "maximumFuzzRadius": 0
                }
                req_headers['Content-Length'] = str(len(str(payload)))
                api_data = requests.post('https://ms.sc-jpl.com/web/'
                                         'getPlaylist', headers=req_headers,
                                         json=payload).json()
                available_snaps = available_snaps + \
                    api_data['manifest']['elements']
                if(current_iteration > 2000):
                    current_iteration = current_iteration - 2000
                elif(current_iteration > 1000):
                    current_iteration = current_iteration - 100
                else:
                    current_iteration = 1
            print('Sorting list of Snaps...')
            return [i for n, i in enumerate(available_snaps)
                    if i not in available_snaps[n + 1:]]
        except Exception:
            sys.exit("You seem to have been rate limited, "
                     "please wait and try again.")

    if mode == 'snap':
        return requests.post(
            'https://ms.sc-jpl.com/web/getStoryElements',
            json={
                "snapIds": snap_ids
            }
        ).json()
