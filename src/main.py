# Hybrid_Guitar Project
# Made by Antoine Agu (DiXcipuli@gmail.com)

import MenuHandler as mh                                                                                         
import actions
from RPi import GPIO
import os
from signal import pause

#--------------------------------------------------------------------------------------------------------
menu = mh.MenuHandler(custom_tab_path, tab_path)
# ---------------------------------------------------------------------------------------------------------

# PIN DEFINITION --------------------------------------------------------------------------------------
menu_btn_next = 4               #
menu_btn_previous = 17          # Buttons to browse the menu
menu_btn_validate =27           #
menu_btn_return = 22            #

btn_servo_1 = 13            #
btn_servo_2 = 19            #
btn_servo_3 = 26            # Buttons to trigger the servos
btn_servo_4 = 16            #
btn_servo_5 = 20            #
btn_servo_6 = 21            #
# -----------------------------------------------------------------------------------------------------

# GPIO SETUP ------------------------------------------------------------------------------------------
#GPIO.setmode(GPIO.BCM)
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


# GPIO CALLBACK ----------------------------------------------------------------------------------------------------
GPIO.add_event_detect(menu_btn_next, GPIO.FALLING, callback=lambda x:menu_btn_callback, bouncetime=300) #SEEMS TO DETECT RISING EDGE ALSO !
GPIO.add_event_detect(menu_btn_previous, GPIO.FALLING, callback=lambda x:menu_btn_callback, bouncetime=300) #SEEMS TO DETECT RISING EDGE ALSO !
GPIO.add_event_detect(menu_btn_validate, GPIO.FALLING , callback=lambda x:menu_btn_callback, bouncetime=300)
GPIO.add_event_detect(menu_btn_return, GPIO.FALLING , callback=lambda x:menu_btn_callback, bouncetime=300)

GPIO.add_event_detect(btn_servo_1, GPIO.FALLING, callback=lambda x: servo_btn_callback(0), bouncetime=150)
GPIO.add_event_detect(btn_servo_2, GPIO.FALLING, callback=lambda x: servo_btn_callback(1), bouncetime=150)
GPIO.add_event_detect(btn_servo_3, GPIO.FALLING, callback=lambda x: servo_btn_callback(2), bouncetime=150)
GPIO.add_event_detect(btn_servo_4, GPIO.FALLING, callback=lambda x: servo_btn_callback(3), bouncetime=150)
GPIO.add_event_detect(btn_servo_5, GPIO.FALLING, callback=lambda x: servo_btn_callback(4), bouncetime=150)
GPIO.add_event_detect(btn_servo_6, GPIO.FALLING, callback=lambda x: servo_btn_callback(5), bouncetime=150)
# ------------------------------------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------------------


#define functions which will be triggered on pin state changes
def menu_btn_callback(channel):
    if GPIO.input(channel) == 0:
        if channel == menu_btn_next:
            menu.next()
        elif channel == menu_btn_previous:
            menu.previous()
        elif channel == menu_btn_validate:
            menu.execute()
        elif channel == menu_btn_return:
            menu.back_in_menu()

        menu.update_display()

def servo_btn_callback(index):
    if not menu.welcome_state:
        if isinstance(menu.get_current_node(), mh.RecordSessionItem): 
            if menu.get_current_node().current_state == mh.RecordSessionState.RECORDING:
                menu.get_current_node().save_note(index)

    actions.trigger_servo(index)
    
def main():
    menu.display_welcome_msg()
    menu.display_tree()
    pause()
    
if __name__ == "__main__":
    main()
