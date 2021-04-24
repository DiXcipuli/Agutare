import time                                                                                             
import guitarpro
import Adafruit_PCA9685
from threading import Timer
import threading
import Adafruit_CharLCD as LCD
from RPLCD import CharLCD
import os
from RPi import GPIO

#Rasp4 ulimit -s 8192

path = '/home/pi/Documents/RobotizeGuitar/'
menu = ['Set Motor to Min', 'Set Motor to Mid', 'Set Motor to Max', 'Song List', 'Test']
song_list = ['Nirvana.gp3','test6.gp5', 'Dark_Ré.gp3' ]
test_list = ['String 1','String 2','String 3', 'String 4','String 5','String 6',]
testMode = False
menuMode = 0
tab_running = False
run_tab = False

os.system('clear') #clear screen, this is just for the OCD purmin_poses
 
#tell to GPIO library to use logical PIN names/numbers, instead of the physical PIN numbers
GPIO.setmode(GPIO.BCM)

#LCD SCREEN -----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------
lcd_rs = 20
lcd_en = 26
lcd_d4 = 19
lcd_d5 = 13
lcd_d6 = 6
lcd_d7 = 5

lcd_columns = 16
lcd_rows = 2

#lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)
#lcd = CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows) 
lcd = CharLCD(pin_rs=lcd_rs, pin_rw=None, pin_e=lcd_en, pins_data=[lcd_d4, lcd_d5, lcd_d6, lcd_d7],
              numbering_mode=GPIO.BCM,
              cols=lcd_columns, rows=lcd_rows, dotsize=8,
              auto_linebreaks=True,
              pin_backlight=None, backlight_enabled=True,
              )
#ROTARY ENCODER--------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------
clk = 7
dt = 8
sw = 25
backButton = 18
 
#set up the GPIO events on those pins
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(sw, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(backButton, GPIO.IN, pull_up_down=GPIO.PUD_UP)


cursor = -1
events = []
 
#define functions which will be triggered on pin state changes
def clkClicked(channel):
        global cursor
 
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
 
        if clkState == 0 and dtState == 1:
                cursor = cursor - 1
                if menuMode == 0 :#Main Menu
                    if cursor < 0:
                        cursor = len(menu) -1
                elif menuMode == 1: #Song list menu
                    if cursor < 0:
                        cursor = len(song_list) - 1
                elif menuMode == 2: #Test list
                    if cursor < 0:
                        cursor = len(test_list) - 1

                updateMenuDisplay()
 
def dtClicked(channel):
        global cursor
 
        clkState = GPIO.input(clk)
        dtState = GPIO.input(dt)
         
        if clkState == 1 and dtState == 0:
                cursor = cursor + 1
                if menuMode == 0: #Main Menu
                    if cursor > len(menu) - 1:
                        cursor = 0
                elif menuMode == 1: # Song list menu
                    if cursor > len(song_list) - 1:
                        cursor = 0
                elif menuMode == 2: # Test list
                    if cursor > len(test_list) - 1:
                        cursor = 0

                updateMenuDisplay() 
                 
def updateMenuDisplay():
    lcd.clear()

    if menuMode == 0 :#Main Menu
        #lcd.message(menu[cursor])
        lcd.write_string(menu[cursor])
        print(menu[cursor])
    elif menuMode == 1 :#Song list menu
        #lcd.message(song_list[cursor])
        lcd.write_string(song_list[cursor])
        print(song_list[cursor])
    elif menuMode == 2:
        #lcd.message(test_list[cursor])
        lcd.write_string(test_list[cursor])
        print(test_list[cursor])

def execute(channel):
    global menuMode
    global cursor
    global testMode
    global run_tab
    print ("Validate")
    if menuMode == 0: #Main Menu
        if cursor == 0:
            setToMin()
        if cursor == 1:
            setToNeutral()
        if cursor == 2:
            setToMax()
        if cursor == 3:
            menuMode = 1
            cursor = 0
            updateMenuDisplay()
        if cursor == 4:
            menuMode = 2
            cursor = 0
    elif menuMode == 1:
        run_tab = True

    elif menuMode == 2:
        testMode = True
        testThread = threading.Thread(target=runTest)
        testThread.start()

def runTest():
    while testMode == True:
        string(cursor)
        time.sleep(0.5)

def back(channel):
    print('back')
    global menuMode
    global cursor
    global events
    global tab_running
    global testMode
    tab_running = False
    if menuMode == 1:
        menuMode = 0
        cursor = 0
        updateMenuDisplay()
        for event in events:
            event.cancel()
        events.clear()

    elif menuMode == 2 and testMode:
        testMode = False
        menuMode = 2
        updateMenuDisplay()

    elif menuMode == 2 and not testMode:
        menuMode = 0
        cursor = 0
        updateMenuDisplay()
#8192
#set up the interrupts
GPIO.add_event_detect(clk, GPIO.FALLING, callback=clkClicked, bouncetime=300)
GPIO.add_event_detect(dt, GPIO.FALLING, callback=dtClicked, bouncetime=300)
GPIO.add_event_detect(sw, GPIO.FALLING , callback=execute, bouncetime=300)
GPIO.add_event_detect(backButton, GPIO.FALLING , callback=back, bouncetime=300)

#GPIO.cleanup()

pwm = Adafruit_PCA9685.PCA9685()

# Configure min and max servo pulse lengths
servo_min = 80
servo_neutral = [275,285,295,295,295,285]
servo_max = 510

min_pos=[True, True, True, True, True, True]

pwm.set_pwm_freq(50)
cst = 40
cst_min = [40, 40, 40, 40, 40, 40]
cst_max = [40, 40, 40, 40, 40, 40]
timer = 1



def setToMin():
    for i in range (0, 6):
        min_pos[i] = True

    pwm.set_pwm(0, 0, servo_neutral[0]  - cst_min[0])
    pwm.set_pwm(1, 0, servo_neutral[1]  - cst_min[1])
    pwm.set_pwm(2, 0, servo_neutral[2]  - cst_min[2])
    pwm.set_pwm(3, 0, servo_neutral[3]  - cst_min[3])
    pwm.set_pwm(4, 0, servo_neutral[4]  - cst_min[4])
    pwm.set_pwm(5, 0, servo_neutral[5]  - cst_min[5])

def setToNeutral():
    pwm.set_pwm(0, 0, servo_neutral[0])
    pwm.set_pwm(1, 0, servo_neutral[1])
    pwm.set_pwm(2, 0, servo_neutral[2])
    pwm.set_pwm(3, 0, servo_neutral[3])
    pwm.set_pwm(4, 0, servo_neutral[4])
    pwm.set_pwm(5, 0, servo_neutral[5])

def setToMax():
    for i in range (0, 6):
        min_pos[i] = False

    pwm.set_pwm(0, 0, servo_neutral[0]  + cst_max[0])
    pwm.set_pwm(1, 0, servo_neutral[1]  + cst_max[1])
    pwm.set_pwm(2, 0, servo_neutral[2]  + cst_max[2])
    pwm.set_pwm(3, 0, servo_neutral[3]  + cst_max[3])
    pwm.set_pwm(4, 0, servo_neutral[4]  + cst_max[4])
    pwm.set_pwm(5, 0, servo_neutral[5]  + cst_max[5])

def loadTab():
    global tab_running
    tab_running = True
    setToMin()
    global events
    song = guitarpro.parse(path + song_list[cursor])
    #song = guitarpro.parse('Nirvana.gp3')
    print("Tempo = ", song.tempo)
    print("Number of tracks = ", len(song.tracks))
    print("Number of measures = ", len(song.tracks[0].measures))
    print("Number of voices = ", len(song.tracks[0].measures[0].voices))
    measure_number = 0
    print("Number of beats per bar" , song.measureHeaders[0].timeSignature.numerator)
    beats_per_bar = song.measureHeaders[0].timeSignature.numerator
    for measure in song.tracks[0].measures:
        measure_time = measure_number * 60 * beats_per_bar / song.tempo
        for voice in measure.voices:
            print("Number of beats = ", len(voice.beats))
            beat_time = 0
            for beat in voice.beats:
                note_time = measure_time + beat_time
                beat_time = beat_time + (beat.duration.time/1000)* (60/song.tempo)
                if beat.notes:
                    print("Note time = ", note_time)

                    for note in beat.notes:
                        if note.string == 1:
                            events.append(Timer(note_time, string, [0]))
                        if note.string == 2:
                            events.append(Timer(note_time, string, [1]))
                        if note.string == 3:
                            events.append(Timer(note_time, string, [2]))
                        if note.string == 4:
                            events.append(Timer(note_time, string, [3]))
                        if note.string == 5:
                            events.append(Timer(note_time, string, [4]))
                        if note.string == 6:
                            events.append(Timer(note_time, string, [5]))
                            

        measure_number = measure_number + 1
    for event in events:
        event.start()
    print("---------- Tab is Starting ---------- With ", len(events), " threads" )

def string(index):
    print("String",str(index+1))
    global min_pos

    if min_pos[index]:
        pwm.set_pwm(index, 0, servo_neutral[index] + cst_max[index])
        min_pos[index] = False
    else:
        pwm.set_pwm(index, 0, servo_neutral[index] - cst_min[index])
        min_pos[index] = True 

def initialize():
    lcd.clear()
    lcd.write_string('Guitar Ready!')

def main():
    global tab_running, run_tab
    initialize()
    setToNeutral()
    #loadTab()
    #setToMin()
    #time.sleep(1)
    #setToMax()
    #loadTab()
    #setToNeutral()
    
    while True:
        if run_tab:
            if not tab_running:
                run_tab = False
                tab_running = True
                loadTab()

            run_tab = False

if __name__ == "__main__":
    main()
