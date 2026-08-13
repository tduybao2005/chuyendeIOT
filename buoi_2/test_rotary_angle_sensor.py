from time import sleep 
from grove.adc import ADC 

sensor = ADC(0x08)

while True:
    value = sensor.read_voltage(2) # Ket qua dien ap (mV) (0-3299)
    #value = sensor.read_raw(2)    # Ket qua ADC 12bit (0-4095)
    #value = sensor.read(2)        # Ket qua ti le dien ap do chia 0.1% (0-999)
    print(value)
    sleep(2)
