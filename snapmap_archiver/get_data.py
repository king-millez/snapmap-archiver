import requests, random, json, pathlib

req_headers = {
    'User-Agent': random.choice(json.loads(open(f'{pathlib.Path(__file__).parent.absolute()}/utils/user-agents.json', 'r').read())),
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
    for entry in json.loads(requests.post('https://ms.sc-jpl.com/web/getLatestTileSet', headers=req_headers, json={}).text)['tileSetInfos']:
        if(entry['id']['type'] == 'HEAT'):
            return(entry['id']['epoch'])

def api_query(lat, lon, zl=5):
    payload = {"requestGeoPoint":{"lat":lat,"lon":lon},"zoomLevel":zl,"tileSetId":{"flavor":"default","epoch":get_epoch(),"type":1},"radiusMeters":35071.770277487456,"maximumFuzzRadius":0}
    req_headers['Content-Length'] = str(len(str(payload)))
    api_data = requests.post('https://ms.sc-jpl.com/web/getPlaylist', headers=req_headers, json=payload).text
    return(api_data)