# Hybrid_Guitar.py
# Made by Antoine Agu (DiXcipuli@gmail.com)



import time                                                                                             
import guitarpro as pygp
import Adafruit_PCA9685
from threading import Timer
import threading
import I2C_LCD_driver
from RPi import GPIO
import os
from signal import pause
from anytree import Node, RenderTree, search #To implement the menu architecture




# PIN DEFINITION --------------------------------------------------------------------------------------
rotary_pin_A = 7            #
rotary_pin_B = 8            # ROTARY ENCODER
rotary_switch = 25          #

back_button = 18            # Return / Cancel button

btn_servo_1 = 20            #
btn_servo_2 = 21            #
btn_servo_3 = 22            # Buttons to trigger the servos
btn_servo_4 = 23            #
btn_servo_5 = 24            #
btn_servo_6 = 26            #
btn_servo_list = [btn_servo_1, btn_servo_2, btn_servo_3, btn_servo_4, btn_servo_5, btn_servo_6]

buzzer_pin = 12             # I am using the PMW of the Raspberrw, on the GPIO12, PMW channel 0
# -----------------------------------------------------------------------------------------------------




# BUZZER-METRONOME ------------------------------------------------------------------------------------
buzzer_freq = 440
buzzer_duration = 0.07 # In second, how long does the buzzer last for the metronome
# -----------------------------------------------------------------------------------------------------




# GPIO SETUP ------------------------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)

GPIO.setup(rotary_pin_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(rotary_pin_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(rotary_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(back_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(btn_servo_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Buttons to trigger servos
GPIO.setup(btn_servo_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_5, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_6, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #

GPIO.setup(buzzer_pin, GPIO.OUT)                                # Buzzer pin set to PWM
buzzer_pwm = GPIO.PWM(buzzer_pin, buzzer_freq)                  #
# -----------------------------------------------------------------------------------------------------




# TAB, metronome and Display information --------------------------------------------------------------------------------------
tab_path = '/home/pi/Documents/RobotizeGuitar/Tabs/'                # For tabs which wont be edited
custom_tab_path = '/home/pi/Documents/RobotizeGuitar/CustomTabs/'   # For own compositions, where measures and notes will be added
current_tab = None          # Stores the current tab we are working on (pyguitarpro.Song object)
current_tab_name = None     # Stores the current tab name we are working on (string)

default_tempo = 120
new_tab_tempo = default_tempo
current_tempo = default_tempo
default_tab_name = "tab_"
extension_type = ".gp5"     # Could be also .gp3 .gp4 or .tg (for TuxGuitar)
 

events = [] # Will store all the timer, one per note.

metronome_on = False 
is_string_test_running = False
is_tab_running = False
run_tab_at_startup = True

# Instanciate LCD object
lcd_display = I2C_LCD_driver.lcd()      
#--------------------------------------------------------------------------------------------------------




# MENU ---------------------------------------------------------------------------------------------------
welcome_msg = 'Guitar Ready!'

# The menu architecture is handled by a tree
current_node = None
main_menu = ['Play Tab', 'Practice', 'Test Strings', 'Set Motors Pos']
song_list = [] # Will be populate with the tabs in 'tab_path' folder
practice_menu = ['Free Mode', 'Record Mode']
string_test_list = ['String 1','String 2','String 3', 'String 4','String 5','String 6',]
motor_pos_menu = ['Set Motors LOW', 'Set Motors MID', 'Set Motors HIGH']
record_menu = ['New Tab', 'Existing Tab']
new_tab_menu = "Choose tempo"
existing_tab = [] # Will be populate with the tabs in 'custom_tab_path' folder
menu_sleeping_time = 0.5 # The time needed to display some useful information

for file in os.listdir(tab_path):   # Populating the list with all the files in the 'tab_path' folder
    song_list.append(str(file))

# Combining the sub menu
sub_menu_list = [song_list, practice_menu, string_test_list, motor_pos_menu]

# Creqting the first top node of the tree
top_menu_node = Node("top_menu_node")
#Populate tree, with the main menu list
for option in main_menu:
    Node(option, parent = top_menu_node)

current_node = top_menu_node.children[0]

for index, option in enumerate(top_menu_node.children): # For each option in the menu, populate the
    for sub_option in sub_menu_list[index]:             # 
        Node(sub_option, parent = option)               # tree with the sub menu list

record_node = search.findall_by_attr(top_menu_node, "Record Mode")[0]

for i, option in enumerate(record_menu):
    node = Node(option, parent = record_node)
    if i == 0:
        Node(new_tab_menu, parent = node)

existing_tab_node = search.findall_by_attr(top_menu_node, record_menu[1])[0]

for file in os.listdir(custom_tab_path):
    existing_tab.append(str(file))
    Node(str(file), parent = existing_tab_node)

# Uncomment those two lines to print the menu tree
# for pre, fill, node in RenderTree(top_menu_node):
#     print("%s%s" % (pre, node.name))


# Define where we are in the tree
cursor = -1
# ---------------------------------------------------------------------------------------------------------




# SERVOS --------------------------------------------------------------------------------------------------
pwm_16_channel_module = Adafruit_PCA9685.PCA9685()

servo_mid_position = [275,285,295,295,295,285]
low_offset_from_mid = [40, 40, 40, 40, 40, 40]
high_offset_from_mid = [40, 40, 40, 40, 40, 40]

# Array to keep track of the state of servos, HIGH or LOW
servo_low_position=[True, True, True, True, True, True]
servo_routine_sleep = 0.5 # Sleep time in the back and forth servo routine
is_servos_triggering_allowed = False

#Set pwm frequency
pwm_16_channel_module.set_pwm_freq(50)

# -----------------------------------------------------------------------------------------------------






#define functions which will be triggered on pin state changes
def rotary_pin_A_callback(channel):
    global cursor

    if GPIO.input(rotary_pin_A) == 0: #GPIO callback seems not to work properly, so I have to check that rotary_pin_A is low
        # Here we only check the pin B, as we know that A fell to LOW, which triggered the callback
        rotary_pin_B_state = GPIO.input(rotary_pin_B)

        if rotary_pin_B_state == 1:
            cursor = cursor - 1
        elif rotary_pin_B_state == 0:
            cursor = cursor + 1

        checkMenuTree()
        updateMenuDisplay()

def validate(channel):
    global current_menu_index, cursor, is_string_test_running, run_tab_at_startup, current_node, is_servos_triggering_allowed

    if GPIO.input(rotary_switch) == 0:
        print ("Validate")
        if not current_node.children: # If the current node has no children, it means some actions need to be executed ...
            if current_node.parent.name == main_menu[0]: # = PlayTab
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Playing :", 1)
                lcd_display.lcd_display_string(song_list[cursor], 2)
                
                playTab()
            
            elif current_node.name == practice_menu[0]: # = Free mode
                is_servos_triggering_allowed = True
                startMetronome()
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Free Mode On !", 1)
                lcd_display.lcd_display_string("Tempo: " + str(current_tempo), 2)

            elif current_node.parent.name == main_menu[2]: # = Loop test String
                if not is_string_test_running:
                    is_string_test_running = True
                    testThread = threading.Thread(target=string_test_loop)
                    testThread.start()
                    lcd_display.lcd_clear()
                    lcd_display.lcd_display_string("Playing String " + str(cursor + 1), 1)

            elif current_node.parent.name == main_menu[3]: # = Set Motors to Position
                if cursor == 0:
                    setServoLowPosition()
                if cursor == 1:
                    setServoMidPosition()
                if cursor == 2:
                    setServoHighPosition()
                
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Done !", 1)
                time.sleep(menu_sleeping_time)
                updateMenuDisplay()

            elif current_node == existing_tab_node: # Browsing for existing custom tab, but no file found under 'custom_tab_path'
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("No Tab Found !", 1)
                time.sleep(menu_sleeping_time)
                updateMenuDisplay()

            elif current_node.name == new_tab_menu:
                createTab(new_tab_tempo)
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Tab Created !", 1)
                time.sleep(menu_sleeping_time)
                updateMenuDisplay()

            
        else:                         # ... otherwise we keep going deeper in the tree
            current_node = current_node.children[0]
            cursor = 0
            updateMenuDisplay()
    


def back(channel):
    print('back')
    global cursor, events, is_tab_running, is_string_test_running, current_node, is_servos_triggering_allowed, new_tab_tempo
    global metronome_on
    
    new_tab_tempo = default_tempo

    if is_tab_running : # We do not go back to the parent, we just stop the action, and re-display the current node
        is_tab_running = False
        # We cancel the Timer, to stop the triggering of servos
        for event in events:
            event.cancel()   
        events.clear()

        updateMenuDisplay()

    elif is_string_test_running : # We do not go back to the parent, we just stop the action, and re-display the current node
        is_string_test_running = False
        updateMenuDisplay()

    # We do not go back to the parent, we just stop the action, and re-display the current node
    elif current_node.name == practice_menu[0] and is_servos_triggering_allowed:
        is_servos_triggering_allowed = False
        metronome_on = False
        updateMenuDisplay()
    
    else:
        if not current_node.parent == top_menu_node: # Prevents from going out of the top node.
            current_node = current_node.parent # We go back to the parent in the menu tree
            #TO DO get the right index
            cursor = 0

        else: # If we are already at the top level menu, then it just gets back to the first option in the top menu
            current_node = top_menu_node.children[0]
            cursor = 0
            
        updateMenuDisplay()



def checkMenuTree(): #used to loop in the menu
    global cursor, current_node, new_tab_tempo

    if current_node.name == new_tab_menu: # In that case we are changing the tempo with the rotary encoder
        new_tab_tempo = default_tempo + cursor
        updateMenuDisplay()

    else:
        if cursor >= len(current_node.parent.children): # Get back to the parent, to get the total children
            cursor = 0
        elif cursor < 0:
            cursor = len(current_node.parent.children) - 1

        # Set the new current node
        current_node = current_node.parent.children[cursor]

 

def updateMenuDisplay():
    lcd_display.lcd_clear()
    lcd_display.lcd_display_string(current_node.name,1)

    if current_node.name == new_tab_menu:
        lcd_display.lcd_display_string(str(new_tab_tempo),2)
    print(current_node.name)



def string_test_loop():
    while is_string_test_running == True:
        trigger_servo(cursor)
        time.sleep(servo_routine_sleep)




# GPIO CALLBACK ----------------------------------------------------------------------------------------------------
GPIO.add_event_detect(rotary_pin_A, GPIO.FALLING, callback=rotary_pin_A_callback) #SEEMS TO DETECT RISING EDGE ALSO !
GPIO.add_event_detect(rotary_switch, GPIO.RISING , callback=validate, bouncetime=300)
GPIO.add_event_detect(back_button, GPIO.FALLING , callback=back, bouncetime=300)

GPIO.add_event_detect(btn_servo_1, GPIO.FALLING, callback=lambda x: trigger_servo(0), bouncetime=150)
GPIO.add_event_detect(btn_servo_2, GPIO.FALLING, callback=lambda x: trigger_servo(1), bouncetime=150)
GPIO.add_event_detect(btn_servo_3, GPIO.FALLING, callback=lambda x: trigger_servo(2), bouncetime=150)
GPIO.add_event_detect(btn_servo_4, GPIO.FALLING, callback=lambda x: trigger_servo(3), bouncetime=150)
GPIO.add_event_detect(btn_servo_5, GPIO.FALLING, callback=lambda x: trigger_servo(4), bouncetime=150)
GPIO.add_event_detect(btn_servo_6, GPIO.FALLING, callback=lambda x: trigger_servo(5), bouncetime=150)
# ------------------------------------------------------------------------------------------------------------------


def setServoLowPosition():
    for i in range (0, 6):
        servo_low_position[i] = True
        pwm_16_channel_module.set_pwm(i, 0, servo_mid_position[i] - low_offset_from_mid[i])

def setServoMidPosition():
    for i in range (0, 6):
        pwm_16_channel_module.set_pwm(i, 0, servo_mid_position[i])

def setServoHighPosition():
    for i in range (0, 6):
        servo_low_position[i] = False
        pwm_16_channel_module.set_pwm(i, 0, servo_mid_position[i]  + high_offset_from_mid[i])

def createTab(tempo):
    print("called")
    global current_tab
    i = 0
    file_name = custom_tab_path + default_tab_name + str(i) + extension_type
    while os.path.isfile(file_name): #Check if file already exists
        i += 1
        file_name = custom_tab_path + default_tab_name + str(i) + extension_type
        print(i)

    current_tab = pygp.Song()
    track = pygp.Track(current_tab)
    current_tab.tracks.append(track)
    measure = track.measures[0]
    voice = measure.voices[0]

    print(file_name)
    pygp.write(current_tab, file_name)

def saveLoop():
    track = current_tab.track[0]
    header = current_tab.measureHeaders[0]
    measure = pygp.Measure(track, header)
    track.measure.append(measure)

    #Filling the created measure

    saveTab()

def startMetronome():
    global metronome_on

    metronome_on = True
    metronomeThread()

def metronomeThread():
    if metronome_on:
        timer = 60 / current_tempo
        threading.Timer(timer, metronomeThread).start()

        #Trigger the buzzer to a specify pwm frequency
        buzzer_pwm.start(50) # Duty cycle, between 0 and 100
        time.sleep(buzzer_duration)
        buzzer_pwm.stop()

        #Uncomment to check th number of Thread object running
        print(threading.active_count())

def saveTab():
    if not path.isdir(custom_tab_path):
        os.mkdir(custom_tab_path)

    pygp.write(current_tab, custom_tab_path + current_tab_name + extension_type)

def loadTab():
    #TO DO set the current tab name
    #current_tab = pygp.parse
    current_tempo = current_tab.tempo


def playTab(tab_name = None):
    global is_tab_running, events

    #TO DO: is_tab_running false at the end of song

    if not is_tab_running:
        # Flag to prevent re-launching another Tab.
        is_tab_running = True

        # Set all motors to low position
        setServoLowPosition()
        
        #Load tab
        if tab_name == None:
            song = pygp.parse(tab_path + song_list[cursor])
        else:
            song = pygp.parse(tab_name)

        print("Song name = ", song_list[cursor])
        print("Tempo = ", song.tempo)
        print("Number of tracks = ", len(song.tracks))
        print("Number of measures = ", len(song.tracks[0].measures))
        print("Number of voices = ", len(song.tracks[0].measures[0].voices))
        measure_number = 0
        print(type(song.tracks[0].measures[0]))
        print("Number of beats per bar" , song.measureHeaders[0].timeSignature.numerator)
        beats_per_bar = song.measureHeaders[0].timeSignature.numerator
        for measure in song.tracks[0].measures:
            measure_time = measure_number * 60 * beats_per_bar / song.tempo
            for voice in measure.voices:
                print("Number of beats = ", len(voice.beats))
                beat_time = 0
                for beat in voice.beats:
                    note_time = measure_time + beat_time
                    print(note_time)
                    beat_time = beat_time + (beat.duration.time/1000)* (60/song.tempo)
                    if beat.notes:
                        print("Note time = ", note_time)

                        for note in beat.notes:
                            if note.string == 1:
                                events.append(Timer(note_time, trigger_servo, [0]))
                            if note.string == 2:
                                events.append(Timer(note_time, trigger_servo, [1]))
                            if note.string == 3:
                                events.append(Timer(note_time, trigger_servo, [2]))
                            if note.string == 4:
                                events.append(Timer(note_time, trigger_servo, [3]))
                            if note.string == 5:
                                events.append(Timer(note_time, trigger_servo, [4]))
                            if note.string == 6:
                                events.append(Timer(note_time, trigger_servo, [5]))
                                

            measure_number = measure_number + 1
        for event in events:
            event.start()
        print("---------- Tab is Starting ---------- With ", len(events), " threads" )


def trigger_servo(index):
    global servo_low_position

    if is_servos_triggering_allowed and GPIO.input(btn_servo_list[index]) == 0 : 

        print("String",str(index+1))
        
        if servo_low_position[index]:
            pwm_16_channel_module.set_pwm(index, 0, servo_mid_position[index] + high_offset_from_mid[index])
            servo_low_position[index] = False
        else:
            pwm_16_channel_module.set_pwm(index, 0, servo_mid_position[index] - low_offset_from_mid[index])
            servo_low_position[index] = True 

def initialize():
    setServoMidPosition()
    lcd_display.lcd_clear()
    lcd_display.lcd_display_string(welcome_msg)


def main():
    initialize()

    pause()
    

if __name__ == "__main__":
    main()
