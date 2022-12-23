class Coordinates:
    def __init__(self, coord_str: str):
        self.geo_msg = '\n\nUse comma seperated values for latitude/longitude, e.g: -l="35.0,67.0"'
        if ',' not in coord_str:
            raise ValueError(f'No comma is present in the provided coordinates.{self.geo_msg}')
        try:
            self.lat, self.long = coord_str.split(',', 1)
        except Exception:
            raise ValueError(f'Provided coordinates could not be split to lat/long points.{self.geo_msg}')
