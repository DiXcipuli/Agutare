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
extension_type = ".agu"   


#Set pwm frequency
pwm_16_channel_module.set_pwm_freq(50)

def playTab(tab_name):
    global is_tab_running, events

    #TO DO: is_tab_running false a

    # Set all motors to low position
    setServoLowPosition()

    with open(tab_name + "/MetaDefault.agu") as tab_file:
        lines = tab_file.readlines()

    tempo = int(lines[0].split(',')[1].rstrip('\n'))
    beats_per_loop = int(lines[1].split(',')[1].rstrip('\n'))
    for i, line in enumerate(lines[2:]):
        with open(tab_name + '/' + line.rstrip('\n')) as loop_file:
            loop_notes = loop_file.readlines()
        for note in loop_notes:
            note_time = float(note.split(',')[1].rstrip('\n'))
            note_string = int(note.split(',')[0])
            events.append(Timer((note_time + i )* beats_per_loop * 60 / tempo, trigger_servo, [note_string]))
    for event in events:
        event.start()

    # #Load tab
    # song = pygp.parse(tab_name)
    # print("Tempo = ", song.tempo)
    # print("Number of tracks = ", len(song.tracks))
    # print("Number of measures = ", len(song.tracks[0].measures))
    # measure_number = 0
    # beats_per_bar = song.measureHeaders[0].timeSignature.numerator
    # for measure in song.tracks[0].measures:
    #     measure_time = measure_number * 60 * beats_per_bar / song.tempo
    #     for voice in measure.voices:
    #         beat_time = 0
    #         for beat in voice.beats:
    #             note_time = measure_time + beat_time
    #             print(note_time)
    #             beat_time = beat_time + (beat.duration.time/1000)* (60/song.tempo)
    #             if beat.notes:
    #                 for note in beat.notes:
    #                     events.append(Timer(note_time, trigger_servo, [note.string - 1]))

    #     measure_number = measure_number + 1
    # for event in events:
    #     event.start()
    # print("---------- Tab is Starting ---------- With ", len(events), " threads" )


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

def createTab(tempo, beats):
    global current_tab
    i = 0
    dir_name = custom_tab_path + default_tab_name + str(i)
    while os.path.isdir(dir_name): #Check if dir already exists
        i += 1
        dir_name = custom_tab_path + default_tab_name + str(i)
    
    os.mkdir(dir_name)

    with open(dir_name + '/' + "Meta.agu" , 'w') as file:
        file.writelines(["Tempo, " + str(tempo) + '\n', "Beats, " + str(beats) + '\n'])

    with open(dir_name + '/' + "MetaDefault.agu" , 'w') as file:
        file.writelines(["Tempo, " + str(tempo) + '\n', "Beats, " + str(beats) + '\n'])


    return default_tab_name + str(i)


# def clear_events():
#     global events
#     for event in events:
#         event.cancel()   
#     events.clear()