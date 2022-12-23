from dataclasses import dataclass


@dataclass
class Snap:
    snap_id: str
    url: str
    create_time: int
    file_type: str
