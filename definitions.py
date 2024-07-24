import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(ROOT_DIR, 'tests')
RESOURCES_DIR = os.path.join(EXAMPLES_DIR, 'resources')
RAW_JSON = os.path.join(RESOURCES_DIR, 'raw.json')
ZDF_JSON = os.path.join(RESOURCES_DIR, 'zdf.json')
DOWNLOAD_JSON = os.path.join(RESOURCES_DIR, 'download.json')