from servos import servo
import guitarpro as pygp
from threading import Timer
import os
from enum_classes import SessionRecorderState
import time

custom_tab_path = '/home/pi/Documents/RobotizeGuitar/CustomTabs/'
tab_path = '/home/pi/Documents/RobotizeGuitar/Tabs/'                # For tabs which wont be edited
default_tab_name = "tab_"

class TabManager:
    def __init__(self):
        self.extension_lisit = ("agu", "gp3", "gp4", "gp5")
        self.events = []
        self.bar_starting_time = 0
        self.saved_notes_list = [[] for i in range(6)]  #Contains the time where the string was triggered, not the duration yet
        self.pre_record_list = [False, False, False, False, False, False]
        self.sorted_notes_list = []
        self.is_tab_playing = False
        self.callback = None


    def play_tab(self, tab_name, is_agu_file, from_loop = None):
        if not self.is_tab_playing:
            self.is_tab_playing = True

            # Set all motors to low position
            servo.setServoLowPosition()

            if is_agu_file:
                with open(tab_name + '/MetaDefault.agu') as tab_file:
                    lines = tab_file.readlines()

                tempo = int(lines[0].split(',')[1].rstrip('\n'))
                beats_per_loop = int(lines[1].split(',')[1].rstrip('\n'))

                last_timer = 0
                start_from = 1
                if from_loop != None:
                    start_from = from_loop
                for i, line in enumerate(lines[2 + start_from - 1:]):
                    with open(tab_name + '/' + line.rstrip('\n')) as loop_file:
                        loop_notes = loop_file.readlines()
                    for note in loop_notes:
                        note_time = float(note.split(',')[1].rstrip('\n'))
                        note_string = int(note.split(',')[0])
                        self.events.append(Timer((note_time + i )* beats_per_loop * 60 / tempo, servo.trigger_servo, [note_string]))
                        last_timer = (note_time + i )* beats_per_loop * 60 / tempo
                
                self.events.append(Timer(last_timer + 0.2, self.end_tab_callback))

                for event in self.events:
                    event.start()

            else :
                song = pygp.parse(tab_name)
                print("Tempo = ", song.tempo)
                print("Number of tracks = ", len(song.tracks))
                print("Number of measures = ", len(song.tracks[0].measures))
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
                                for note in beat.notes:
                                    self.events.append(Timer(note_time, servo.trigger_servo, [note.string - 1]))

                    measure_number = measure_number + 1
                for event in self.events:
                    event.start()

                print("---------- Tab is Starting ---------- With ", len(self.events), " threads" )

    def end_tab_callback(self):
        self.is_tab_playing = False
        self.clear_events()
        
        if self.callback != None:
            self.callback()

    def set_callback(self, callback):
        self.callback = callback

    def createTab(self, tempo, beats):
        i = 1
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


    def clear_events(self):
        for event in self.events:
            event.cancel()   
        self.events.clear()
        self.is_tab_playing = False

    def save_note(self, index, mode):
        if mode == 0:
            self.pre_record_list[index] = True
        elif mode == 1:
            note_start_time = time.time() - self.bar_starting_time
            self.saved_notes_list[index].append(note_start_time)

    def process_loop(self): # No matter the loop is saved or note, some process is done
        self.sorted_notes_list = []

        # List all notes, sorted by time, in order to print them.
        for i in range(0, 6):
            if self.pre_record_list[i]:
                self.sorted_notes_list.append((i,0))
            for j in range(0, len(self.saved_notes_list[i])):
                self.sorted_notes_list.append((i,self.saved_notes_list[i][j]))

        self.sorted_notes_list = sorted(self.sorted_notes_list, key = lambda tup: tup[1])
        
        self.print_saved_notes()

        # Reset List of notes
        self.pre_record_list = [False, False, False, False, False, False]
        self.saved_notes_list = [[] for i in range(6)]
        self.bar_starting_time = 0

        self.replay_loop()
    
    def replay_loop(self):
        for i in range(0, 5):
            for string, time in self.sorted_notes_list:
                self.events.append(Timer(time + (i * self.beats * 60/self.current_tempo), servo.trigger_servo, [string]))

        for event in self.events:
            event.start()
        
    def print_saved_notes(self):
        #In term of note starting time in seconds
        print("|------------------------------------------------------")
        print("| Loop recorded over " + str(self.beats) + " beats")
        print("|------------------------------------------------------")
        print("|   String id     |      starting time (in s)")
        print("|------------------------------------------------------")
        for i, time in self.sorted_notes_list:
            print("|   String " + str(i + 1) + "      |      " + str(time) + " s")

        print("|------------------------------------------------------")


    def load_tab_info(self, tab_name):
        #The tab name is already stored at this point, we only need to update:
        #   -tempo
        #   -beats
        #   -nb of loops
        self.tab_name = tab_name
        with open(custom_tab_path + self.tab_name + "/MetaDefault.agu") as file:
            lines = file.readlines()
            self.current_tempo = int(lines[0].split(',')[1])
            self.beats = int(lines[1].split(',')[1])
            nb_of_loops = len(lines) - 2

        return nb_of_loops, self.current_tempo

    def saveLoop(self):
        i = 1
        loop_file = custom_tab_path + self.tab_name + '/' + "Loop_" + str(i)
        while os.path.isfile(loop_file):
            i += 1
            loop_file = custom_tab_path + self.tab_name + '/' + "Loop_" + str(i)

        with open(loop_file, 'w') as saved_file:
            for string, time in self.sorted_notes_list:
                saved_file.write(str(string) + "," + str(time / self.beats) + '\n')

        with open('../CustomTabs/' + self.tab_name + "/MetaDefault.agu", 'a') as saved_file:
            saved_file.write("Loop_" + str(i) + '\n')

        self.load_tab_info(self.tab_name)

    def clear_saved_notes(self):
        self.saved_notes_list = [[] for i in range(6)]  
        self.pre_record_list = [False, False, False, False, False, False]
        self.sorted_notes_list = []

tab_manager = TabManager()