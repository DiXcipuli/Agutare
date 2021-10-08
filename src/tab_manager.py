from types import prepare_class
import guitarpro as pygp
from threading import Timer
import os
from enum_classes import SessionRecorderState
import time



class TabManager:

    def __init__(self, servo_manager, tab_path, custom_tab_path):
        self.servo_manager = servo_manager
        self.tab_path = tab_path
        self.custom_tab_path = custom_tab_path

        self.extension_lisit = ("agu", "gp3", "gp4", "gp5")
        self.gp_extensions = ("gp3", "gp4", "gp5")
        self.agu_extension = "agu"
        self.default_tab_dir_name = "tab_"
        self.save_file = "Meta.agu"

        self.events = []                    # When playing a tab, each note will create a Threading Timer object, stored in this variable
        self.loop_repeat_number = 2
        self.bar_starting_time = 0
        self.saved_notes_list = [[] for i in range(6)] 
        # Sometimes when pressing the button on the first beat, we may press it few milli seconds before the beginning of the loop.
        # This 'pre_record' variable is made to handle this. If it is true, then we will create a note on the very first beat.
        self.pre_record_list = [False, False, False, False, False, False]
        self.sorted_notes_list = []
        self.is_tab_playing = False
        self.callback = None


    @property
    def tab_path(self):
        return self._tab_path


    @tab_path.setter
    def tab_path(self, path):
        self._tab_path = path


    @property
    def custom_tab_path(self):
        return self._custom_tab_path


    @custom_tab_path.setter
    def custom_tab_path(self, path):
        self._custom_tab_path = path


    def createTab(self, tempo, beats):

        i = 1
        dir_name = self.custom_tab_path + self.default_tab_dir_name + str(i)

        while os.path.isdir(dir_name): #Check if dir already exists
            i += 1
            dir_name = self.custom_tab_path + self.default_tab_dir_name + str(i)
        
        os.mkdir(dir_name)

        text = ["Tempo, " + str(tempo) + '\n', "Beats, " + str(beats) + '\n']
        with open(dir_name + '/' + self.save_file , 'w') as file:
            file.writelines(text)


        return self.default_tab_dir_name + str(i)



    def check_tab_format(self, check_mode): #mode 1: Allow both (gp3, gp4, gp5) and .agu format. mode 2: Allows only .agu format (for recording)
        consistent_tabs = []

        if check_mode == 1:
            for file_name in sorted(os.listdir(self.tab_path)):   # Check all files in tab_path, both files and dirs
                if os.path.isfile(self.tab_path + str(file_name)):              # If it is a file, check that the extension is in (gp3,4,5)
                    if str(file_name)[-3:] in self.gp_extensions:
                        consistent_tabs.append(file_name)
                elif os.path.isdir(self.tab_path + str(file_name)):             # If its a dir, check that it contains a Meta.agu file
                    for sub_file_name in sorted(os.listdir(self.tab_path + str(file_name))):
                        if str(sub_file_name)[-3:] in self.agu_extension:
                            consistent_tabs.append(file_name)
                            break

        elif check_mode == 2:
            for file_name in sorted(os.listdir(self.custom_tab_path)):   # Check all files in tab_path, both files and dirs
                if os.path.isdir(self.custom_tab_path + str(file_name)):             # If its a dir, check that it contains a Meta.agu file
                    for sub_file_name in sorted(os.listdir(self.tab_path + str(file_name))):
                        if str(sub_file_name)[-3:] in self.agu_extension:
                            consistent_tabs.append(file_name)
                            break


        return consistent_tabs


    # For gpX, the name of the tab corresponds directly to the name of the save file, but for .agu format,
    # the name of the tab that the user sees on the screen correspond to a folder, in which a .agu file is.
    # So this function returns the real tab save file, from either a gpX or .agu tab
    # Return 0 if gpX format, 1 otherwise

    def grab_tab_file_from_name(self, absolute_tab_name):
        if os.path.isfile(absolute_tab_name):
            return (absolute_tab_name, 0)
        elif os.path.isdir(absolute_tab_name):
            return (os.path.join(absolute_tab_name, self.save_file), 1)


    def play_tab(self, tab_path, is_agu_file, from_loop = None, to_loop = None):

        if not self.is_tab_playing:
            self.is_tab_playing = True

            # Set all servos to low position
            self.servo_manager.setServoLowPosition()

            if is_agu_file:
                with open(tab_path + '/' + self.save_file) as tab_file:
                    lines = tab_file.readlines()

                tempo = int(lines[0].split(',')[1].rstrip('\n'))
                beats_per_loop = int(lines[1].split(',')[1].rstrip('\n'))

                last_timer = 0
                start_from = 1
                end_to = len(lines) - 1
                pre_event_array = []
                nb_of_loops = len(lines) - 2
                if from_loop != None:
                    start_from = from_loop
                if to_loop != None:
                    end_to = to_loop
                for i, line in enumerate(lines[2 + start_from - 1 : 2 + end_to - 1]):
                    with open(tab_path + '/' + line.rstrip('\n')) as loop_file:
                        loop_notes = loop_file.readlines()
                    for note in loop_notes:
                        note_time = float(note.split(',')[1].rstrip('\n'))
                        note_string = int(note.split(',')[0])
                        pre_event_array.append(((note_time + i )* beats_per_loop * 60 / tempo, note_string))
                        

                for i in range (self.loop_repeat_number):
                    for time, string in pre_event_array:
                        self.events.append(Timer(time + i * self.beats * 60/self.current_tempo * nb_of_loops, self.servo_manager.trigger_servo, [string]))
                last_timer = (self.loop_repeat_number - 1) * self.beats * 60/self.current_tempo * nb_of_loops + pre_event_array[-1][0]
                
                self.events.append(Timer(last_timer + 0.2, self.end_tab_callback))

                for event in self.events:
                    event.start()

            else :
                last_timer = 0
                song = pygp.parse(tab_path)
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
                            #print(beat.duration.time)
                            beat_time = beat_time + (beat.duration.time/960)* (60/song.tempo)
                            if beat.notes:
                                last_timer = note_time
                                for note in beat.notes:
                                    self.events.append(Timer(note_time, self.servo_manager.trigger_servo, [note.string - 1]))


                    measure_number = measure_number + 1

                self.events.append(Timer(last_timer + 0.2, self.end_tab_callback))
                for event in self.events:
                    event.start()

                print("---------- Tab is Starting ---------- With ", len(self.events), " threads" )


    def end_tab_callback(self): # Sends a signal when the tab is over
        self.is_tab_playing = False
        self.clear_events()
        
        if self.callback != None:
            self.callback()


    def set_callback(self, callback):
        self.callback = callback


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
        for i in range(0, self.loop_repeat_number):
            for string, time in self.sorted_notes_list:
                self.events.append(Timer(time + (i * self.beats * 60/self.current_tempo), self.servo_manager.trigger_servo, [string]))

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


    def saveLoop(self):
        i = 1
        loop_file = self.custom_tab_path + self.tab_name + '/' + "Loop_" + str(i)
        while os.path.isfile(loop_file):
            i += 1
            loop_file = self.custom_tab_path + self.tab_name + '/' + "Loop_" + str(i)

        with open(loop_file, 'w') as saved_file:
            for string, time in self.sorted_notes_list:
                saved_file.write(str(string) + "," + str(time / (self.beats * 60 / self.current_tempo)) + '\n')

        with open('../CustomTabs/' + self.tab_name + "/" + self.save_file, 'a') as saved_file:
            saved_file.write("Loop_" + str(i) + '\n')

        self.load_tab_info(self.tab_name)


    def load_tab_info(self, tab_name):
        self.tab_name = tab_name
        with open(self.custom_tab_path + self.tab_name + "/" + self.save_file) as file:
            lines = file.readlines()
            self.current_tempo = int(lines[0].split(',')[1])
            self.beats = int(lines[1].split(',')[1])
            nb_of_loops = len(lines) - 2

        return nb_of_loops, self.current_tempo


    def clear_events(self):
        for event in self.events:
            event.cancel()   
        self.events.clear()
        self.is_tab_playing = False


    def clear_saved_notes(self):
        self.saved_notes_list = [[] for i in range(6)]  
        self.pre_record_list = [False, False, False, False, False, False]
        self.sorted_notes_list = []
