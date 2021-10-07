# Aguitar Project
# Made by Antoine Agu (DiXcipuli@gmail.com, www.DiXcipuli.com)

import metronome as metro       # Manages the metronome
import servo_manager as sm      # Manages the servo motors
import tab_manager as tm        # Manages the tabs, creates them, populates them, plays them
import menu_manager as mm       # Manages the user inputs, browses through the menu, displays info

import signal
from RPi import GPIO

GPIO.setmode(GPIO.BCM)

tab_path = '/home/pi/Documents/Aguitare/Tabs/'                  # path to tabs that are finished, ready to be played
custom_tab_path = '/home/pi/Documents/Aguitare/CustomTabs/'     # path to tabs the user is working on, that will be edited and modified

    
def main():

    metronome = metro.Metronome()
    servo_manager = sm.ServoManager()
    tab_manager = tm.TabManager(servo_manager, tab_path, custom_tab_path)

    menu_manager = mm.MenuManager(metronome, servo_manager, tab_manager)
    
    menu_manager.display_tree()     # Shows the menu tree, useful to debug
    signal.pause()
    
if __name__ == "__main__":
    main()
