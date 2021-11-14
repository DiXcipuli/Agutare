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
        # is_root is defined in anytree
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
    
    def __init__(self, node_name, index, size, lcd_display, text_to_display, tab_manager, parent = None, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.tab_manager = tab_manager
        self.is_tab_playing = False

    def next(self):
        if not self.is_tab_playing:
            return super().next()
        else:
            return self

        
    def previous(self):
        if not self.is_tab_playing:
            return super().previous()
        else:
            return self


    def execute(self):
        if not self.is_tab_playing:
            self.update_display()
            # Get absolute path, and get if its a gpX or .agu file
            tab_absolute_path , is_agu_file = self.tab_manager.grab_tab_file_from_node_name(self.node_name)
            if is_agu_file: # If it is, we need to pass some info to the tab manager before playing it
                self.tab_manager.load_tab_info(tab_absolute_path)
            self.tab_manager.play_tab(tab_absolute_path, is_agu_file)
            self.is_tab_playing = True
        return self


    def cancel(self):
        if self.is_tab_playing:
            self.is_tab_playing = False
            self.tab_manager.clear_events()
            return self
        else:
            return self.parent
        

    def update_display(self):
        self.lcd_display.lcd_clear()
        if self.is_tab_playing:
            self.lcd_display.lcd_display_string("Playing", 1)
        else:
            super().update_display()


    def end_tab_callback(self):
        self.is_tab_playing = False
        self.update_display()

    
    def on_focus(self):
        self.tab_manager.set_callback(self.end_tab_callback)


    def node_type(self):
        return "TabPlayerNode"


class StringRoutineNode(BasicMenuNode): # Will trigger back and forth the specified servo, in order for the user to set it easily above the guitar string
    
    def __init__(self, node_name, index, size, lcd_display, text_to_display, servo_manager, parent = None, children = None):
        self.servo_manager = servo_manager
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.is_string_test_running = False
        self.servo_routine_sleep = 0.5


    def next(self):
        if not self.is_string_test_running:
            return super().next()
        else:
            return self

    def previous(self):
        if not self.is_string_test_running:
            return super().previous()
        else:
            return self

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
            self.lcd_display.lcd_display_string(str(self.index + 1) + "/6", 2)

    def node_type(self):
        return "StringRoutineNode"


class ServosPositionNode(BasicMenuNode): # Set all servos to either, Low, Mid or High (No use for it actually)
    
    def __init__(self, node_name, index, size, lcd_display, text_to_display, servo_manager, menu_sleeping_time, parent = None, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.servo_manager = servo_manager
        self.menu_sleeping_time = menu_sleeping_time

    def execute(self):
        if self.index == 0: # Servo to LOW position
            self.servo_manager.setAllServosLowPosition()
        elif self.index == 1:
            self.servo_manager.setAllServosMidPosition()
        elif self.index == 2:
            self.servo_manager.setAllServosHighPosition()

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
            tab_name = self.tab_manager.create_tab(self.metronome.tempo, self.metronome.beats_per_loop)
            self.lcd_display.lcd_clear()
            self.lcd_display.lcd_display_string(tab_name, 1)
            self.lcd_display.lcd_display_string("Created !", 2)
            time.sleep(self.menu_sleeping_time)
            self.children[0].node_name = str(tab_name)
            self.menu_manager.update_available_tabs()
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


class PwmEditorNode(BasicMenuNode):
    def __init__(self, node_name, index, size, lcd_display, text_to_display, servo_manager, parent=None, children=None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent=parent, children=children)
        self.servo_manager = servo_manager
        self.associated_string = self.parent.parent.index
        self.increment = 10
    
    def next(self):
        self.pwm_value += self.increment
        self.write_pwm_value()
        self.set_pwm_value()
        self.servo_manager.update_pwm_value(self.associated_string, self.index, self.pwm_value)
        return self

    def previous(self):
        self.pwm_value -= self.increment
        self.write_pwm_value()
        self.set_pwm_value()
        self.servo_manager.update_pwm_value(self.associated_string, self.index, self.pwm_value)
        return self


    def write_pwm_value(self):
        lines = []
        with open(self.servo_manager.pwm_file_path) as pwm_file:
            lines = pwm_file.readlines()
            new_line = lines[self.associated_string + self.servo_manager.pwm_comment_lines].split(',')
            new_line[self.index] = str(self.pwm_value)
            if '\n' not in new_line[2]:
                new_line[2] = new_line[2] + '\n'
            new_line = ','.join(new_line)
            lines[self.associated_string] = new_line

        with open(self.servo_manager.pwm_file_path, 'w') as pwm_file:
            pwm_file.writelines(lines)



    def on_focus(self):
        self.read_pwm_file()
        self.set_pwm_value()

    def set_pwm_value(self):
        if self.index in (0, 2):
            value_to_send = self.pwm_mid_value + self.pwm_value
        else:
            value_to_send = self.pwm_value

        self.servo_manager.set_servo_pwm(self.associated_string, value_to_send)


    def read_pwm_file(self):
        with open(self.servo_manager.pwm_file_path) as pwm_file:
            pwm_line = pwm_file.readlines()[self.associated_string + self.servo_manager.pwm_comment_lines].split(',')
            self.pwm_value = int(pwm_line[self.index])
            # We need to get the mid value, as Low and High are defined as a offset from mid
            self.pwm_mid_value = int(pwm_line[1])


    def update_display(self):
        self.lcd_display.lcd_clear()
        if self.index in (0,2):
            self.lcd_display.lcd_display_string("Offset from mid", 1)
            self.lcd_display.lcd_display_string(str(self.pwm_value), 2)
        else:
            self.lcd_display.lcd_display_string("Mid value", 1)
            self.lcd_display.lcd_display_string(str(self.pwm_value), 2)


    def node_type(self):
        return "PwmEditorNode"


class RecorderNode(BasicMenuNode):

    def __init__(self, node_name, index, size, lcd_display, text_to_display, metronome, servo_manager, tab_manager, parent, children = None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent, children)
        self.state = SessionRecorderState.IDLE
        self.metronome = metronome
        self.servo_manager = servo_manager
        self.tab_manager = tab_manager
        

    def next(self):
        return self


    def previous(self):
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
        elif self.state == SessionRecorderState.SAVING:
            self.tab_manager.save_loop(os.path.join(self.tab_manager.tabs_path, self.parent.node_name))
            self.state = SessionRecorderState.IDLE
            self.tab_manager.clear_events()
            self.tab_manager.clear_saved_notes()
        
        return self

    def cancel(self):
        if self.state == SessionRecorderState.IDLE:
            return self.parent
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
        
        if self.state in (SessionRecorderState.ARMED, SessionRecorderState.RECORDING, SessionRecorderState.SAVING):
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
        
    

    def on_focus(self):
        self.absolute_tab_path = self.tab_manager.grab_tab_file_from_node_name(self.parent.node_name)[0]
        tempo, beats, self.nb_of_loops = self.tab_manager.load_tab_info(self.absolute_tab_path)
        self.metronome.tempo = tempo
        self.metronome.beats_per_loop = beats
        self.servo_manager.set_callback_func(self.servo_callback)

    
    def servo_callback(self, index):
        if self.state == SessionRecorderState.ARMED:
            self.tab_manager.save_note(index, 0)
        elif self.state == SessionRecorderState.RECORDING:
            self.tab_manager.save_note(index, 1)
        

    def node_type(self):
        return "SessionRecorderNode"


class LoopPlayerNode(BasicMenuNode):
    def __init__(self, node_name, index, size, lcd_display, text_to_display, tab_manager, parent=None, children=None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent=parent, children=children)
        
        self.state = SessionRecorderState.PLAYER_SELECTION_START
        self.tab_manager = tab_manager

        self.nb_of_loops = 0
        self.start_at_loop = 0
        self.end_after_loop = 0

    
    def next(self):
        if self.state == SessionRecorderState.PLAYER_SELECTION_START:
            self.start_at_loop +=1
            if self.start_at_loop > self.nb_of_loops:
                self.start_at_loop = 1
        elif self.state == SessionRecorderState.PLAYER_SELECTION_END:
            self.end_after_loop +=1
            if self.end_after_loop > self.nb_of_loops:
                self.end_after_loop = self.start_at_loop

        return self


    def previous(self):
        if self.state == SessionRecorderState.PLAYER_SELECTION_START:
            self.start_at_loop -= 1
            if self.start_at_loop < 1:
                self.start_at_loop = self.nb_of_loops
        elif self.state == SessionRecorderState.PLAYER_SELECTION_END:
            self.end_after_loop -= 1
            if self.end_after_loop < self.start_at_loop:
                self.end_after_loop = self.nb_of_loops
        return self


    def execute(self):
        if self.state == SessionRecorderState.PLAYER_SELECTION_START:
            if self.nb_of_loops != 0:
                self.state = SessionRecorderState.PLAYER_SELECTION_END
        elif self.state == SessionRecorderState.PLAYER_SELECTION_END:
            if self.nb_of_loops != 0: 
                self.state = SessionRecorderState.PLAYER_ON
                self.tab_manager.play_tab(self.absolute_tab_path, True,  self.start_at_loop, self.end_after_loop)
        return self


    def cancel(self):
        if self.state == SessionRecorderState.PLAYER_ON:
            self.state = SessionRecorderState.PLAYER_SELECTION_START
            self.tab_manager.clear_events()
            return self
        elif self.state == SessionRecorderState.PLAYER_SELECTION_START:
            return self.parent
        elif self.state == SessionRecorderState.PLAYER_SELECTION_END:
            self.state = SessionRecorderState.PLAYER_SELECTION_START
            return self


    def on_focus(self):
        self.tab_manager.set_callback(self.end_tab_callback)
        self.absolute_tab_path = self.tab_manager.grab_tab_file_from_node_name(self.parent.node_name)[0]
        tempo, beats, self.nb_of_loops = self.tab_manager.load_tab_info(self.absolute_tab_path)
        self.start_at_loop = self.nb_of_loops
        self.end_after_loop = self.nb_of_loops

    def end_tab_callback(self):
        self.state = SessionRecorderState.PLAYER_SELECTION_END
        self.update_display()


    def update_display(self):
        self.lcd_display.lcd_clear()
        if self.state == SessionRecorderState.PLAYER_SELECTION_START:
            self.lcd_display.lcd_display_string("From:", 1)
            if self.nb_of_loops == 0:
                self.lcd_display.lcd_display_string("No loop rec. yet", 2)
            else:
                self.lcd_display.lcd_display_string(str(self.start_at_loop), 2)
        elif self.state == SessionRecorderState.PLAYER_SELECTION_END:
            self.lcd_display.lcd_display_string("From:       To:", 1)
            self.lcd_display.lcd_display_string(str(self.start_at_loop) + "    " + str(self.end_after_loop), 2)
        elif self.state == SessionRecorderState.PLAYER_ON:
            self.lcd_display.lcd_display_string("PLAYING !", 1)


class SessionNode(BasicMenuNode):
    def __init__(self, node_name, index, size, lcd_display, text_to_display, metronome, servo_manager, tab_manager, parent, pseudo_parent, children=None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent=parent, children=children)

        self.metronome = metronome
        self.servo_manager = servo_manager
        self.tab_manager = tab_manager
        self.pseudo_parent = pseudo_parent

        #define 3 children nodes
        self.recorder_node = RecorderNode("recorder", 0, 3, self.lcd_display, "Recorder", self.metronome, self.servo_manager, self.tab_manager, self)
        self.player_node = LoopPlayerNode("Player", 1, 3, self.lcd_display, "Player", self.tab_manager, self)
        #self.options_node = TabOptionNode("Option", 2, 3, self.lcd_display, "Options", self.tab_manager, self)

        self.node_list = ["Recorder", "Player", "Options"]
        self.cursor = 0


    def next(self):
        self.cursor += 1
        if self.cursor >= len(self.node_list):
            self.cursor = 0
        return self


    def previous(self):
        self.cursor -= 1
        if self.cursor < 0:
            self.cursor = len(self.node_list) - 1
        return self


    def execute(self):
        return self.children[self.cursor]


    def cancel(self):
        return self.pseudo_parent


    def update_display(self):
        self.lcd_display.lcd_clear()
        self.lcd_display.lcd_display_string(self.node_list[self.cursor], 1)
        self.lcd_display.lcd_display_string(str(self.cursor + 1) +"/" + str(len(self.node_list)), 2)




"""
class TabOptionNode(BasicMenuNode):
    def __init__(self, node_name, index, size, lcd_display, text_to_display, tab_manager, parent=None, children=None):
        super().__init__(node_name, index, size, lcd_display, text_to_display, parent=parent, children=children)
        self.tab_manager = tab_manager

        self.tempo_option = TempoOption("Change Tempo")

        self.cursor = 0


    def next(self):
        self.cursor += 1
        if self.cursor >= len(self.node_list):
            self.cursor = 0
        return self


    def previous(self):
        self.cursor -= 1
        if self.cursor < 0:
            self.cursor = len(self.node_list) - 1
        return self
        


    def update_display(self):
        self.lcd_display.lcd_clear()
        self.lcd_display.lcd_display_string()


    class TempoOption(BasicMenuNode):
        def __init__(self, text_to_display):
            self.text_to_display = text_to_display

"""


class MenuManager:

    def __init__(self, metronome, servo_manager, tab_manager):
        self.metronome = metronome
        self.servo_manager = servo_manager
        self.tab_manager = tab_manager

        self.lcd_display = I2C_LCD_driver.lcd() 
        self.menu_sleeping_time = 1.2 # The time needed to display some useful information


        self.root_node = BasicMenuNode("Root", 0, 1, self.lcd_display, "Root")    # Root node

        self.play_tab_node = BasicMenuNode("play_tab_node", 0, 5, self.lcd_display, "Play Tab", self.root_node)
        self.practice_node = BasicMenuNode("practice_node", 1, 5, self.lcd_display, "Practice", self.root_node)
        self.string_routine_node = BasicMenuNode("string_test_node", 2, 5, self.lcd_display, "String Routine", self.root_node)
        self.servo_pos_node = BasicMenuNode("motor_pos_node", 3, 5, self.lcd_display, "Servo Position", self.root_node)
        self.pwm_editor_node = BasicMenuNode("pwm_editor_node", 4, 5, self.lcd_display, "Change PWM value", self.root_node)


        self.free_play_node = FreePlayNode("freeplay_node", 0, 2, self.lcd_display, "Free Mode", self.metronome, self.practice_node)
        self.session_mode_node = BasicMenuNode("record_node", 1, 2, self.lcd_display, "Session Mode", self.practice_node)
        

        for i in range(0,6):
            StringRoutineNode("String " + str(i + 1), i, 6, self.lcd_display, "String " + str(i + 1), self.servo_manager, parent = self.string_routine_node)

        servo_text = ["Low", "Mid", "High"]
        for i in range(0,3):
            ServosPositionNode("Servos to " + servo_text[i], i, 3, self.lcd_display, "Servos to " + servo_text[i], self.servo_manager, self.menu_sleeping_time, self.servo_pos_node)


        self.new_tab_node = TabCreatorNode("new_tab_node", 0, 2, self.lcd_display, "New Tab", self.metronome, self.tab_manager, self.menu_sleeping_time, parent = self.session_mode_node, menu_manager = self)
        SessionNode("RS", 0, 1, self.lcd_display, "", self.metronome, self.servo_manager, self.tab_manager, self.new_tab_node, self.new_tab_node)
        self.existing_tab_node = BasicMenuNode("existing_tab_node", 1, 2, self.lcd_display, "Existing Tabs", self.session_mode_node)
        
        #PWM editor children
        for i in range(0,6):
            node = BasicMenuNode("pwm_editor_sub_node", i, 6, self.lcd_display, "String " + str(i + 1), self.pwm_editor_node)
            for j in range(0,3):
                if j == 0:
                    text_to_display = "LOW"
                elif j == 1:
                    text_to_display = "MID"
                elif j == 2:
                    text_to_display = "HIGH"

                sub_node = BasicMenuNode("pwm_editor_sub_node", j, 3, self.lcd_display, text_to_display, node)
                PwmEditorNode("PWM_value_editor", j, 3, self.lcd_display, text_to_display, self.servo_manager, sub_node)


        self.update_available_tabs()
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


    def update_available_tabs(self):

        # 1: Checking for all tab, either gpX or .agu, to be reachable in 'Playing Mode' -------------------------------------------
        all_available_tabs = self.tab_manager.get_available_tabs(check_mode = 1)

        # Remove all nodes under 'Playing node', in order to recreate them all, with eventually new ones.
        if len(self.play_tab_node.children) != 0:
            for child in self.play_tab_node.children:
                del child.children
            del self.play_tab_node.children
            self.play_tab_node.children = ()
        

        for index, file_name  in enumerate(sorted(all_available_tabs)): 
           TabPlayerNode(str(file_name), index, len(all_available_tabs), self.lcd_display, str(file_name), self.tab_manager, self.play_tab_node)
        # --------------------------------------------------------------------------------------------------------------------------

        # 2: Checking .agu tab, to be reachable in 'Record Mode' -------------------------------------------------------------------
        available_tabs = self.tab_manager.get_available_tabs(check_mode = 2)

        # Remove all nodes under 'Existing Tab node', in order to recreate them all, with eventually new ones.
        if len(self.existing_tab_node.children) != 0:
            for child in self.existing_tab_node.children:
                del child.children
            del self.existing_tab_node.children
            self.existing_tab_node.children = ()
        for i, file_name in enumerate(sorted(available_tabs)):   # Populating the list with all the files in the 'custom_tab_path' folder
            new_tab = BasicMenuNode(str(file_name), i, len(available_tabs), self.lcd_display, str(file_name), self.existing_tab_node)
            SessionNode(str(file_name), 0, 1, self.lcd_display, "", self.metronome, self.servo_manager, self.tab_manager, new_tab, self.existing_tab_node)


     

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
