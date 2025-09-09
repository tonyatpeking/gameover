from pynput.mouse import Button, Controller
from pynput.keyboard import Key, Controller as KeyboardController, HotKey, GlobalHotKeys

from time import sleep

mouse = Controller()

# get mouse position
position = mouse.position
print('the mouse is at', position)

# set mouse position
#mouse.position = (100, 100)
# relative movement
#sleep(0.7)
#mouse.move(100, 100)

keyboard = KeyboardController()



#keyboard.type('Hello World')


from pynput import keyboard

def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def on_release(key):
    print('{0} released'.format(
        key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False



def on_activate():
    print('Global hotkey activated!')


def on_hotkey_release():
    print('Global hotkey released!')

def for_canonical(f):
    return lambda k: f(l.canonical(k))

listener = None

def win32_event_filter(msg, data):
    print(f'msg: {msg}')
    print(f'data: 0x{data.vkCode:X}')
    global listener
    if data.vkCode == 0x48:
        # Suppress x
        print('suppressing event')
        #listener._suppress = True
        listener.suppress_event()

        
        return True
    else:
        #listener._suppress = False
        return True

hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('h'),
    on_activate)





listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
        win32_event_filter=win32_event_filter,
        suppress=False
        )



with listener as l:
    l.join()

