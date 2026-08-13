import time 
from grove.display.jhd1802 import JHD1802

lcd = JHD1802()

lcd.setCursor(0, 0)
lcd.write('hello world')

print('applicantion exiting...')
