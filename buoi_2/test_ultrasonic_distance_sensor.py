import time
from grove.grove_ultrasonic_ranger import GroveUltrasonicRanger

sensor = GroveUltrasonicRanger(5) # D5

while True: 
    distance = sensor.get_distance()
    print('{} cm', format(distance))

    if distance < 20: 
        print('1')
    else: 
        print('0')

    time.sleep(1)
