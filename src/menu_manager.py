from anytree import NodeMixin, RenderTree
import I2C_LCD_driver
import os
import threading
import time
import guitarpro as pygp
from threading import Timer
from enum_classes import TabCreatorState, SessionRecorderState
from gpiozero import Button

"""
The menu is based on 'anytree'. The class MenuManager will create the whole menu as a tree,
and each node is an instance of one of the classes below, all inherited from NodeMixin.
Some nodes/classes are very basic, like BasicMenuNode, whose purpose is just to navigate to another sub-menu
Other nodes are more complexe, and their purpose can be: creating tab, running the metronome etc..

If you want to create your own feature and add it in the existing menu, just create a new class, inherited from
BasicMenuNode, and then create an instance of it in the menu handler, and add it where you want in the tree

Four buttons are used to navigate in the menu:
    -> Next
    <- Previous
    x execute
    o cancel

"""



class BasicMenuNode(NodeMixin):

    def __init__(self, node_name, index, size, lcd_display, text_to_display , parent = None, children = None):
        self.node_name = node_name
        self.index = index          # index of the node: [0 -> nb of siblings]
        self.size = size            # number of siblings
        self.lcd_display = lcd_display
        self.text_to_display = text_to_display                  # text displayed on the LCD screen
        self.parent = parent
        self.pos_indication = str(self.index + 1) + " / " + str(self.size)      # helps the user to know where he is located in the menu
        if children:
            self.children = children


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


    def execute(self):
        if self.is_leaf:
            return self
        else:
            return self.children[0]


    def cancel(self):
        if self.parent.is_root:
            return self
        else:
            return self.parent


    def update_display(self):
        self.lcd_display.lcd_clear()
        self.lcd_display.lcd_display_string(self.text_to_display, 1) # LCD line 1 
        self.lcd_display.lcd_display_string(self.pos_indication, 2)  # LCD line 2


    def on_focus(self):
        pass


    def node_type(self):
        return "BasicMenuNode"


class TabPlayerNode(BasicMenuNode): # This class will load a tab, (either gp3, gp4, gp5 or agu format) and play it by triggering the servos
    
    def __init__(self, node_name, index, size, lcd_display, text_to_display, parent = None, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)


    def execute(self):
        if not self.is_tab_palying:
            self.update_display()
            self.playTab(self.tab_path + self.text_to_display)
        return self


    def cancel(self):
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
        return "TabPlayerNode"


class StringRoutineNode(BasicMenuNode): # Will trigger back and forth the specified servo, in order for the user to set it easily above the guitar string
    
    def __init__(self, node_name, index, size, lcd_display, text_to_display, servo_manager, parent = None, children = None):
        self.servo_manager = servo_manager
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.is_string_test_running = False
        self.servo_routine_sleep = 0.5


    def execute(self):
        if not self.is_string_test_running:
            self.is_string_test_running = True
            testThread = threading.Thread(target=self.string_test_loop)
            testThread.start()
        return self


    def cancel(self):
        if self.is_string_test_running:
            self.is_string_test_running = False
            return self
        else:
            return self.parent
            

    def string_test_loop(self):
        while self.is_string_test_running:
            self.servo_manager.trigger_servo(self.index)
            time.sleep(self.servo_routine_sleep)


    def update_display(self):
        self.lcd_display.lcd_clear()
        if self.is_string_test_running:
            self.lcd_display.lcd_display_string("String " + str(self.index + 1) + " playing", 1)
        else:
            self.lcd_display.lcd_display_string("String " + str(self.index + 1), 1)

    def node_type(self):
        return "StringRoutineNode"


class ServosPositionNode(BasicMenuNode): # Set all servos to either, Low, Mid or High (No use for it actually)
    
    def __init__(self, node_name, index, size, lcd_display, text_to_display, servo_manager, menu_sleeping_time, parent = None, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.servo_manager = servo_manager
        self.menu_sleeping_time = menu_sleeping_time

    def execute(self):
        if self.index == 0: # Servo to LOW position
            self.servo_manager.setServoLowPosition()
        elif self.index == 1:
            self.servo_manager.setServoMidPosition()
        elif self.index == 2:
            self.servo_manager.setServoHighPosition()

        self.lcd_display.lcd_clear()
        self.lcd_display.lcd_display_string("Set !", 1)
        time.sleep(self.menu_sleeping_time)
       
        return self   

    def node_type(self):
        return "ServosPositionNode"


class FreePlayNode(BasicMenuNode):

    def __init__(self, node_name, index, size, lcd_display, text_to_display, metronome, parent = None, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.metronome = metronome
        

    def next(self):
        if self.metronome.is_metronome_active:
            self.metronome.increase_tempo()
            return self
        else:
            return super().next()
        

    def previous(self):
        if self.metronome.is_metronome_active:
            self.metronome.decrease_tempo()
            return self
        else:
            return super().next()
        

    def execute(self):
        if not self.metronome.is_metronome_active:
            self.metronome.start_metronome()
        else:
            self.metronome.reset_tempo()
        return self


    def cancel(self):
        if self.metronome.is_metronome_active:
            self.metronome.stop_metronome()
            return self
        else:
            return self.parent

    def update_display(self):
        self.lcd_display.lcd_clear()
        self.lcd_display.lcd_display_string(self.text_to_display, 1)

        if self.metronome.is_metronome_active:
            self.lcd_display.lcd_display_string(str(self.metronome.tempo), 2)
        else:
            self.lcd_display.lcd_display_string(self.pos_indication, 2)


    def node_type(self):
        return "FreePlayNode"


class TabCreatorNode(BasicMenuNode):

    def __init__(self, node_name, index, size, lcd_display, text_to_display, metronome, tab_manager, menu_sleeping_time, menu_manager, parent = None, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.state = TabCreatorState.IDLE
        self.metronome = metronome
        self.tab_manager = tab_manager
        self.menu_sleeping_time = menu_sleeping_time
        self.menu_manager = menu_manager


    def next(self):
        if self.state == TabCreatorState.DEFINING_TEMPO:
            self.metronome.increase_tempo()
            return self
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.metronome.increase_beats_per_loop()
            return self
        else:
            return super().next()

        
    def previous(self):
        if self.state == TabCreatorState.DEFINING_TEMPO:
            self.metronome.decrease_tempo()
            return self
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.metronome.decrease_beats_per_loop()
            return self
        else:
            return super().next()
        

    def execute(self):
        if self.state == TabCreatorState.IDLE:
            self.state = TabCreatorState.DEFINING_TEMPO
            self.metronome.start_metronome()
        elif self.state == TabCreatorState.DEFINING_TEMPO:
            self.state = TabCreatorState.DEFINING_BEATS
            self.metronome.stop_metronome()
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.state = TabCreatorState.IDLE
            tab_name = self.tab_manager.createTab(self.metronome.tempo, self.metronome.beats_per_loop)
            self.lcd_display.lcd_clear()
            self.lcd_display.lcd_display_string(tab_name, 1)
            self.lcd_display.lcd_display_string("Created !", 2)
            time.sleep(self.menu_sleeping_time)
            self.children[0].node_name = str(tab_name)
            self.menu_manager.update_custom_tabs_list()
            return self.children[0]
        return self


    def cancel(self):
        if self.state == TabCreatorState.IDLE:
            return self.parent
        elif self.state == TabCreatorState.DEFINING_TEMPO:
            self.state = TabCreatorState.IDLE
            self.metronome.stop_metronome()
            return self
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.state = TabCreatorState.DEFINING_TEMPO
            self.metronome.start_metronome()
            return self


    def update_display(self):
        self.lcd_display.lcd_clear()
        
        if self.state == TabCreatorState.IDLE:
            self.lcd_display.lcd_display_string(self.text_to_display, 1)
            self.lcd_display.lcd_display_string(self.pos_indication, 2)
        elif self.state == TabCreatorState.DEFINING_TEMPO:
            self.lcd_display.lcd_display_string("Tempo?", 1)
            self.lcd_display.lcd_display_string(str(self.metronome.tempo), 2)
        elif self.state == TabCreatorState.DEFINING_BEATS:
            self.lcd_display.lcd_display_string("Beats in loop?", 1)
            self.lcd_display.lcd_display_string(str(self.metronome.beats_per_loop), 2)


    def node_type(self):
        return "TabCreatorNode"




class SessionRecorderNode(BasicMenuNode):

    def __init__(self, node_name, index, size, lcd_display, text_to_display, metronome, servo_manager, tab_manager, parent, pseudo_parent, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.bars_to_record = 1
        self.state = SessionRecorderState.IDLE
        self.pseudo_parent = pseudo_parent
        self.metronome = metronome
        self.servo_manager = servo_manager
        self.tab_manager = tab_manager
        
        self.nb_of_loops = 0
        self.selected_loop = 0


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
            self.selected_loop -= 1
            if self.selected_loop < 1:
                self.selected_loop = self.nb_of_loops

        return self


    def execute(self):
        if self.state == SessionRecorderState.IDLE:
            self.metronome.start_metronome(self.metronome_callback)
            self.state = SessionRecorderState.METRONOME_ON
        elif self.state == SessionRecorderState.METRONOME_ON:
            self.metronome.current_beat = 0 # Reset the beat
            self.state = SessionRecorderState.ARMED
        elif self.state == SessionRecorderState.ARMED:
            self.state = SessionRecorderState.IDLE
            self.tab_manager.clear_saved_notes()
            self.metronome.stop_metronome()
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            self.state = SessionRecorderState.PLAYER_SELECTION
        elif self.state == SessionRecorderState.PLAYER_SELECTION: 
            self.state = SessionRecorderState.PLAYER_ON
            self.tab_manager.play_tab(self.tab_manager.custom_tab_path + self.node_name, True,  self.selected_loop)
        elif self.state == SessionRecorderState.SAVING:
            self.tab_manager.saveLoop()
            self.nb_of_loops =  self.tab_manager.load_tab_info(self.node_name)[0]
            self. selected_loop = self.nb_of_loops
            self.state = SessionRecorderState.IDLE
            self.tab_manager.clear_events()
            self.tab_manager.clear_saved_notes()
        
        return self

    def cancel(self):
        if self.state == SessionRecorderState.IDLE:
            return self.pseudo_parent
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            self.state = SessionRecorderState.IDLE
            return self
        elif self.state == SessionRecorderState.METRONOME_ON:
            self.state = SessionRecorderState.IDLE
            self.metronome.stop_metronome()
            return self
        elif self.state == SessionRecorderState.ARMED:
            self.state = SessionRecorderState.IDLE
            self.metronome.stop_metronome()
            return self
        elif self.state == SessionRecorderState.RECORDING:
            self.tab_manager.clear_saved_notes()
            self.metronome.stop_metronome()
            self.state = SessionRecorderState.IDLE
            return self
        elif self.state == SessionRecorderState.SAVING:
            self.state = SessionRecorderState.IDLE
            self.tab_manager.clear_saved_notes()
            self.tab_manager.clear_events()
            #CLEAR EVENT LIST
            return self
        elif self.state == SessionRecorderState.PLAYER_ON:
            self.state = SessionRecorderState.PLAYER_IDLE
            self.tab_manager.clear_events()
            return self
        elif self.state == SessionRecorderState.PLAYER_SELECTION:
            self.state = SessionRecorderState.PLAYER_IDLE
            self.tab_manager.clear_events()
            return self


    def end_tab_callback(self):
        self.state = SessionRecorderState.PLAYER_IDLE
        self.update_display()


    def metronome_callback(self, overflow):
        print(self.metronome.current_beat)

        if overflow:
            if self.state == SessionRecorderState.ARMED:
                self.state = SessionRecorderState.RECORDING
                self.tab_manager.bar_starting_time = time.time()
            elif self.state == SessionRecorderState.RECORDING:
                self.tab_manager.process_loop()
                self.metronome.stop_metronome()
                self.state = SessionRecorderState.SAVING
                
        self.update_display()
    

    def update_display(self):
        self.lcd_display.lcd_clear()
        if self.state == SessionRecorderState.IDLE:
            self.lcd_display.lcd_display_string("Not Armed", 1)
            self.lcd_display.lcd_display_string("Metron. Off  " + "1/2", 2)
        elif self.state == SessionRecorderState.METRONOME_ON:
            self.lcd_display.lcd_display_string("Not Armed", 1)
            self.lcd_display.lcd_display_string("Metron. On   " + "1/2", 2)
        elif self.state == SessionRecorderState.ARMED:
            self.lcd_display.lcd_display_string("Armed " + str(self.metronome.current_beat), 1)
        elif self.state == SessionRecorderState.RECORDING:
            self.lcd_display.lcd_display_string("Recording " + str(self.metronome.current_beat), 1)
        elif self.state == SessionRecorderState.SAVING:
            self.lcd_display.lcd_display_string("Save Loop ?", 1)
        elif self.state == SessionRecorderState.PLAYER_IDLE:
            self.lcd_display.lcd_display_string("PLAYER:", 1)
            self.lcd_display.lcd_display_string("2/2", 2)
        elif self.state == SessionRecorderState.PLAYER_SELECTION:
            self.lcd_display.lcd_display_string("Play from loop:", 1)
            if self.nb_of_loops == 0:
                self.lcd_display.lcd_display_string("No loop rec. yet", 2)
            else:
                self.lcd_display.lcd_display_string(str(self.selected_loop), 2)
        elif self.state == SessionRecorderState.PLAYER_ON:
            self.lcd_display.lcd_display_string("PLAYING ! :", 1)
    

    def on_focus(self):
        self.tab_manager.set_callback(self.end_tab_callback)
        self.nb_of_loops, tempo = self.tab_manager.load_tab_info(self.node_name)
        self.metronome.tempo = tempo
        self.selected_loop = self.nb_of_loops
        self.servo_manager.set_callback_func(self.servo_callback)

    
    def servo_callback(self, index):
        if self.state == SessionRecorderState.ARMED:
            self.tab_manager.save_note(index, 0)
        elif self.state == SessionRecorderState.RECORDING:
            self.tab_manager.save_note(index, 1)
        

    def node_type(self):
        return "SessionRecorderNode"
        

class MenuManager:

    def __init__(self, metronome, servo_manager, tab_manager):
        self.metronome = metronome
        self.servo_manager = servo_manager
        self.tab_manager = tab_manager

        self.lcd_display = I2C_LCD_driver.lcd() 
        self.menu_sleeping_time = 1.2 # The time needed to display some useful information


        self.root_node = BasicMenuNode("Root", 0, 1, self.lcd_display, "Root")    # Root node

        self.play_tab_node = BasicMenuNode("play_tab_node", 0, 4, self.lcd_display, "Play Tab", self.root_node)
        self.practice_node = BasicMenuNode("practice_node", 1, 4, self.lcd_display, "Practice", self.root_node)
        self.string_routine_node = BasicMenuNode("string_test_node", 2, 4, self.lcd_display, "String test", self.root_node)
        self.servo_pos_node = BasicMenuNode("motor_pos_node", 3, 4, self.lcd_display, "Servo position", self.root_node)
        
        self.tab_node_list = []

        # Populating the list with all the files in the 'tab_path' folder
        for index, file_name  in enumerate(sorted(os.listdir(self.tab_manager.tab_path))): 
            self.tab_node_list.append(TabPlayerNode(str(file_name), index, len(os.listdir(self.tab_manager.tab_path)), self.lcd_display, str(file_name),  self.play_tab_node))


        self.free_play_node = FreePlayNode("freeplay_node", 0, 2, self.lcd_display, "Metronome", self.metronome, self.practice_node)
        self.record_node = BasicMenuNode("record_node", 1, 2, self.lcd_display, "Record", self.practice_node)
        

        for i in range(0,6):
            StringRoutineNode("String " + str(i + 1), i, 6, self.lcd_display, "String " + str(i + 1), self.servo_manager, parent = self.string_routine_node)

        servo_text = ["Low", "Mid", "High"]
        for i in range(0,3):
            ServosPositionNode("Servos to " + servo_text[i], i, 3, self.lcd_display, "Servos to " + servo_text[i], self.servo_manager, self.menu_sleeping_time, self.servo_pos_node)


        self.new_tab_node = TabCreatorNode("new_tab_node", 0, 2, self.lcd_display, "New Tab", self.metronome, self.tab_manager, self.menu_sleeping_time, parent = self.record_node, menu_manager = self)
        SessionRecorderNode("RS", 0, 1, self.lcd_display, "", self.metronome, self.servo_manager, self.tab_manager, self.new_tab_node, self.play_tab_node)
        self.existing_tab_node = BasicMenuNode("existing_tab_node", 1, 2, self.lcd_display, "Existing Tabs", self.record_node)
        

        self.update_custom_tabs_list()
        self.current_node = self.play_tab_node
        self.set_inputs()
        self.update_display()
        


    def set_inputs(self):
        btn_next = 4                #
        btn_previous = 17           #   Buttons to browse the menu
        btn_execute =27             #
        btn_cancel = 22             #

        Button(btn_next).when_pressed = lambda x: self.next()
        Button(btn_previous).when_pressed = lambda x: self.previous()
        Button(btn_execute).when_pressed = lambda x: self.execute()
        Button(btn_cancel).when_pressed = lambda x: self.cancel()


    def get_current_node(self):
        return self.current_node


    def update_custom_tabs_list(self):

        if len(self.existing_tab_node.children) != 0:
            for child in self.existing_tab_node.children:
                del child.children
            del self.existing_tab_node.children
            self.existing_tab_node.children = ()
        

        for i, file_name in enumerate(sorted(os.listdir(self.tab_manager.custom_tab_path))):   # Populating the list with all the files in the 'custom_tab_path' folder
            new_tab = BasicMenuNode(str(file_name), i, len(os.listdir(self.tab_manager.custom_tab_path)), self.lcd_display, str(file_name), self.existing_tab_node)
            SessionRecorderNode(str(file_name), 0, 1, self.lcd_display, "", self.metronome, self.servo_manager, self.tab_manager, new_tab, self.play_tab_node)

        self.display_tree()
    
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


    def execute(self):
        previous_node = self.current_node
        self.current_node = self.current_node.execute()
        if not self.current_node is previous_node:
            self.current_node.on_focus()
        self.update_display()


    def cancel(self):     
        previous_node = self.current_node
        self.current_node = self.current_node.cancel()
        if not self.current_node is previous_node:
            self.current_node.on_focus()
        self.update_display()
    

    def update_display(self):
        self.current_node.update_display()


    def display_tree(self):
        for pre, fill, node in RenderTree(self.root_node):
            print("%s%s --> (%s)" % (pre, node.node_name, node.node_type()))