class Coordinates:
    def __init__(self, coord_str: str):
        try:
            lat, long = coord_str.split(",", 1)
            self.lat = float(lat)
            self.long = float(long)
        except Exception:
            raise ValueError(
                f'Provided coordinates [{coord_str}] could not be split to lat/long points. Use comma seperated values for latitude/longitude, e.g: -l="35.0,67.0".'
            )

    def __str__(self) -> str:
        return f"Lat: {self.lat}, Lon: {self.long}"

    def __repr__(self) -> str:
        return f"({self.lat},{self.long})"
