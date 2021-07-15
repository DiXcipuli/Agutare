from anytree import NodeMixin, RenderTree
from RPi import GPIO
import I2C_LCD_driver
import actions
import os
import threading
import time

GPIO.setmode(GPIO.BCM)
buzzer_pin = 12 
buzzer_freq = 440
buzzer_duration = 0.07
GPIO.setup(buzzer_pin, GPIO.OUT) 
buzzer_pwm = GPIO.PWM(buzzer_pin, buzzer_freq)
default_tempo = 60

default_beats_to_record = 4
min_beats_to_record = 1
max_beats_to_record = 8


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



class TabPlayerItem(BasicMenuItem): #text_to_display has to be the tab name as follow: 'ComeAsYouAre.gp3'
    def __init__(self, node_name, index, size, text_to_display, tab_path, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.is_tab_palying = False
        self.tab_path = tab_path

    def execute(self):
        if not self.is_tab_palying:
            self.is_tab_palying = True
            self.update_display()
            actions.playTab(self.tab_path + self.text_to_display)
        return self

    def back_in_menu(self):
        if self.is_tab_palying:
            self.is_tab_palying = False
            actions.clear_events()
            return self
        else:
            return self.parent
        

    def update_display(self):
        lcd_display.lcd_clear()
        if self.is_tab_palying:
            lcd_display.lcd_display_string("Playing", 1)
        else:
            super().update_display()

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

class MetronomeItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, new_tab_mode, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.current_tempo = default_tempo
        self.saved_tempo = default_tempo
        self.tempo_factor = 5
        self.is_metronome_on = False
        self.new_tab_mode = new_tab_mode
        
    def next(self):
        if self.is_metronome_on:
            self.current_tempo = self.current_tempo + self.tempo_factor
            return self
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
                actions.createTab(self.current_tempo)
                lcd_display.lcd_clear()
                lcd_display.lcd_display_string("Tab Created !", 1)
                time.sleep(menu_sleeping_time)
                return self.children[0]
            else:
                self.current_tempo = default_tempo
        return self

    def update_display(self):
        lcd_display.lcd_clear()
        lcd_display.lcd_display_string(self.text_to_display, 1)

        if self.is_metronome_on:
            lcd_display.lcd_display_string(str(self.current_tempo), 2)
        else:
            lcd_display.lcd_display_string(self.pos_indication, 2)

    def back_in_menu(self):
        if self.is_metronome_on:
            self.is_metronome_on = False
            return self
        else:
            return self.parent


    def metronomeThread(self):
        if self.is_metronome_on:
            timer = 60 / self.current_tempo
            threading.Timer(timer, self.metronomeThread).start()

            #Trigger the buzzer to a specify pwm frequency
            buzzer_pwm.start(50) # Duty cycle, between 0 and 100
            time.sleep(buzzer_duration)
            buzzer_pwm.stop()
            #Uncomment to check th number of Thread object running
            print(threading.active_count())

class RecordSessionItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.beats_to_record = default_beats_to_record
        self.is_metronome_on = False
        self.is_armed = False
        self.is_recording = False
        self.is_saving_state = False
        self.current_beat = 0
        self.current_tempo = default_tempo

    def execute(self):
        self.is_armed = not self.is_armed

        if self.is_armed:
            self.current_beat = 0 # Reset the beat
            self.is_metronome_on = True # Running metronome
            self.metronomeThread()
        return self

    def metronomeThread(self):
        if self.is_metronome_on:
            timer = 60 / self.current_tempo
            threading.Timer(timer, self.metronomeThread).start()

            buzzer_pwm.start(50) # Duty cycle, between 0 and 100
            if self.is_armed or self.is_recording:
                self.current_beat += 1 
            if self.current_beat > self.beats_to_record:
                self.current_beat = 1
                if self.is_armed:
                    self.is_armed = False
                    self.is_recording = True
                elif self.is_recording:
                    self.is_recording = False
                    self.is_saving_state = True
                    self.is_metronome_on = False
            
            if self.is_armed or self.is_recording or self.is_saving_state:
                self.update_display()

            time.sleep(buzzer_duration)
            buzzer_pwm.stop()

    def next(self): # Here the next button increases the number of beats to be recorded
        self.beats_to_record += 1
        if self.beats_to_record > max_beats_to_record:
            self.beats_to_record = min_beats_to_record

        return self

    def previous(self): # Here the previous button triggers and stop the metronome
        self.is_metronome_on = not self.is_metronome_on
        self.current_beat = 0

        if self.is_metronome_on:
            self.metronomeThread()

        return self

    def back_in_menu(self):
        self.is_metronome_on = False
        return self

    def update_display(self):
        lcd_display.lcd_clear()
        if self.is_recording:
            lcd_display.lcd_display_string("Recording " + str(self.current_beat), 1)
        elif self.is_armed:
            lcd_display.lcd_display_string("Armed " + str(self.current_beat), 1)
        elif self.is_saving_state:
            lcd_display.lcd_display_string("Save Loop ?", 1)
        else:
            lcd_display.lcd_display_string("Not Armed " + str(self.beats_to_record), 1)

        if not self.is_saving_state:
            if self.is_metronome_on:
                lcd_display.lcd_display_string("Metronome On", 2)
            else:
                lcd_display.lcd_display_string("Metronome Off", 2)
   
            

class MenuHandler:  # This class will create the whole tree, and will be used to return the current_node.
    def __init__(self, custom_tab_path, tab_path):
        self.tab_path = tab_path
        self.custom_tab_path = custom_tab_path

        self.welcome_msg = "Guitar Ready!"
        self.welcome_state = True

        # Root level
        self.root_node = BasicMenuItem("Root", 0, 1, "Root")
        # Level 1
        level_1_size = 4
        self.play_tab_node = BasicMenuItem("play_tab_node", 0, level_1_size, "Play Tab", self.root_node)
        self.practice_node = BasicMenuItem("practice_node", 1, level_1_size, "Practice", self.root_node)
        self.string_test_node = BasicMenuItem("string_test_node", 2, level_1_size, "String test", self.root_node)
        self.servo_pos_node = BasicMenuItem("motor_pos_node", 3, level_1_size, "Servo position", self.root_node)
        # Level 2
        # Level 2_1 (Inside 'Play Tab' menu)
        self.tab_node_list = []
        self.custom_tab_node_list = []

        for index, file_name  in enumerate(os.listdir(tab_path)): # Populating the list with all the files in the 'tab_path' folder
            self.tab_node_list.append(TabPlayerItem(str(file_name), index, len(os.listdir(tab_path)), str(file_name), self.tab_path,  self.play_tab_node))

        # Level 2_2 (Inside 'Practice' menu)
        level_2_2_size = 2
        self.metronome_node = MetronomeItem("metronome_node", 0, level_2_2_size, "Metronome",False, self.practice_node)
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

        self.new_tab_node = MetronomeItem("new_tab_node", 0, level_2_2_size, "New Tab",True, self.record_node)
        RecordSessionItem("RS", 0, 1, "", self.new_tab_node)
        self.existing_tab_node = BasicMenuItem("existing_tab_node", 1, level_2_2_size, "Existing Tabs", self.record_node)
        
        for i, file_name in enumerate(os.listdir(self.custom_tab_path)):   # Populating the list with all the files in the 'custom_tab_path' folder
            self.custom_tab_node_list.append(BasicMenuItem(str(file_name), i, len(os.listdir(self.custom_tab_path)), str(file_name), self.existing_tab_node))
            RecordSessionItem("RS_" + str(file_name), 0, 1, "", self.custom_tab_node_list[i])

    def display_welcome_msg(self):
        lcd_display.lcd_display_string(self.welcome_msg)

    def get_current_node(self):
        return self.current_node

    def execute(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        else:
            self.current_node = self.current_node.execute()

    def back_in_menu(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        else:
            self.current_node = self.current_node.back_in_menu()
    
    def next(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        else:
            self.current_node = self.current_node.next()

    def previous(self):
        if self.welcome_state:
            self.welcome_state = False
            self.current_node = self.play_tab_node
        self.current_node = self.current_node.previous()

    def update_display(self):
        self.current_node.update_display()

    def display_tree(self):
        for pre, fill, node in RenderTree(self.root_node):
            print("%s%s" % (pre, node.node_name))