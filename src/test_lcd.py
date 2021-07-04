import I2C_LCD_driver
from RPi import GPIO

GPIO.setmode(GPIO.BCM)

lcd = I2C_LCD_driver.lcd()
#RASPBERRY PINS
clk = 7
dt = 8

clkState = 1
previousClkState = 1

#set up the GPIO events on those pins
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                 
def updateMenuDisplay(text):
    lcd.lcd_clear()
    lcd.lcd_display_string(text)

def main():
    while True:
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
         
        if clkState == 0 and previousClkState == 1:
            if dtState == 0:
                updateMenuDisplay("Text test + 1")
            else:
                updateMenuDisplay("Text test - 1")               

        previousClkState = clkState

if __name__ == "__main__":
    main()
