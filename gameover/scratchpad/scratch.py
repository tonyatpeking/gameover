from pynput import keyboard
 
def keyboard_listener():
    global listener
    def on_press(key):
        print('on press', key)

    def on_release(key):
        print('on release', key)
        if key == keyboard.Key.esc:
            return False # This will quit the listener
 
    def win32_event_filter(msg, data):
        if (msg == 257 or msg == 256) and data.vkCode == 0x48: # Key Down/Up & h
            print("Suppressing h up")
            listener._suppress = True
            return False
            # return False # if you return False, your on_press/on_release will not be called
        else:
             listener._suppress = False
        return True
            
    return keyboard.Listener(
        on_press=on_press,
        on_release=on_release,
        win32_event_filter=win32_event_filter,
        suppress=False
    )

listener = keyboard_listener()

if __name__ == '__main__':
    with listener as ml:
        ml.join()