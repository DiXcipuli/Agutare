# Aguitare Project V.1.0

This project tries to 'replace' the right hand of the guitarist, to allow him to play a second instrument simultaneously. The final purpose is to have a system which loads a tab, and acts as the right hand of the guitarist, triggering the servos and plucking the strings at the right time over the song.

The user can navigate the menu through a LCD screen, where he can choose among the different features presented below. Here is a [Youtube link](https://www.youtube.com/watch?v=UqwoRIKUd7I) showing the final result.

![presentation](/imgs/Aguitare_presentation.jpg)


## Features

For now, the software allows to:
- Import and play a tab (triggering the servos accordingly), in **.gp3**,**.gp4** or **.gp5** extension.
- Set and trigger a **metronome**, beeping through a piezo buzzer.
- Create new tabs, with a specific tempo and beats per bar, in a **custom tab format** explained below.
- Compose and save bars/loops on the fly 
- Replay any section of a tab (from A to B) in loop, in order to practice a specific section.
- Change the settings related to the servos, without touching the code   

## Software
### Installation

The only library on which the project relies on is the **pyguitarpro** lib, which allows to parse **gpX** files.
You can directly install it through **pip**:

```bash
pip3 install PyGuitarPro
```

## Hardware

### Material
* Rapsberry 3B +
* Adafruit PWM 16 channel PCA9685
* LCD with I2C communication
* 6 x 9G servo motors
* A bunch of push buttons (4 for navigating the menu, and 6 to trigger the servos)
* A 5V powerbank battery (With 3A max output in my case)

### Scheme
![wiring](/imgs/Aguitare_wiring.png)

## Usage

If you try to run the program, and play a tab, you ll probably encounter an error, saying: **"Can't create more thread"**. That's because for each note in the tab, a **threading.Timer** object will be created, and, by default, the raspberry wont handle creating hundreds or thousands of threads. But this can be changed, and the limit of maximum threads can be raised by changing the size of the stack. To change it temporarily:

```bash
ulimit -s 200
```
200 is a good value, and will probably be enough to play 'big' tabs, without having consequences on the system stability.
If you want to change those value permanently


To run the program:
```bash
python3 main.py
```
However, you might want to automatically run the program at start up. I encountered issues running it at startup with a services, as it seems not to load properly this file_name, and thus the ulimit stack value is the default one, which creates issues. The dirty solution for now is to add a line in the **~/.bashrc** which will execute it:

```bash
python3 main.py
```

## Custom tab format

When creating a new tab, it creates a folder with a default name (like tab_1) and it generates inside a **Meta.agu** file, which holds on the first two lines, the **tempo**, and the **number of beats** per bar. Then the next lines will hold the file name of each new bar you will record.

When you record and save a bar, it will create a Bar_X file, with X an id which will be incremented. If you save your first bar, it will create the file **Bar_1**. This file contains for each note two information: on which string the note is played, and at what time. The time is normalized between 0 and 1.

For example, given this melody:
![wiring](/imgs/Aguitare_example.png)

It would create such a file:

```
5,0.0
4,0.25
2,0.5
1,0.625
```
And finally, this **bar_1** would be appended and referenced in the **Meta.agu** file:

```
tempo, 120
beats, 4
bar_1
```

## Tab converter

To convert **gp3**,**gp4** or **gp5** tab to custom **Meta.agu** file (to create and append new bars to it for example, or to be able to play a specific section in loop), ou can use the **tab_converter** tool:

```bash
python3 tab_converter.py -i path/to/tab -o /path/to/output
```

# Adding your own features

The whole menu is built as a tree. Each feature is represented by a node (you can see the whole menu structure when running the program).
If you wanna add your own feature and add it in the existing menu, you just have to create a class that inherits from **BasicMenuNode**
and create an instance in the **MenuManager** class, and making it child of an existing node. Some nodes have no other purpose than just
going deeper into a sub menu. Those nods are represented by the **BasicMenuNode** class. All the other class have a specific purpose, like 
the tab player, the metronome, the recorder etc..

Here is a global representation of the current menu (may not be up to date):

![menu](/imgs/Aguitare_menu.png)