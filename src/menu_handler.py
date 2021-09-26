from anytree import NodeMixin, RenderTree
import I2C_LCD_driver
import os
import threading
import time
import guitarpro as pygp
from threading import Timer
from enum_classes import TabCreatorState, SessionRecorderState
from metronome import metronome
from servos import servo
from tab_manager import tab_manager
from gpiozero import Button


default_tempo = 60
default_beats_per_loop = 4

custom_tab_path = '/home/pi/Documents/RobotizeGuitar/CustomTabs/'
tab_path = '/home/pi/Documents/RobotizeGuitar/Tabs/'                # For tabs which wont be edited


default_bars_to_record = 1
min_bars_to_record = 1
max_bars_to_record = 2

lcd_display = I2C_LCD_driver.lcd() 
menu_sleeping_time = 1.2 # The time needed to display some useful information


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


    def execute(self):
        if not self.is_tab_palying:
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
            servo.trigger_servo(self.index)
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
            servo.setServoLowPosition()
        elif self.index == 1:
            servo.setServoMidPosition()
        elif self.index == 2:
            servo.setServoHighPosition()

        lcd_display.lcd_clear()
        lcd_display.lcd_display_string("Set !", 1)
        time.sleep(menu_sleeping_time)
       
        return self   

    def node_type(self):
        return "ServoPositionItem"


class FreePlayItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        #self.metronome = Metronome()
        
    def next(self):
        if metronome.is_metronome_active:
            metronome.increase_tempo()
            return self
        else:
            return super().next()
        
    def previous(self):
        if metronome.is_metronome_active:
            metronome.decrease_tempo()
            return self
        else:
            return super().next()
        

    def execute(self):
        if not metronome.is_metronome_active:
            metronome.start_metronome()
        else:
            metronome.reset_tempo()
        return self

    def back_in_menu(self):
        if metronome.is_metronome_active:
            metronome.stop_metronome()
            return self
        else:
            return self.parent

    def update_display(self):
        lcd_display.lcd_clear()
        lcd_display.lcd_display_string(self.text_to_display, 1)

        if metronome.is_metronome_active:
            lcd_display.lcd_display_string(str(metronome.tempo), 2)
        else:
            lcd_display.lcd_display_string(self.pos_indication, 2)


    def node_type(self):
        return "FreePlayItem"


class TabCreatorItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.state = TabCreatorState.IDLE
        #self.metronome = Metronome()

    def next(self):
        if self.state == TabCreatorState.DEFINING_TEMPO:
            metronome.increase_tempo()
            return self
        elif self.state == TabCreatorState.DEFINING_BEATS:
            metronome.increase_beats_per_loop()
            return self
        else:
            return super().next()
        
    def previous(self):
        if self.state == TabCreatorState.DEFINING_TEMPO:
            metronome.decrease_tempo()
            return self
        elif self.state == TabCreatorState.DEFINING_BEATS:
            metronome.decrease_beats_per_loop()
            return self
        else:
            return super().next()
        

    def execute(self):
        if self.state == TabCreatorState.IDLE:
            self.state = TabCreatorState.DEFINING_TEMPO
            metronome.start_metronome()
        elif self.state == TabCreatorState.DEFINING_TEMPO:
            self.state = TabCreatorState.DEFINING_BEATS
            metronome.stop_metronome()
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.state = TabCreatorState.IDLE
            tab_name = tab_manager.createTab(metronome.tempo, metronome.beats_per_loop)
            lcd_display.lcd_clear()
            lcd_display.lcd_display_string(tab_name, 1)
            lcd_display.lcd_display_string("Created !", 2)
            time.sleep(menu_sleeping_time)
            self.children[0].node_name = str(tab_name)
            return self.children[0]
        return self

    def back_in_menu(self):
        if self.state == TabCreatorState.IDLE:
            return self.parent
        elif self.state == TabCreatorState.DEFINING_TEMPO:
            self.state = TabCreatorState.IDLE
            metronome.stop_metronome()
            return self
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.state = TabCreatorState.DEFINING_TEMPO
            metronome.start_metronome()
            return self

    def update_display(self):
        lcd_display.lcd_clear()
        
        if self.state == TabCreatorState.IDLE:
            lcd_display.lcd_display_string(self.text_to_display, 1)
            lcd_display.lcd_display_string(self.pos_indication, 2)
        elif self.state == TabCreatorState.DEFINING_TEMPO:
            lcd_display.lcd_display_string("Tempo?", 1)
            lcd_display.lcd_display_string(str(metronome.tempo), 2)
        elif self.state == TabCreatorState.DEFINING_BEATS:
            lcd_display.lcd_display_string("Beats in loop?", 1)
            lcd_display.lcd_display_string(str(metronome.beats_per_loop), 2)


    def node_type(self):
        return "TabCreatorItem"


class SessionRecorderItem(BasicMenuItem):
    def __init__(self, node_name, index, size, text_to_display, parent, pseudo_parent, children = None):
        super().__init__(node_name, index, size, text_to_display, parent, children)
        self.bars_to_record = default_bars_to_record
        self.state = SessionRecorderState.IDLE
        self.pseudo_parent = pseudo_parent
        
        self.nb_of_loops = 0
        self.selected_loop = 0


    def execute(self):
        if self.state == SessionRecorderState.IDLE:
            metronome.start_metronome(self.metronome_callback)
            self.state = SessionRecorderState.METRONOME_ON
        elif self.state == SessionRecorderState.METRONOME_ON:
            metronome.current_beat = 0 # Reset the beat
            self.state = SessionRecorderState.ARMED
        elif self.state == SessionRecorderState.ARMED:
            self.state = SessionRecorderState.IDLE
            tab_manager.clear_saved_notes()
            metronome.stop_metronome()
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            self.state = SessionRecorderState.PLAYER_SELECTION
        elif self.state == SessionRecorderState.PLAYER_SELECTION: 
            self.state = SessionRecorderState.PLAYER_ON
            tab_manager.play_tab(custom_tab_path + self.node_name, True,  self.selected_loop)
        elif self.state == SessionRecorderState.SAVING:
            tab_manager.saveLoop()
            self.nb_of_loops =  tab_manager.load_tab_info(self.node_name)[0]
            self. selected_loop = self.nb_of_loops
            self.state = SessionRecorderState.IDLE
            tab_manager.clear_events()
            tab_manager.clear_saved_notes()
        
        return self

    def end_tab_callback(self):
        self.state = SessionRecorderState.PLAYER_IDLE
        self.update_display()


    def metronome_callback(self, overflow):
        print(metronome.current_beat)

        if overflow:
            if self.state == SessionRecorderState.ARMED:
                self.state = SessionRecorderState.RECORDING
                tab_manager.bar_starting_time = time.time()
            elif self.state == SessionRecorderState.RECORDING:
                tab_manager.process_loop()
                metronome.stop_metronome()
                self.state = SessionRecorderState.SAVING
                
        self.update_display()


    def next(self): # Here the next button increases the number of beats to be recorded
        if self.state in (SessionRecorderState.IDLE, SessionRecorderState.METRONOME_ON):
            self.state = SessionRecorderState.PLAYER_IDLE
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            self.state = SessionRecorderState.IDLE
        elif self.state == SessionRecorderState.PLAYER_SELECTION:
            self.selected_loop +=1
            if self.selected_loop > self.nb_of_loops:
                self.selected_loop = 1

        return self


    def previous(self): # Here the previous button triggers and stop the metronome
        if self.state in (SessionRecorderState.IDLE, SessionRecorderState.METRONOME_ON):
            self.state = SessionRecorderState.PLAYER_IDLE
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            self.state = SessionRecorderState.IDLE
        elif self.state == SessionRecorderState.PLAYER_SELECTION:
            self.selected_loop -=1
            if self.selected_loop < 1:
                self.selected_loop = self.nb_of_loops

        return self


    def back_in_menu(self):
        if self.state == SessionRecorderState.IDLE:
            return self.pseudo_parent
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            self.state = SessionRecorderState.IDLE
            return self
        elif self.state == SessionRecorderState.METRONOME_ON:
            self.state = SessionRecorderState.IDLE
            metronome.stop_metronome()
            return self
        elif self.state == SessionRecorderState.ARMED:
            self.state = SessionRecorderState.IDLE
            metronome.stop_metronome()
            return self
        elif self.state == SessionRecorderState.RECORDING:
            tab_manager.clear_saved_notes()
            metronome.stop_metronome()
            self.state = SessionRecorderState.IDLE
            return self
        elif self.state == SessionRecorderState.SAVING:
            self.state = SessionRecorderState.IDLE
            tab_manager.clear_saved_notes()
            tab_manager.clear_events()
            #CLEAR EVENT LIST
            return self
        elif self.state == SessionRecorderState.PLAYER_ON:
            self.state = SessionRecorderState.PLAYER_IDLE
            tab_manager.clear_events()
            return self
        elif self.state == SessionRecorderState.PLAYER_SELECTION:
            self.state = SessionRecorderState.PLAYER_IDLE
            tab_manager.clear_events()
            return self


    def update_display(self):
        lcd_display.lcd_clear()
        if self.state == SessionRecorderState.IDLE:
            lcd_display.lcd_display_string("Not Armed", 1)
            lcd_display.lcd_display_string("Metron. Off  " + "1/2", 2)
        elif self.state == SessionRecorderState.METRONOME_ON:
            lcd_display.lcd_display_string("Not Armed", 1)
            lcd_display.lcd_display_string("Metron. On   " + "1/2", 2)
        elif self.state == SessionRecorderState.ARMED:
            lcd_display.lcd_display_string("Armed " + str(metronome.current_beat), 1)
        elif self.state == SessionRecorderState.RECORDING:
            lcd_display.lcd_display_string("Recording " + str(metronome.current_beat), 1)
        elif self.state == SessionRecorderState.SAVING:
            lcd_display.lcd_display_string("Save Loop ?", 1)
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            lcd_display.lcd_display_string("PLAYER:", 1)
            lcd_display.lcd_display_string("2/2", 2)
        elif self.state == SessionRecorderState.PLAYER_SELECTION:
            lcd_display.lcd_display_string("Play from loop:", 1)
            if self.nb_of_loops == 0:
                lcd_display.lcd_display_string("No loop rec. yet", 2)
            else:
                lcd_display.lcd_display_string(str(self.selected_loop), 2)
        elif self.state == SessionRecorderState.PLAYER_ON:
            lcd_display.lcd_display_string("PLAYING ! :", 1)
    

    def on_focus(self):
        tab_manager.set_callback(self.end_tab_callback)
        self.nb_of_loops, tempo = tab_manager.load_tab_info(self.node_name)
        metronome.tempo = tempo
        self.selected_loop = self.nb_of_loops
        servo.set_callback_func(self.servo_callback)

    
    def servo_callback(self, index):
        if self.state == SessionRecorderState.ARMED:
            tab_manager.save_note(index, 0)
        elif self.state == SessionRecorderState.RECORDING:
            tab_manager.save_note(index, 1)
        

    def node_type(self):
        return "SessionRecorderItem"
        

class MenuHandler:  # This class will create the whole tree, and will be used to return the current_node.
    def __init__(self):
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
        self.metronome_node = FreePlayItem("freeplay_node", 0, level_2_2_size, "Metronome", self.practice_node)
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

        self.new_tab_node = TabCreatorItem("new_tab_node", 0, level_2_2_size, "New Tab", self.record_node)
        SessionRecorderItem("RS", 0, 1, "", self.new_tab_node, self.play_tab_node)
        self.existing_tab_node = BasicMenuItem("existing_tab_node", 1, level_2_2_size, "Existing Tabs", self.record_node)
        
        for i, file_name in enumerate(sorted(os.listdir(custom_tab_path))):   # Populating the list with all the files in the 'custom_tab_path' folder
            self.custom_tab_node_list.append(BasicMenuItem(str(file_name), i, len(os.listdir(custom_tab_path)), str(file_name), self.existing_tab_node))
            SessionRecorderItem(str(file_name), 0, 1, "", self.custom_tab_node_list[i], self.play_tab_node)

        self.current_node = self.play_tab_node
        self.update_display()
        self.set_inputs()

    def set_inputs(self):
        menu_btn_next_pin = 4               #
        menu_btn_previous_pin = 17          # Buttons to browse the menu
        menu_btn_validate_pin =27           #
        menu_btn_return_pin = 22            #

        menu_btn_next = Button(menu_btn_next_pin)
        menu_btn_next.when_pressed = lambda x: self.next()
        menu_btn_previous = Button(menu_btn_previous_pin)
        menu_btn_previous.when_pressed = lambda x: self.previous()
        menu_btn_execute = Button(menu_btn_validate_pin)
        menu_btn_execute.when_pressed = lambda x: self.execute()
        menu_btn_return = Button(menu_btn_return_pin)
        menu_btn_return.when_pressed = lambda x: self.back_in_menu()


    def get_current_node(self):
        return self.current_node

    def execute(self):
        previous_node = self.current_node
        self.current_node = self.current_node.execute()
        if not self.current_node is previous_node:
            self.current_node.on_focus()
        self.update_display()

    def back_in_menu(self):     
        previous_node = self.current_node
        self.current_node = self.current_node.back_in_menu()
        if not self.current_node is previous_node:
            self.current_node.on_focus()
        self.update_display()
    
    def next(self):
        previous_node = self.current_node
        self.current_node = self.current_node.next()
        if not self.current_node is previous_node:
            self.current_node.on_focus()
        self.update_display()

    def previous(self):
        previous_node = self.current_node
        self.current_node = self.current_node.previous()
        if not self.current_node is previous_node:
            self.current_node.on_focus()
        self.update_display()

    def update_display(self):
        self.current_node.update_display()

    def display_tree(self):
        for pre, fill, node in RenderTree(self.root_node):
            print("%s%s --> (%s)" % (pre, node.node_name, node.node_type()))