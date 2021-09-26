# Hybrid_Guitar Project
# Made by Antoine Agu (DiXcipuli@gmail.com)

import menu_handler as mh                                                                                         
import signal


menu = mh.MenuHandler()

    
def main():
    menu.display_tree()
    signal.pause()
    
if __name__ == "__main__":
    main()
