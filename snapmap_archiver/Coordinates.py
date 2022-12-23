class Coordinates:
    def __init__(self, coord_str: str):
        self.geo_msg = '\n\nUse comma seperated values for latitude/longitude, e.g: -l="35.0,67.0"'
        if ',' not in coord_str:
            raise ValueError(f'No comma is present in the provided coordinates.{self.geo_msg}')
        try:
            lat, long = coord_str.split(',', 1)
            self.lat = float(lat)
            self.long = float(long)
        except Exception:
            raise ValueError(f'Provided coordinates could not be split to lat/long points.{self.geo_msg}')

    def __str__(self) -> str:
        return f'Lat: {self.lat}, Lon: {self.long}'

    def __repr__(self) -> str:
        return f'({self.lat},{self.long})'
