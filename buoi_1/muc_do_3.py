from gpiozero import LED, Button
from time import  sleep
from signal import pause

# module 1
led_1 = LED(16)
button_1 = Button(17)

# module 2
led_2 = LED(24)
button_2 = Button(25)

# module 3 
led_3 = LED(22)
button_3 = Button(23)

# yeu cau
step = 0.5
ton_max = 10
ton_min = 0.5
toff_max = 10
toff_min = 0.5

# ton/toff module 1 ban dau
ton_module_1 = 3
toff_module_1 = 4

# ton/toff module 2 ban dau
ton_module_2 = 1 
toff_module_2 = 6

def increase_ton():
    global ton_module_1, toff_module_1 
    ton_module_1 = min(ton_max, ton_module_1 + step)
    toff_module_1 = max(toff_min, toff_module_1 - step)
    print(f"[module 1] ton = {ton_module_1}, toff = {toff_module_1}")
    led_1.blink(on_time = ton_module_1, off_time = toff_module_1)

def decrease_ton():
    global ton_module_2, toff_module_2 
    ton_module_2 = max(ton_min, ton_module_2 - step)
    toff_module_2 = min(toff_max, toff_module_2 + step)
    print(f"[module 2] ton = {ton_module_2}, toff = {toff_module_2}")
    led_2.blink(on_time = ton_module_2, off_time = toff_module_2)

def pressed_button_3():
    led_3.blink(on_time = ton_module_1, off_time = toff_module_1)

def released_button_3():
    led_3.blink(on_time = ton_module_2, off_time = toff_module_2)

button_1.when_pressed = increase_ton
button_2.when_pressed = decrease_ton

button_3.when_pressed = pressed_button_3
button_3.when_released = released_button_3

led_1.blink(on_time = ton_module_1, off_time = toff_module_1)
led_2.blink(on_time = ton_module_2, off_time = toff_module_2)
led_3.blink(on_time = ton_module_2, off_time = toff_module_2)

pause()
