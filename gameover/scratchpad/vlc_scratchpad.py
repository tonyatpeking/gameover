import vlc
from pathlib import Path
from time import sleep
player = vlc.MediaPlayer(r'')
player.play()
player.get_instance() # returns the corresponding instance
sleep(10)