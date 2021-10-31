import guitarpro as pygp
from threading import Timer
import os
from enum_classes import SessionRecorderState
import time



class TabManager:

    def __init__(self, servo_manager, tabs_path):
        self.servo_manager = servo_manager
        self.tabs_path = tabs_path

        self.extensions_list = ("agu", "gp3", "gp4", "gp5")
        self.gp_extensions = ("gp3", "gp4", "gp5")
        self.agu_extension = "agu"
        self.default_tab_dir_name = "tab_"
        self.default_loop_name = "Loop_"
        self.meta_tab_file = "Meta.agu"
        self.header_tempo = "Tempo,"
        self.header_beats = "Beats,"

        self.events = []                    # When playing a tab, each note will create a Threading Timer object, stored in this variable
        self.repeat_loop_X_time = 4
        self.repeat_newly_saved_loop_X_time = 4
        self.end_of_tab_event_offset = 0.2
        self.bar_starting_time = 0
        self.saved_notes_list = [[] for i in range(6)]

        # Sometimes when pressing the button on the first beat, we may press it few milli seconds before the beginning of the loop.
        # This 'pre_record' variable is made to handle this. If it is true, then we will create a note on the very first beat.
        self.pre_record_list = [False, False, False, False, False, False]
        self.sorted_notes_list = []
        self.is_tab_playing = False
        self.callback = None
        self.gp_to_agu_mapping = {6:0, 5:1, 4:2, 3:3, 2:4, 1:5}


    @property
    def tabs_path(self):
        return self._tab_path


    @tabs_path.setter
    def tabs_path(self, path):
        self._tab_path = path


    def create_tab(self, tempo, beats):
        i = 1
        # Create a directory with a default tab_name, which will contain the meta file and all the recorded loops
        dir_name = os.path.join(self.tabs_path, self.default_tab_dir_name + str(i))

        while os.path.isdir(dir_name): #Check if dir already exists
            i += 1
            dir_name = os.path.join(self.tabs_path, self.default_tab_dir_name + str(i))
        
        os.mkdir(dir_name)

        # Write the header (tempo and number of beats) in the Meta.agu file
        header = [self.header_tempo + str(tempo) + '\n', self.header_beats + str(beats) + '\n']
        with open(dir_name + '/' + self.meta_tab_file , 'w') as file:
            file.writelines(header)

        # Returns the name of the directory containing the files
        return self.default_tab_dir_name + str(i)


    # Returns a list of all available tabs in the tab folder
    # Two modes:
    #       1: Return both (gp3,gp4, gp5) and .agu format
    #       2: Return only .agu format
    def get_available_tabs(self, check_mode):
        consistent_tabs = []

        if check_mode == 1:
            for file_name in sorted(os.listdir(self.tabs_path)):                                # Check all files in tab_path, both files (.gpX) and dirs (agu format)
                if os.path.isfile(os.path.join(self.tabs_path, str(file_name))):                # If it is a file, check that the extension is in (gp3,4,5)
                    if str(file_name)[-3:] in self.gp_extensions:
                        consistent_tabs.append(file_name)
                elif os.path.isdir(os.path.join(self.tabs_path, str(file_name))):               # If its a dir, check that it contains a Meta.agu file
                    for sub_file_name in sorted(os.listdir(os.path.join(self.tabs_path , str(file_name)))):
                        if str(sub_file_name)[-3:] in self.agu_extension:
                            consistent_tabs.append(file_name)
                            break

        elif check_mode == 2:
            for file_name in sorted(os.listdir(self.tabs_path)):                # Check all dirs in tab_path
                if os.path.isdir(os.path.join(self.tabs_path, str(file_name))):              # If its a dir, check that it contains a Meta.agu file
                    for sub_file_name in sorted(os.listdir(os.path.join(self.tabs_path, str(file_name)))):
                        if str(sub_file_name)[-3:] in self.agu_extension:
                            consistent_tabs.append(file_name)
                            break

        return consistent_tabs


    # For gpX, the name of the tab corresponds directly to the name of the saved_file (tab_name.gpX), but for .agu format,
    # the name of the tab that the user sees on the screen correspond to a folder, in which a .agu file is.
    # So this function returns the real tab saved_file, from either a gpX:
    #       - /default/tab/dir/tab_name.gpX
    #   or from a .agu tab:
    #       - /default/tab/dir/tab_name/Meta.agu
    # Return 0 if gpX format, 1 if Meta.agu file
    def grab_tab_file_from_node_name(self, tab_name):
        tab_name_absolute_path = os.path.join(self.tabs_path, tab_name)
        if os.path.isfile(tab_name_absolute_path):
            return (tab_name_absolute_path, 0)
        elif os.path.isdir(tab_name_absolute_path):
            return (os.path.join(tab_name_absolute_path, self.meta_tab_file), 1)


    # This function allows to play the tab entierly, or to it play in a range from a to b, and wrapped in a loop
    def play_tab(self, absolute_tab_path, is_agu_file, from_loop = None, to_loop = None):
        # tab_path points directly to either a tab.gpX format, or directly to a Meta.agu format, thanks to the
        # grab_tab_file_from_name function

        if not self.is_tab_playing:
            self.is_tab_playing = True

            # Set all servos to low position
            self.servo_manager.setAllServosLowPosition()

            if is_agu_file:
                with open(absolute_tab_path) as tab_file:
                    lines = tab_file.readlines()

                # The first two lines contain the meta info
                tempo = int(lines[0].split(',')[1].rstrip('\n'))
                beats_per_loop = int(lines[1].split(',')[1].rstrip('\n'))

                end_of_tab_event_timer = 0      # This timer will be added after the very last note, to send a signal that the tab is over.
                
                start_at_loop = 1
                end_after_loop = len(lines) - 2

                pre_event_array = []            # Will store all the notes of the considered loops. Then, will will duplicate X time, in order
                                                # to play the selection in loop

                if from_loop != None:
                    start_at_loop = from_loop
                if to_loop != None:
                    end_after_loop = to_loop
                nb_of_loops = end_after_loop - start_at_loop + 1

                # Retrieve dir path from tab path
                absolute_tab_dir = absolute_tab_path.split('/')
                absolute_tab_dir.pop()
                absolute_tab_dir = '/'.join(absolute_tab_dir)

                
                for i, line in enumerate(lines[2 + start_at_loop - 1 : 2 + end_after_loop]):
                    with open(os.path.join(absolute_tab_dir, line.rstrip('\n'))) as loop_file:
                        loop_notes = loop_file.readlines()
                    for note in loop_notes:
                        note_time = float(note.split(',')[1].rstrip('\n'))
                        note_string = int(note.split(',')[0])
                        pre_event_array.append(((note_time + i )* beats_per_loop * 60 / tempo, note_string))
                        

                # If we play the song as a whole, we do not loop it.
                # Otherwise, if its a small portion, we do it.
                repeat = 1
                if from_loop != None and to_loop != None:
                    repeat = self.repeat_loop_X_time

                for i in range (repeat):
                    for time, string in pre_event_array:
                        self.events.append(Timer(time + i * self.beats * 60/self.current_tempo * nb_of_loops, self.servo_manager.trigger_servo, [string]))
                
                end_of_tab_event_timer = (self.repeat_loop_X_time - 1) * self.beats * 60/self.current_tempo * nb_of_loops + pre_event_array[-1][0]\
                    + self.end_of_tab_event_offset
                
                # Add a timer that will trigger an end_of_tab callback
                self.events.append(Timer(end_of_tab_event_timer, self.end_of_tab_callback))


            else :
                end_of_tab_event_timer = 0
                song = pygp.parse(absolute_tab_path)
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
                                end_of_tab_event_timer = note_time
                                for note in beat.notes:
                                    self.events.append(Timer(note_time, self.servo_manager.trigger_servo, [self.gp_to_agu_mapping[note.string]]))


                    measure_number = measure_number + 1

                self.events.append(Timer(end_of_tab_event_timer + 0.2, self.end_of_tab_callback))
            
            print("This tab has {0} notes and thus, will try to create {0} threads.".format(len(self.events)))
            
            
            try:
                for event in self.events:
                    event.start()

            except RuntimeError as e:
                print("If an error occurs below, complaining about not being able to create more threads, then \
                you will have to lower the size allocated to ")
                print(e)



    def end_of_tab_callback(self): # Sends a signal when the tab is over
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


    def process_loop(self): # No matter whether the loop is saved or note, some process is done
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
        for i in range(0, self.repeat_newly_saved_loop_X_time):
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


    def save_loop(self, absolute_tab_dir):
        i = 1
        loop_file = os.path.join(absolute_tab_dir, "Loop_" + str(i))
        while os.path.isfile(loop_file):
            i += 1
            loop_file = os.path.join(absolute_tab_dir, "Loop_" + str(i))

        with open(loop_file, 'w') as loop_file:
            for string, time in self.sorted_notes_list:
                loop_file.write(str(string) + "," + str(time / (self.beats * 60 / self.current_tempo)) + '\n')

        with open(os.path.join(absolute_tab_dir, self.meta_tab_file), 'a') as tab_file:
            tab_file.write(self.default_loop_name+ str(i) + '\n')


    def load_tab_info(self, absolute_tab_path):
        with open(absolute_tab_path) as file:
            lines = file.readlines()
            self.current_tempo = int(lines[0].split(',')[1])
            self.beats = int(lines[1].split(',')[1])
            nb_of_loops = len(lines) - 2

        return self.current_tempo, self.beats, nb_of_loops


    def clear_events(self):
        for event in self.events:
            event.cancel()   
        self.events.clear()
        self.is_tab_playing = False


    def clear_saved_notes(self):
        self.saved_notes_list = [[] for i in range(6)]  
        self.pre_record_list = [False, False, False, False, False, False]
        self.sorted_notes_list = []
