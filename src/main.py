# Hybrid_Guitar Project
# Made by Antoine Agu (DiXcipuli@gmail.com)

import MenuHandler as mh
                                                                                             
import guitarpro as pygp




from RPi import GPIO
import os
from signal import pause



# PIN DEFINITION --------------------------------------------------------------------------------------
menu_btn_next = 4               #
menu_btn_previous = 17           # Buttons to browse the menu
menu_btn_validate =27           #
menu_btn_return = 22            #

btn_servo_1 = 13            #
btn_servo_2 = 19            #
btn_servo_3 = 26            # Buttons to trigger the servos
btn_servo_4 = 16            #
btn_servo_5 = 20            #
btn_servo_6 = 21            #
btn_servo_list = [btn_servo_1, btn_servo_2, btn_servo_3, btn_servo_4, btn_servo_5, btn_servo_6]

buzzer_pin = 12             # I am using the PMW of the Raspberry, on the GPIO12, PMW channel 0
# -----------------------------------------------------------------------------------------------------
 

# BUZZER-METRONOME ------------------------------------------------------------------------------------
buzzer_freq = 440
buzzer_duration = 0.07      # In second, how long does the buzzer last for the metronome
# -----------------------------------------------------------------------------------------------------


# GPIO SETUP ------------------------------------------------------------------------------------------
# GPIO.setmode(GPIO.BCM)

GPIO.setup(menu_btn_next, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(menu_btn_previous, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(menu_btn_validate, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(menu_btn_return, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.setup(btn_servo_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Buttons to trigger servos
GPIO.setup(btn_servo_4, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_5, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #
GPIO.setup(btn_servo_6, GPIO.IN, pull_up_down=GPIO.PUD_UP)      #

# GPIO.setup(buzzer_pin, GPIO.OUT)                                # Buzzer pin set to PWM
# buzzer_pwm = GPIO.PWM(buzzer_pin, buzzer_freq)                  #
# -----------------------------------------------------------------------------------------------------


# TAB, metronome and Display information --------------------------------------------------------------------------------------
tab_path = '/home/pi/Documents/RobotizeGuitar/Tabs/'                # For tabs which wont be edited
custom_tab_path = '/home/pi/Documents/RobotizeGuitar/CustomTabs/'   # For own compositions, where measures and notes will be added
current_tab = None                  # Stores the current tab we are working on (pyguitarpro.Song object)
current_tab_name = None             # Stores the current tab name we are working on (string)

default_tempo = 120
new_tab_tempo = default_tempo
current_tempo = default_tempo
saved_tempo = default_tempo
tempo_interval = 5                  # When changing the tempo value, will go 5 by 5 instead of 1 by 1
default_tab_name = "tab_"           # It wont be able to set the desired tab name when creating one. 
extension_type = ".gp5"             # Could be also .gp3 .gp4 or .tg (for TuxGuitar)
 
events = []                         # Will store all the timer, one per note.

is_metronome_on = False 
is_string_test_running = False
is_tab_running = False
run_tab_at_startup = True
is_free_mode_on = False

   
#--------------------------------------------------------------------------------------------------------
menu = mh.MenuHandler(custom_tab_path, tab_path)
# ---------------------------------------------------------------------------------------------------------

#define functions which will be triggered on pin state changes
def menu_btn_callback(channel):
    if GPIO.input(channel) == 0:
        if channel == menu_btn_next:
            menu.next()
        else:
            menu.previous()

        menu.update_display()


def validate(channel):
    if GPIO.input(menu_btn_validate) == 0:
        menu.execute()
        menu.update_display()
    # global current_menu_index, cursor, is_string_test_running, run_tab_at_startup, current_node
    # global is_free_mode_on, previous_cursor

    # if GPIO.input(menu_btn_validate) == 0:
    #     print ("Validate")
    #     if not current_node.children: # If the current node has no children, it means some actions need to be executed ...
    #         if current_node.parent.name == main_menu[0]: # = PlayTab
    #             lcd_display.lcd_clear()
    #             lcd_display.lcd_display_string("Playing :", 1)
    #             lcd_display.lcd_display_string(tab_list[cursor], 2)
                
    #             playTab()
            
    #         elif current_node.name == practice_menu[0]: # = Free mode
    #             is_free_mode_on = True
    #             startMetronome()
    #             updateMenuDisplay()

    #         elif current_node.parent.name == main_menu[2]: # = Loop test String
    #             if not is_string_test_running:
    #                 is_string_test_running = True
    #                 testThread = threading.Thread(target=string_test_loop)
    #                 testThread.start()
    #                 lcd_display.lcd_clear()
    #                 lcd_display.lcd_display_string("Playing String " + str(cursor + 1), 1)

    #         elif current_node.parent.name == main_menu[3]: # = Set Motors to Position
    #             if cursor == 0:
    #                 setServoLowPosition()
    #             if cursor == 1:
    #                 setServoMidPosition()
    #             if cursor == 2:
    #                 setServoHighPosition()
                
    #             lcd_display.lcd_clear()
    #             lcd_display.lcd_display_string("Done !", 1)
    #             time.sleep(menu_sleeping_time)
    #             updateMenuDisplay()

    #         elif current_node == custom_tab_list_node: # Browsing for existing custom tab, but no file found under 'custom_tab_path'
    #             lcd_display.lcd_clear()
    #             lcd_display.lcd_display_string("No Tab Found !", 1)
    #             time.sleep(menu_sleeping_time)
    #             updateMenuDisplay()

    #         elif current_node.name == new_tab_menu:
    #             createTab(new_tab_tempo)
    #             lcd_display.lcd_clear()
    #             lcd_display.lcd_display_string("Tab Created !", 1)
    #             time.sleep(menu_sleeping_time)
    #             updateMenuTree() # Need to rescan the existing tab under 'custom_tab_folder'
    #             updateMenuDisplay()

            
    #     else:                         # ... otherwise we keep going deeper in the tree
    #         current_node = current_node.children[0]
    #         if current_node.name == new_tab_menu:
    #             startMetronome()
    #         previous_cursor = cursor #We store where we were in this menu, for later when we will press return
    #         cursor = 0
    #         updateMenuDisplay()
    


def back(channel):
    menu.back_in_menu()
    menu.update_display()
    # print('back')
    # global cursor, events, is_tab_running, is_string_test_running, current_node, new_tab_tempo
    # global is_metronome_on, is_free_mode_on, saved_tempo
    
    # new_tab_tempo = default_tempo

    # if is_tab_running : # We do not go back to the parent, we just stop the action, and re-display the current node
    #     is_tab_running = False
    #     # We cancel the Timer, to stop the triggering of servos
    #     for event in events:
    #         event.cancel()   
    #     events.clear()

    #     updateMenuDisplay()

    # elif is_string_test_running : # We do not go back to the parent, we just stop the action, and re-display the current node
    #     is_string_test_running = False
    #     updateMenuDisplay()

    # # We do not go back to the parent, we just stop the action, and re-display the current node
    # elif current_node.name == practice_menu[0] and is_metronome_on:
    #     is_free_mode_on = False
    #     is_metronome_on = False
    #     saved_tempo = current_tempo
    #     cursor = 0
    #     updateMenuDisplay()

    # elif current_node.name == record_session:
    #     current_node = record_mode_node
    #     cursor = 0
    
    # else:
    #     if not current_node.parent == top_menu_node: # Prevents from going out of the top node.
    #         if current_node.name == new_tab_menu:
    #             is_metronome_on = False
    #         current_node = current_node.parent # We go back to the parent in the menu tree
    #         #TO DO get the right index
    #         cursor = previous_cursor

    #     else: # If we are already at the top level menu, then it just gets back to the first option in the top menu
    #         current_node = top_menu_node.children[0]
    #         cursor = 0
            
    #     updateMenuDisplay()


# GPIO CALLBACK ----------------------------------------------------------------------------------------------------
GPIO.add_event_detect(menu_btn_next, GPIO.FALLING, callback=menu_btn_callback, bouncetime=300) #SEEMS TO DETECT RISING EDGE ALSO !
GPIO.add_event_detect(menu_btn_previous, GPIO.FALLING, callback=menu_btn_callback, bouncetime=300) #SEEMS TO DETECT RISING EDGE ALSO !
GPIO.add_event_detect(menu_btn_validate, GPIO.FALLING , callback=validate, bouncetime=300)
GPIO.add_event_detect(menu_btn_return, GPIO.FALLING , callback=back, bouncetime=300)

GPIO.add_event_detect(btn_servo_1, GPIO.FALLING, callback=lambda x: trigger_servo(0), bouncetime=150)
GPIO.add_event_detect(btn_servo_2, GPIO.FALLING, callback=lambda x: trigger_servo(1), bouncetime=150)
GPIO.add_event_detect(btn_servo_3, GPIO.FALLING, callback=lambda x: trigger_servo(2), bouncetime=150)
GPIO.add_event_detect(btn_servo_4, GPIO.FALLING, callback=lambda x: trigger_servo(3), bouncetime=150)
GPIO.add_event_detect(btn_servo_5, GPIO.FALLING, callback=lambda x: trigger_servo(4), bouncetime=150)
GPIO.add_event_detect(btn_servo_6, GPIO.FALLING, callback=lambda x: trigger_servo(5), bouncetime=150)
# ------------------------------------------------------------------------------------------------------------------

def updateMenuTree():
    global custom_tab_list
    custom_tab_list = []

    for file_name in os.listdir(custom_tab_path):
        custom_tab_list.append(str(file_name))
        Node(str(file_name), parent = custom_tab_list_node)


def main():
    #initialize()
    menu.display_welcome_msg()
    menu.display_tree()
    pause()
    

if __name__ == "__main__":
    main()
