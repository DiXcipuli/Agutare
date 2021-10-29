# Aguitare Project
# Made by Antoine Agu (DiXcipuli@gmail.com, www.DiXcipuli.com)

import metronome as metro       # Manages the metronome
import servo_manager as sm      # Manages the servo motors
import tab_manager as tm        # Manages the tabs, creates them, populates them, plays them
import menu_manager as mm       # Manages the user inputs, browses through the menu, displays info

import signal
from RPi import GPIO

GPIO.setmode(GPIO.BCM)

tabs_path = '/home/pi/Documents/Aguitare/tabs/'

    
def main():

    metronome = metro.Metronome()
    servo_manager = sm.ServoManager()
    tab_manager = tm.TabManager(servo_manager, tabs_path)

    menu_manager = mm.MenuManager(metronome, servo_manager, tab_manager)
    
    menu_manager.display_tree()     # Shows the menu tree, useful to debug
    signal.pause()
    
if __name__ == "__main__":
    main()
