from pynput import keyboard
import pyautogui

# Скорость перемещения мыши
speed = 10

def on_press(key):
    try:
        if key.char.lower() == 'w':
            pyautogui.moveRel(0, -speed)
        elif key.char.lower() == 's':
            pyautogui.moveRel(0, speed)
        elif key.char.lower() == 'a':
            pyautogui.moveRel(-speed, 0)
        elif key.char.lower() == 'd':
            pyautogui.moveRel(speed, 0)
        elif key.char.lower() == 'q':
            pyautogui.click()
        elif key.char.lower() == 'e':
            pyautogui.click(button='right')
    except AttributeError:
        pass

def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False

# Collect events until released
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
