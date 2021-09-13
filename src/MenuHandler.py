from anytree import NodeMixin, RenderTree
from RPi import GPIO
import I2C_LCD_driver
import actions
import os
import threading
import time
import guitarpro as pygp
from threading import Timer
from EnumClasses import MetronomeState, TabCreatorState, SessionRecorderState

GPIO.setmode(GPIO.BCM)

buzzer_pin = 12 
buzzer_freq = 440
buzzer_duration = 0.07
GPIO.setup(buzzer_pin, GPIO.OUT) 
buzzer_pwm = GPIO.PWM(buzzer_pin, buzzer_freq)
default_tempo = 60

custom_tab_path = '/home/pi/Documents/RobotizeGuitar/CustomTabs/'
tab_path = '/home/pi/Documents/RobotizeGuitar/Tabs/'                # For tabs which wont be edited


default_bars_to_record = 1
min_bars_to_record = 1
max_bars_to_record = 2

lcd_display = I2C_LCD_driver.lcd() 
menu_sleeping_time = 0.5 # The time needed to display some useful information


class BasicMenuItem(NodeMixin):
    def __init__(self, node_name, index, size, text_to_display , parent = None, children = None):
        self.node_name = node_name
        self.index = index
        self.size = size
        self.parent = parent
        self.text_to_display = text_to_display
        self.pos_indication = str(self.index + 1) + " / " + str(self.size)
        if children:
            self.children = children

    def execute(self):
        if self.is_leaf:
            return self
        else:
            return self.children[0]
            
    def back_in_menu(self):
        if self.parent.is_root:
            return self
        else:
            return self.parent

    def next(self):
        if self.index + 1 >= self.size:
            return self.parent.children[0]
        else:
            return self.parent.children[self.index + 1]

    def previous(self):
        if self.index - 1 < 0:
            return self.parent.children[self.size - 1]
        else:
            return self.parent.children[self.index - 1]

    def update_display(self):
        lcd_display.lcd_clear()
        lcd_display.lcd_display_string(self.text_to_display, 1) # LCD line 1 
        lcd_display.lcd_display_string(self.pos_indication, 2) # LCD line 2

    def on_focus(self):
        pass

    def node_type(self):
        return "BasicMenuItem"

class TabPlayerItem(BasicMenuItem): #text_to_display has to be the tab name as follow: 'ComeAsYouAre.gp3'
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.is_tab_palying = False
        self.events = []

    def execute(self):
        if not self.is_tab_palying:
            self.is_tab_palying = True
            self.update_display()
            self.playTab(self.tab_path + self.text_to_display)
        return self

    def back_in_menu(self):
        if self.is_tab_palying:
            self.is_tab_palying = False
            self.clear_events()
            return self
        else:
            return self.parent
        

    def update_display(self):
        lcd_display.lcd_clear()
        if self.is_tab_palying:
            lcd_display.lcd_display_string("Playing", 1)
        else:
            super().update_display()

    def playTab():
        # Set all motors to low position
        actions.setServoLowPosition()
        
        #Load tab
        song = pygp.parse(tab_path + self.node_name)
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
                    beat_time = beat_time + (beat.duration.time/1000)* (60/song.tempo)
                    if beat.notes:
                        for note in beat.notes:
                            self.events.append(Timer(note_time, trigger_servo, [note.string - 1]))
                                
            measure_number = measure_number + 1
        for event in self.events:
            event.start()
        print("-- Tab is Starting -- With ", len(events), " threads" )

    def clear_events():
        for event in self.events:
            event.cancel()   
        events.clear()

    def node_type(self):
        return "TabPlayerItem"

class StringTestItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.is_string_test_running = False
        self.servo_routine_sleep = 0.5

    def execute(self):
        if not self.is_string_test_running:
            self.is_string_test_running = True
            testThread = threading.Thread(target=self.string_test_loop)
            testThread.start()
        return self
            
    def string_test_loop(self):
        while self.is_string_test_running:
            actions.trigger_servo(self.index)
            time.sleep(self.servo_routine_sleep)

    def back_in_menu(self):
        if self.is_string_test_running:
            self.is_string_test_running = False
            return self
        else:
            return self.parent

    def update_display(self):
        lcd_display.lcd_clear()
        if self.is_string_test_running:
            lcd_display.lcd_display_string("String " + str(self.index + 1) + " playing", 1)
        else:
            lcd_display.lcd_display_string("String " + str(self.index + 1), 1)

    def node_type(self):
        return "StringTestItem"

class ServoPositionItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)

    def execute(self):
        if self.index == 0: # Servo to LOW position
            actions.setServoLowPosition()
        elif self.index == 1:
            actions.setServoMidPosition()
        elif self.index == 2:
            actions.setServoHighPosition()

        lcd_display.lcd_clear()
        lcd_display.lcd_display_string("Set !", 1)
        time.sleep(menu_sleeping_time)
       
        return self   

    def node_type(self):
        return "ServoPositionItem"

class MetronomeItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.current_tempo = default_tempo
        self.saved_tempo = default_tempo
        self.tempo_factor = 5
        self.state = MetronomeState.IDLE
        
    def next(self):
        if self.state == MetronomeState.DEFINING_TEMPO:
            self.current_tempo = self.current_tempo + self.tempo_factor
            return self
        else:
            return super().next()
        
    def previous(self):
        if self.state == MetronomeState.DEFINING_TEMPO:
            self.current_tempo = self.current_tempo - self.tempo_factor
            return self
        else:
            return super().next()
        

    def execute(self):
        if self.state == MetronomeState.IDLE:
            self.state = MetronomeState.DEFINING_TEMPO
            self.metronomeThread()
        # else:
        #     if self.new_tab_mode:
        #         self.is_metronome_on = False
        #         tab_name = actions.createTab(self.current_tempo)
        #         lcd_display.lcd_clear()
        #         lcd_display.lcd_display_string("Tab Created !", 1)
        #         time.sleep(menu_sleeping_time)
        #         self.children[0].node_name = str(tab_name)
        #         self.children[0].current_tempo = self.current_tempo
        #         return self.children[0]
        else:
            self.current_tempo = default_tempo
        return self

    def back_in_menu(self):
        if self.state == MetronomeState.DEFINING_TEMPO:
            self.state = MetronomeState.IDLE
            return self
        else:
            return self.parent

    def update_display(self):
        lcd_display.lcd_clear()
        lcd_display.lcd_display_string(self.text_to_display, 1)

        if self.state == MetronomeState.DEFINING_TEMPO:
            lcd_display.lcd_display_string(str(self.current_tempo), 2)
        else:
            lcd_display.lcd_display_string(self.pos_indication, 2)


    def metronomeThread(self):
        if self.state == MetronomeState.DEFINING_TEMPO:
            timer = 60 / self.current_tempo
            threading.Timer(timer, self.metronomeThread).start()

            #Trigger the buzzer to a specify pwm frequency
            buzzer_pwm.start(50) # Duty cycle, between 0 and 100
            time.sleep(buzzer_duration)
            buzzer_pwm.stop()
            #Uncomment to check th number of Thread object running
            #print(threading.active_count())

    def node_type(self):
        return "MetronomeItem"


class TabCreatorItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent = None, children = None)
        self.current_tempo = default_tempo
        self.saved_tempo = default_tempo
        self.tempo_factor = 5
        self.state = TabCreatorState.IDLE
        self.beat = 4

    def next(self):
        if self.state == TabCreatorState.DEFINING_TEMPO:
            self.current_tempo = self.current_tempo + self.tempo_factor
            return self
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.beat += 1
        else:
            return super().next()
        
    def previous(self):
        if self.is_metronome_on:
            self.current_tempo = self.current_tempo - self.tempo_factor
            return self
        else:
            return super().next()
        

    def execute(self):
        if not self.is_metronome_on:
            self.is_metronome_on = True
            self.metronomeThread()
        else:
            if self.new_tab_mode:
                self.is_metronome_on = False
                tab_name = actions.createTab(self.current_tempo)
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Tab Created !", 1)
                time.sleep(menu_sleeping_time)
                self.children[0].node_name = str(tab_name)
                self.children[0].current_tempo = self.current_tempo
                return self.children[0]
            else:
                self.current_tempo = default_tempo
        return self

    def back_in_menu(self):
        if self.is_metronome_on:
            self.is_metronome_on = False
            return self
        else:
            return self.parent

    def update_display(self):
        lcd_display.lcd_clear()
        lcd_display.lcd_display_string(self.text_to_display, 1)

        if self.is_metronome_on:
            lcd_display.lcd_display_string(str(self.current_tempo), 2)
        else:
            lcd_display.lcd_display_string(self.pos_indication, 2)


    def metronomeThread(self):
        if self.is_metronome_on:
            timer = 60 / self.current_tempo
            threading.Timer(timer, self.metronomeThread).start()

            #Trigger the buzzer to a specify pwm frequency
            buzzer_pwm.start(50) # Duty cycle, between 0 and 100
            time.sleep(buzzer_duration)
            buzzer_pwm.stop()
            #Uncomment to check th number of Thread object running
            #print(threading.active_count())

    def node_type(self):
        return "MetronomeItem"




class SessionRecorderItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent, pseudo_parent, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.bars_to_record = default_bars_to_record
        self.is_metronome_on = False
        self.current_beat = 0
        self.current_tempo = default_tempo
        self.current_state = SessionRecorderState.NOT_ARMED
        self.pseudo_parent = pseudo_parent
        self.bar_starting_time = 0
        self.saved_notes_list = [[] for i in range(6)]  #Contains the time where the string was triggered, not the duration yet
        self.pre_record_list = [False, False, False, False, False, False]
        self.sorted_notes_list = []
        self.events = []

    def execute(self):
        if self.current_state == SessionRecorderState.NOT_ARMED:
            self.current_state = SessionRecorderState.ARMED
            self.current_beat = 0 # Reset the beat
            self.is_metronome_on = True # Running metronome
            self.metronomeThread()
        elif self.current_state == SessionRecorderState.ARMED:
            self.current_state = SessionRecorderState.NOT_ARMED
            self.is_metronome_on = False
        elif self.current_state == SessionRecorderState.SAVING:
            self.saveLoop()
            self.current_state = SessionRecorderState.NOT_ARMED
            self.clean_events()
        
        return self

    def metronomeThread(self):
        if self.is_metronome_on:
            timer = 60 / self.current_tempo
            threading.Timer(timer, self.metronomeThread).start()

            buzzer_pwm.start(50) # Duty cycle, between 0 and 100
            if self.current_state == SessionRecorderState.ARMED or self.current_state == SessionRecorderState.RECORDING:
                self.current_beat += 1 
            if self.current_beat > self.beats:
                self.current_beat = 1
                if self.current_state == SessionRecorderState.ARMED:
                    self.current_state = SessionRecorderState.RECORDING
                    self.bar_starting_time = time.time()
                elif self.current_state == SessionRecorderState.RECORDING:
                    self.process_loop()
                    self.current_state = SessionRecorderState.SAVING
                    self.is_metronome_on = False
            
            if not self.current_state == SessionRecorderState.NOT_ARMED:
                self.update_display()

            time.sleep(buzzer_duration)
            buzzer_pwm.stop()

    def next(self): # Here the next button increases the number of beats to be recorded
        if self.current_state == SessionRecorderState.NOT_ARMED:
            self.bars_to_record += 1
            if self.bars_to_record > max_bars_to_record:
                self.bars_to_record = min_bars_to_record

        return self

    def previous(self): # Here the previous button triggers and stop the metronome
        if self.current_state == SessionRecorderState.NOT_ARMED:
            self.is_metronome_on = not self.is_metronome_on
            self.current_beat = 0

            if self.is_metronome_on:
                self.metronomeThread()
            
        return self

    def back_in_menu(self):
        self.is_metronome_on = False

        if self.current_state == SessionRecorderState.ARMED:
            self.current_state = SessionRecorderState.NOT_ARMED
            return self
        elif self.current_state == SessionRecorderState.NOT_ARMED:
            return self.pseudo_parent
        elif self.current_state == SessionRecorderState.RECORDING:
            self.current_state = SessionRecorderState.NOT_ARMED
            return self
        elif self.current_state == SessionRecorderState.SAVING:
            self.current_state = SessionRecorderState.NOT_ARMED
            self.clear_events()
            #CLEAR EVENT LIST
            return self
    
    def clear_events(self):
        for event in self.events:
            event.cancel()
        self.events = []

    def update_display(self):
        lcd_display.lcd_clear()
        if self.current_state == SessionRecorderState.RECORDING:
            lcd_display.lcd_display_string("Recording " + str(self.current_beat), 1)
        elif self.current_state == SessionRecorderState.ARMED:
            lcd_display.lcd_display_string("Armed " + str(self.current_beat), 1)
        elif self.current_state == SessionRecorderState.SAVING:
            lcd_display.lcd_display_string("Save Loop ?", 1)
        else:
            lcd_display.lcd_display_string("Not Armed   B:" + str(self.bars_to_record), 1)

        if self.current_state == SessionRecorderState.NOT_ARMED:
            if self.is_metronome_on:
                lcd_display.lcd_display_string("Metronome On", 2)
            else:
                lcd_display.lcd_display_string("Metronome Off", 2)

    def save_note(self, index):
        if self.current_state == SessionRecorderState.ARMED:
            self.pre_record_list[index] = True
        elif self.current_state == SessionRecorderState.RECORDING:
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
        self.saved_notes_list = [[] for i in range(6)]
        self.bar_starting_time = 0

        self.replay_loop()
    
    def replay_loop(self):
        for i in range(0, 5):
            for string, time in self.sorted_notes_list:
                self.events.append(Timer(time + (i * self.beats * 60/self.current_tempo), actions.trigger_servo, [string]))
                print(time + (i * self.beats * 60/self.current_tempo))

        for event in self.events:
            event.start()
        
    def print_saved_notes(self):
        #In term of note starting time in seconds
        print("|------------------------------------------------------")
        print("| Loop recorded over " + str(self.bars_to_record) + " beats")
        print("|------------------------------------------------------")
        print("|   String id     |      starting time (in s)")
        print("|------------------------------------------------------")
        for i, time in self.sorted_notes_list:
            print("|   String " + str(i + 1) + "      |      " + str(time) + " s")

        print("|------------------------------------------------------")


    def on_focus(self):
        self.load_tab_info()
        

    def load_tab_info(self):
        #The tab name is already stored at this point, we only need to update:
        #   -tempo
        #   -beats
        with open(custom_tab_path + self.node_name + "/Meta.agu") as file:
            lines = file.readlines()
            self.current_tempo = int(lines[0].split(',')[1])
            self.beats = int(lines[1].split(',')[1])

    def saveLoop(self):
        i = 0
        loop_file = custom_tab_path + self.node_name + '/' + "Loop_" + str(i)
        while os.path.isfile(loop_file):
            i += 1
            loop_file = custom_tab_path + self.node_name + '/' + "Loop_" + str(i)

        with open(loop_file, 'w') as saved_file:
            for string, time in self.sorted_notes_list:
                saved_file.write(str(string) + "," + str(time / self.beats) + '\n')

        with open('../CustomTabs/' + self.node_name + "/MetaDefault.agu", 'a') as saved_file:
            saved_file.write("Loop_" + str(i) + '\n')

    def node_type(self):
        return "SessionRecorderItem"
        

class MenuHandler:  # This class will create the whole tree, and will be used to return the current_node.
    def __init__(self):
        self.welcome_msg = "Guitar Ready!"
        self.welcome_state = True

        # Root
        self.root_node = BasicMenuItem("Root", 0, 1, "Root")
        level_1_size = 4
        self.play_tab_node = BasicMenuItem("play_tab_node", 0, level_1_size, "Play Tab", self.root_node)
        self.practice_node = BasicMenuItem("practice_node", 1, level_1_size, "Practice", self.root_node)
        self.string_test_node = BasicMenuItem("string_test_node", 2, level_1_size, "String test", self.root_node)
        self.servo_pos_node = BasicMenuItem("motor_pos_node", 3, level_1_size, "Servo position", self.root_node)
        
        self.tab_node_list = []
        self.custom_tab_node_list = []

        for index, file_name  in enumerate(sorted(os.listdir(tab_path))): # Populating the list with all the files in the 'tab_path' folder
            self.tab_node_list.append(TabPlayerItem(str(file_name), index, len(os.listdir(tab_path)), str(file_name),  self.play_tab_node))

        # Level 2_2 (Inside 'Practice' menu)
        level_2_2_size = 2
        self.metronome_node = MetronomeItem("metronome_node", 0, level_2_2_size, "Metronome", self.practice_node)
        self.record_node = BasicMenuItem("record_node", 1, level_2_2_size, "Record", self.practice_node)
        
        # Level 2_3 (Inside 'String test' menu)
        self.string_test_node_list = []
        for i in range(0,6):
            self.string_test_node_list.append(StringTestItem("String " + str(i + 1), i, 6, "String " + str(i + 1), parent = self.string_test_node))

        # Level 2_4 (Inside 'Servo position' menu)
        self.servo_pos_node_list = []
        servo_text = ["Low", "Mid", "High"]
        for i in range(0,3):
            self.servo_pos_node_list.append(ServoPositionItem("Servos to " + servo_text[i], i, 3, "Servos to " + servo_text[i], parent = self.servo_pos_node))

        self.new_tab_node = MetronomeItem("new_tab_node", 0, level_2_2_size, "New Tab", self.record_node)
        SessionRecorderItem("RS", 0, 1, "", self.new_tab_node, self.play_tab_node)
        self.existing_tab_node = BasicMenuItem("existing_tab_node", 1, level_2_2_size, "Existing Tabs", self.record_node)
        
        for i, file_name in enumerate(sorted(os.listdir(custom_tab_path))):   # Populating the list with all the files in the 'custom_tab_path' folder
            self.custom_tab_node_list.append(BasicMenuItem(str(file_name), i, len(os.listdir(custom_tab_path)), str(file_name), self.existing_tab_node))
            SessionRecorderItem(str(file_name), 0, 1, "", self.custom_tab_node_list[i], self.play_tab_node)

    def display_welcome_msg(self):
        lcd_display.lcd_display_string(self.welcome_msg)

    def get_current_node(self):
        return self.current_node

    def execute(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        else:
            previous_node = self.current_node
            self.current_node = self.current_node.execute()
            if not self.current_node is previous_node:
                self.current_node.on_focus()

    def back_in_menu(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        else:
            previous_node = self.current_node
            self.current_node = self.current_node.back_in_menu()
            if not self.current_node is previous_node:
                self.current_node.on_focus()
    
    def next(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        else:
            previous_node = self.current_node
            self.current_node = self.current_node.next()
            if not self.current_node is previous_node:
                self.current_node.on_focus()

    def previous(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        else:
            previous_node = self.current_node
            self.current_node = self.current_node.previous()
            if not self.current_node is previous_node:
                self.current_node.on_focus()

    def update_display(self):
        self.current_node.update_display()

    def display_tree(self):
        for pre, fill, node in RenderTree(self.root_node):
            print("%s%s --> (%s)" % (pre, node.node_name, node.node_type()))