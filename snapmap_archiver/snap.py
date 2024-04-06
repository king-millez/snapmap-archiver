import json
from dataclasses import dataclass, asdict


@dataclass
class Snap:
    snap_id: str
    url: str
    create_time: int
    file_type: str
    location: str


class SnapJSONEncoder(json.JSONEncoder):
    def default(self, o: Snap):
        return asdict(o)
