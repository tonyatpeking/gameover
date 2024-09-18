from platformdirs import user_config_dir
from pathlib import Path

APP_NAME = 'gameover'
GAMEOVER_DIR = Path(user_config_dir(APP_NAME))
