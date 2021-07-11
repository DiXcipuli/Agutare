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
menu_btn_next = 4               #
menu_btn_previous = 17           # Buttons to browse the menu
menu_btn_validate =27           #
menu_btn_return = 22            #

btn_servo_1 = 13            #
btn_servo_2 = 19            #
btn_servo_3 = 26            # Buttons to trigger the servos
btn_servo_4 = 16            #
btn_servo_5 = 20            #
btn_servo_6 = 21            #
btn_servo_list = [btn_servo_1, btn_servo_2, btn_servo_3, btn_servo_4, btn_servo_5, btn_servo_6]

buzzer_pin = 12             # I am using the PMW of the Raspberry, on the GPIO12, PMW channel 0
# -----------------------------------------------------------------------------------------------------
 



# BUZZER-METRONOME ------------------------------------------------------------------------------------
buzzer_freq = 440
buzzer_duration = 0.07      # In second, how long does the buzzer last for the metronome
# -----------------------------------------------------------------------------------------------------




# GPIO SETUP ------------------------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)

GPIO.setup(menu_btn_next, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(menu_btn_previous, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(menu_btn_validate, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(menu_btn_return, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
current_tab = None                  # Stores the current tab we are working on (pyguitarpro.Song object)
current_tab_name = None             # Stores the current tab name we are working on (string)

default_tempo = 120
new_tab_tempo = default_tempo
current_tempo = default_tempo
saved_tempo = default_tempo
tempo_interval = 5                  # When changing the tempo value, will go 5 by 5 instead of 1 by 1
default_tab_name = "tab_"           # It wont be able to set the desired tab name when creating one. 
extension_type = ".gp5"             # Could be also .gp3 .gp4 or .tg (for TuxGuitar)
 
events = []                         # Will store all the timer, one per note.

is_metronome_on = False 
is_string_test_running = False
is_tab_running = False
run_tab_at_startup = True
is_free_mode_on = False

# Instanciate LCD object
lcd_display = I2C_LCD_driver.lcd()    
#--------------------------------------------------------------------------------------------------------




# MENU ---------------------------------------------------------------------------------------------------
# ALL MESSAGES FROM THE MENU /////////////////////////////////////////////////////////////////
welcome_msg = 'Guitar Ready!'
main_menu = ['Play Tab', 'Practice', 'Test Strings', 'Set Motors Pos']
practice_menu = ['Free Mode', 'Record Mode']
string_test_list = ['String 1','String 2','String 3', 'String 4','String 5','String 6',]
motor_pos_menu = ['Set Motors LOW', 'Set Motors MID', 'Set Motors HIGH']
record_menu = ['New Tab', 'Existing Tab']
new_tab_menu = "New Tab Tempo"
free_mode_menu = "Free Mode Tempo"
record_session = "Record Session"
track_armed = "Track armed!"
track_not_armed = "Track not armed"
tempo_on = "Tempo on"
tempo_off = "Tempo off"

# Those two list will be filed with the files contained in the respective fiolders
custom_tab_list = []
tab_list = []

for file_name in os.listdir(tab_path):          # Populating the list with all the files in the 'tab_path' folder
    tab_list.append(str(file_name))
for file_name in os.listdir(custom_tab_path):   # Populating the list with all the files in the 'custom_tab_path' folder
    custom_tab_list.append(str(file_name))

# CREATING THE TREE ///////////////////////////////////////////////////////////////////////////////////
current_node = None
top_menu_node = Node("top_menu_node")                       # Creating the top node
custom_tab_list_node = None
record_mode_node = None

for index, option_1 in enumerate(main_menu):                #Filling the whole tree
    node_1 = Node(option_1, parent = top_menu_node)    
    if index == 0:      # Play Tab
        for option_2 in tab_list:
            node_2 = Node(option_2, parent = node_1)
    elif index == 1:    # Practice
        for i, option_2 in enumerate(practice_menu):
            node_2 = Node(option_2, parent = node_1)
            # if i == 0:      # Free Mode
            #     node_3 = Node(free_mode_menu, parent = node_2)
            if i == 1:    # Record
                record_mode_node = node_2
                for idx, option_3 in enumerate(record_menu):
                    node_3 = Node(option_3, parent = node_2)
                    if idx == 0: # New Tab
                        node_4 = Node(new_tab_menu, parent = node_3)
                        node_5 = Node(record_session, parent = node_4)
                    elif idx == 1: # Existing Tab
                        custom_tab_list_node = node_3 # Points to node_3
                        for file in custom_tab_list:
                            node_4 = Node(file, parent = node_3)
                            node_5 = Node(record_session, parent = node_4)
    elif index == 2:
        for option_2 in string_test_list:
            node_2 = Node(option_2, parent = node_1)
    elif index == 3:
        for option_2 in motor_pos_menu:
            node_2 = Node(option_2, parent = node_1)
current_node = top_menu_node.children[0]

# Un/comment those two lines to print the menu tree
for pre, fill, node in RenderTree(top_menu_node):
    print("%s%s" % (pre, node.name))

# END OF TREE /////////////////////////////////////////////////////////////////////////////////////////////

# Define where we are in the tree
cursor = -1
previous_cursor = 0

menu_sleeping_time = 0.5 # The time needed to display some useful information
# ---------------------------------------------------------------------------------------------------------




# SERVOS --------------------------------------------------------------------------------------------------
pwm_16_channel_module = Adafruit_PCA9685.PCA9685()

servo_mid_position = [275,285,295,295,295,285]
low_offset_from_mid = [40, 40, 40, 40, 40, 40]
high_offset_from_mid = [40, 40, 40, 40, 40, 40]

# Array to keep track of the state of servos, HIGH or LOW
servo_low_position=[True, True, True, True, True, True]
servo_routine_sleep = 0.5 # Sleep time in the back and forth servo routine


#Set pwm frequency
pwm_16_channel_module.set_pwm_freq(50)

# -----------------------------------------------------------------------------------------------------






#define functions which will be triggered on pin state changes
def menu_btn_callback(channel):
    global cursor

    if GPIO.input(channel) == 0:

        if channel == menu_btn_next:
            cursor += 1
        else:
            cursor -= 1

        checkMenuTree()
        updateMenuDisplay()

def validate(channel):
    global current_menu_index, cursor, is_string_test_running, run_tab_at_startup, current_node
    global is_free_mode_on, previous_cursor

    if GPIO.input(menu_btn_validate) == 0:
        print ("Validate")
        if not current_node.children: # If the current node has no children, it means some actions need to be executed ...
            if current_node.parent.name == main_menu[0]: # = PlayTab
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Playing :", 1)
                lcd_display.lcd_display_string(tab_list[cursor], 2)
                
                playTab()
            
            elif current_node.name == practice_menu[0]: # = Free mode
                is_free_mode_on = True
                startMetronome()
                updateMenuDisplay()

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

            elif current_node == custom_tab_list_node: # Browsing for existing custom tab, but no file found under 'custom_tab_path'
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("No Tab Found !", 1)
                time.sleep(menu_sleeping_time)
                updateMenuDisplay()

            elif current_node.name == new_tab_menu:
                createTab(new_tab_tempo)
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Tab Created !", 1)
                time.sleep(menu_sleeping_time)
                updateMenuTree() # Need to rescan the existing tab under 'custom_tab_folder'
                updateMenuDisplay()

            
        else:                         # ... otherwise we keep going deeper in the tree
            current_node = current_node.children[0]
            if current_node.name == new_tab_menu:
                startMetronome()
            previous_cursor = cursor #We store where we were in this menu, for later when we will press return
            cursor = 0
            updateMenuDisplay()
    


def back(channel):
    print('back')
    global cursor, events, is_tab_running, is_string_test_running, current_node, new_tab_tempo
    global is_metronome_on, is_free_mode_on, saved_tempo
    
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
    elif current_node.name == practice_menu[0] and is_metronome_on:
        is_free_mode_on = False
        is_metronome_on = False
        saved_tempo = current_tempo
        cursor = 0
        updateMenuDisplay()

    elif current_node.name == record_session:
        current_node = record_mode_node
        cursor = 0
    
    else:
        if not current_node.parent == top_menu_node: # Prevents from going out of the top node.
            if current_node.name == new_tab_menu:
                is_metronome_on = False
            current_node = current_node.parent # We go back to the parent in the menu tree
            #TO DO get the right index
            cursor = previous_cursor

        else: # If we are already at the top level menu, then it just gets back to the first option in the top menu
            current_node = top_menu_node.children[0]
            cursor = 0
            
        updateMenuDisplay()



def checkMenuTree(): #used to loop in the menu
    global cursor, current_node, new_tab_tempo, current_tempo

    if current_node.name == new_tab_menu: # In that case we are changing the tempo with the rotary encoder (in new tab menu)
        new_tab_tempo = default_tempo + (cursor * tempo_interval)
        current_tempo = new_tab_tempo
        updateMenuDisplay()

    elif current_node.name == practice_menu[0] and is_free_mode_on:
        current_tempo = saved_tempo + (cursor * tempo_interval)
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

    if current_node.name == new_tab_menu :
        lcd_display.lcd_display_string("Tempo: " + str(new_tab_tempo),2)

    elif is_free_mode_on :
        lcd_display.lcd_display_string("Tempo: " + str(current_tempo),2)

    elif current_node.name == record_session:
        lcd_display.lcd_display_string(current_node.name,1)

    else:
        # Tell us where we are in the current menu with an index
        lcd_display.lcd_display_string(str(cursor + 1) + " / " + str(len(current_node.parent.children)), 2)

    print(current_node.name)



def string_test_loop():
    while is_string_test_running == True:
        trigger_servo(cursor)
        time.sleep(servo_routine_sleep)




# GPIO CALLBACK ----------------------------------------------------------------------------------------------------
GPIO.add_event_detect(menu_btn_next, GPIO.FALLING, callback=menu_btn_callback, bouncetime=300) #SEEMS TO DETECT RISING EDGE ALSO !
GPIO.add_event_detect(menu_btn_previous, GPIO.FALLING, callback=menu_btn_callback, bouncetime=300) #SEEMS TO DETECT RISING EDGE ALSO !
GPIO.add_event_detect(menu_btn_validate, GPIO.FALLING , callback=validate, bouncetime=300)
GPIO.add_event_detect(menu_btn_return, GPIO.FALLING , callback=back, bouncetime=300)

GPIO.add_event_detect(btn_servo_1, GPIO.FALLING, callback=lambda x: trigger_servo(0), bouncetime=150)
GPIO.add_event_detect(btn_servo_2, GPIO.FALLING, callback=lambda x: trigger_servo(1), bouncetime=150)
GPIO.add_event_detect(btn_servo_3, GPIO.FALLING, callback=lambda x: trigger_servo(2), bouncetime=150)
GPIO.add_event_detect(btn_servo_4, GPIO.FALLING, callback=lambda x: trigger_servo(3), bouncetime=150)
GPIO.add_event_detect(btn_servo_5, GPIO.FALLING, callback=lambda x: trigger_servo(4), bouncetime=150)
GPIO.add_event_detect(btn_servo_6, GPIO.FALLING, callback=lambda x: trigger_servo(5), bouncetime=150)
# ------------------------------------------------------------------------------------------------------------------

def updateMenuTree():
    global custom_tab_list
    custom_tab_list = []

    for file_name in os.listdir(custom_tab_path):
        custom_tab_list.append(str(file_name))
        Node(str(file_name), parent = custom_tab_list_node)

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
    global is_metronome_on

    is_metronome_on = True
    metronomeThread()

def metronomeThread():
    if is_metronome_on:
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
            song = pygp.parse(tab_path + tab_list[cursor])
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


    if ( not is_tab_running and GPIO.input(btn_servo_list[index]) == 0) or \
        is_string_test_running or (is_tab_running and GPIO.input(btn_servo_list[index]) == 1): # p

        print("String",str(index+1))
        
        if servo_low_position[index]:
            pwm_16_channel_module.set_pwm(index, 0, servo_mid_position[index] + high_offset_from_mid[index])
            servo_low_position[index] = False
        else:
            pwm_16_channel_module.set_pwm(index, 0, servo_mid_position[index] - low_offset_from_mid[index])
            servo_low_position[index] = True 

def initialize():
    #setServoMidPosition()
    lcd_display.lcd_clear()
    lcd_display.lcd_display_string(welcome_msg)


def main():
    initialize()

    pause()
    

if __name__ == "__main__":
    main()
