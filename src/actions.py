import guitarpro as pygp
import Adafruit_PCA9685
from threading import Timer
import os

# Array to keep track of the state of servos, HIGH or LOW
servo_low_position=[True, True, True, True, True, True]
pwm_16_channel_module = Adafruit_PCA9685.PCA9685()

servo_mid_position = [275,285,295,295,295,285]
low_offset_from_mid = [40, 40, 40, 40, 40, 40]
high_offset_from_mid = [40, 40, 40, 40, 40, 40]
servo_routine_sleep = 0.5 # Sleep time in the back and forth servo routine
events = []                         # Will store all the timer, one per note.
            # For tabs which wont be edited
custom_tab_path = '/home/pi/Documents/RobotizeGuitar/CustomTabs/'   # For own compositions, where measures and notes will be added               # When changing the tempo value, will go 5 by 5 instead of 1 by 1
default_tab_name = "tab_"           # It wont be able to set the desired tab name when creating one. 
extension_type = ".gp5"   


#Set pwm frequency
pwm_16_channel_module.set_pwm_freq(50)

def playTab(tab_name):
    global is_tab_running, events

    #TO DO: is_tab_running false a

    # Set all motors to low position
    setServoLowPosition()
    
    #Load tab
    song = pygp.parse(tab_name)
    print("Tempo = ", song.tempo)
    print("Number of tracks = ", len(song.tracks))
    print("Number of measures = ", len(song.tracks[0].measures))
    print("Number of voices = ", len(song.tracks[0].measures[0].voices))
    measure_number = 0
    beats_per_bar = song.measureHeaders[0].timeSignature.numerator
    for measure in song.tracks[0].measures:
        measure_time = measure_number * 60 * beats_per_bar / song.tempo
        for voice in measure.voices:
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

    print("String",str(index+1))
    
    if servo_low_position[index]:
        pwm_16_channel_module.set_pwm(index, 0, servo_mid_position[index] + high_offset_from_mid[index])
        servo_low_position[index] = False
    else:
        pwm_16_channel_module.set_pwm(index, 0, servo_mid_position[index] - low_offset_from_mid[index])
        servo_low_position[index] = True 

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


def saveTab():
    if not path.isdir(custom_tab_path):
        os.mkdir(custom_tab_path)

    pygp.write(current_tab, custom_tab_path + current_tab_name + extension_type)

def loadTab():
    #TO DO set the current tab name
    #current_tab = pygp.parse
    current_tempo = current_tab.tempo

def clear_events():
    global events
    for event in events:
        event.cancel()   
    events.clear()