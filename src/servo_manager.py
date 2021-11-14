import Adafruit_PCA9685
from gpiozero import Button
import os


class ServoManager():

    def __init__(self, pwm_file_path):
        self.pwm_file_path = pwm_file_path
        self.servo_low_position=[True, True, True, True, True, True]     # Keeps track of the 6 servos positions, LOW or HIGH

        self.callback = None    # Function to call when one servo is triggered (used when recording)
        
        self.pwm_16_channel_module = Adafruit_PCA9685.PCA9685()          # Instance which controls the 16-channels PWM module
        self.pwm_16_channel_module.set_pwm_freq(50)                      # Set to 50Hz

        # Those are some default values, but will be overwritten when loading the pwm_file
        self.servo_mid_position_array = [275,285,295,295,295,285]            
        self.servo_low_position_offset_array = [40, 40, 40, 40, 40, 40]
        self.servo_high_position_offset_array = [40, 40, 40, 40, 40, 40]
        
        # Number of comment lines in the pwm file
        self.pwm_comment_lines = 0

        self.load_pwm_value_from_file()
    
        btn_servo_1 = 21            #
        btn_servo_2 = 20            #
        btn_servo_3 = 16            # Buttons to trigger the servos
        btn_servo_4 = 26            #
        btn_servo_5 = 19            #
        btn_servo_6 = 13            #

        Button(btn_servo_1).when_pressed = lambda x: self.trigger_servo(0, self.callback)
        Button(btn_servo_2).when_pressed = lambda x: self.trigger_servo(1, self.callback)
        Button(btn_servo_3).when_pressed = lambda x: self.trigger_servo(2, self.callback)
        Button(btn_servo_4).when_pressed = lambda x: self.trigger_servo(3, self.callback)
        Button(btn_servo_5).when_pressed = lambda x: self.trigger_servo(4, self.callback)
        Button(btn_servo_6).when_pressed = lambda x: self.trigger_servo(5, self.callback)


    def load_pwm_value_from_file(self):
        if os.path.exists(self.pwm_file_path):
            with open(self.pwm_file_path) as pwm_file:
                lines = pwm_file.readlines()[self.pwm_comment_lines:]

            for i, line in enumerate(lines):
                line = line.split(',')
                for j, value in enumerate(line):
                    if j == 0:
                        self.servo_low_position_offset_array[i] = int(value)
                    elif j == 1:
                        self.servo_mid_position_array[i] = int(value)
                    elif i == 2:
                        self.servo_high_position_offset_array[i] = int(value)

    def update_pwm_value(self, string, mode, value):
        if mode == 0:
            self.servo_low_position_offset_array[string] = int(value)
        elif mode == 1:
            self.servo_mid_position_array[string] = int(value)
        elif string == 2:
            self.servo_high_position_offset_array[string] = int(value)


    def set_callback_func(self, func):
        self.callback = func


    def trigger_servo(self, index, func = None):
        if self.servo_low_position[index]:
            self.pwm_16_channel_module.set_pwm(index, 0, self.servo_mid_position_array[index] + self.servo_high_position_offset_array[index])
            self.servo_low_position[index] = False
        else:
            self.pwm_16_channel_module.set_pwm(index, 0, self.servo_mid_position_array[index] + self.servo_low_position_offset_array[index])
            self.servo_low_position[index] = True

        if func != None:
            func(index)


    def setAllServosLowPosition(self):
        for i in range (0, 6):
            self.servo_low_position[i] = True
            self.pwm_16_channel_module.set_pwm(i, 0, self.servo_mid_position_array[i] + self.servo_low_position_offset_array[i])


    def setAllServosMidPosition(self):
        for i in range (0, 6):
            self.pwm_16_channel_module.set_pwm(i, 0, self.servo_mid_position_array[i])


    def setAllServosHighPosition(self):
        for i in range (0, 6):
            self.servo_low_position[i] = False
            self.pwm_16_channel_module.set_pwm(i, 0, self.servo_mid_position_array[i]  + self.servo_high_position_offset_array[i])


    #string [0-5], value is between 0-4096
    def set_servo_pwm(self, string, value):
        self.pwm_16_channel_module.set_pwm(string, 0, value)
