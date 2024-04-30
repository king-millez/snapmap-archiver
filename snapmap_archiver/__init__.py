import os
import re
from datetime import datetime

DEFAULT_WRITE_JSON = False
DEFAULT_ZOOM_DEPTH = 5
DEFAULT_RADIUS = 10_000
SNAP_PATTERN = re.compile(
    r"(?:https?:\/\/map\.snapchat\.com\/ttp\/snap\/)?(W7_(?:[a-zA-Z0-9\-_\+]{56})(?:\/?@-?[0-9]{1,3}\.?[0-9]{0,},-?[0-9]{1,3}\.?[0-9]{0,}(?:,[0-9]{1,3}\.?[0-9]{0,}z))?)"
)
DEFAULT_API_HOST = "https://ms.sc-jpl.com"
ISSUES_URL = "https://github.com/king-millez/snapmap-archiver/issues/new/choose"


default_output_dir = os.path.join(
    os.getcwd(), f"snaps-{int(datetime.now().timestamp())}"
)
