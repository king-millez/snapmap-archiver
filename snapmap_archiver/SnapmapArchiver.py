import os
from snapmap_archiver.Coordinates import Coordinates


class SnapmapArchiver:
    def __init__(self) -> None:
        self.radius = 10_000
        self.max_radius = 85_000

    def main(self, **kwargs):
        if kwargs['ffmpeg_path']:
            if not os.path.isfile(kwargs['ffmpeg_path']):
                raise FileNotFoundError('Please provide a valid file for --ffmpeg-path')
            self.ffmpeg_path = kwargs['ffmpeg_path']

        if not kwargs['output_dir']:
            raise ValueError('Output directory (-o) is required.')

        if not os.path.isdir(kwargs['output_dir']):
            os.makedirs(kwargs['output_dir'], exist_ok=True)  # Python's exception handling has us covered here

        self.output_dir = kwargs['output_dir']

        if not kwargs['location']:
            raise ValueError('location (-l) is required.')

        self.coords = Coordinates(kwargs['location'])

        if kwargs['radius'] > self.max_radius:
            print('Supplied radius value is too large (above 85,000). Defaulting to 85000.')
            self.radius = self.max_radius

    # def api_query(coords: Coordinates, zl=5, max_radius=10000):
    #     available_snaps = []
    #     current_iteration = max_radius
    #     _epoch = get_epoch()
    #     try:
    #         print('Querying Snaps...')
    #         while current_iteration != 1:
    #             payload = {"requestGeoPoint":{"lat":lat,"lon":lon},"zoomLevel":zl,"tileSetId":{"flavor":"default","epoch":_epoch,"type":1},"radiusMeters":current_iteration,"maximumFuzzRadius":0}
    #             req_headers['Content-Length'] = str(len(str(payload)))
    #             api_data = json.loads(requests.post('https://ms.sc-jpl.com/web/getPlaylist', headers=req_headers, json=payload).text)
    #             available_snaps = available_snaps + api_data['manifest']['elements']
    #             if(current_iteration > 2000):
    #                 current_iteration = current_iteration - 2000
    #             elif(current_iteration > 1000):
    #                 current_iteration = current_iteration - 100
    #             else:
    #                 current_iteration = 1
    #         return [i for n, i in enumerate(available_snaps) if i not in available_snaps[n + 1:]]
    #     except:
    #         sys.exit("You seem to have been rate limited, please wait and try again.")