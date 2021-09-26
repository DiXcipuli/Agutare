import Adafruit_PCA9685
from enum import Enum
from RPi import GPIO
from gpiozero import Button


class RecordingState(Enum):
    IDLE = 0
    PRE_RECORDING = 1
    RECORDING = 2


class Servo():
    

    def __init__(self) -> None:
        self.servo_low_position=[True, True, True, True, True, True]     # Keeps track of the 6 servos positions, LOW or HIGH

        self.callback = None
        
        self.pwm_16_channel_module = Adafruit_PCA9685.PCA9685()          # Instance which controls the 16-channels PWM module
        self.pwm_16_channel_module.set_pwm_freq(50)                      # Set to 50Hz

        self.SERVO_MID_POSITION = [275,285,295,295,295,285]              # 0-4096
        self.LOW_OFFSET_FROM_MID = [40, 40, 40, 40, 40, 40]
        self.HIGH_OFFSET_FROM_MID = [40, 40, 40, 40, 40, 40]

        btn_servo_1 = 13            #
        btn_servo_2 = 19            #
        btn_servo_3 = 26            # Buttons to trigger the servos
        btn_servo_4 = 16            #
        btn_servo_5 = 20            #
        btn_servo_6 = 21            #

        self.btn_array = [btn_servo_1, btn_servo_2, btn_servo_3 , btn_servo_4, btn_servo_5, btn_servo_6]

        btn_1 = Button(btn_servo_1)
        btn_1.when_pressed = lambda x: self.trigger_servo(0, self.callback)
        btn_2 = Button(btn_servo_2)
        btn_2.when_pressed = lambda x: self.trigger_servo(1, self.callback)
        btn_3 = Button(btn_servo_3)
        btn_3.when_pressed = lambda x: self.trigger_servo(2, self.callback)
        btn_4 = Button(btn_servo_4)
        btn_4.when_pressed = lambda x: self.trigger_servo(3, self.callback)
        btn_5 = Button(btn_servo_5)
        btn_5.when_pressed = lambda x: self.trigger_servo(4, self.callback)
        btn_6 = Button(btn_servo_6)
        btn_6.when_pressed = lambda x: self.trigger_servo(5, self.callback)


    def set_callback_func(self, func):
        self.callback = func


    def trigger_servo(self, index, func = None):

        if self.servo_low_position[index]:
            self.pwm_16_channel_module.set_pwm(index, 0, self.SERVO_MID_POSITION[index] + self.HIGH_OFFSET_FROM_MID[index])
            self.servo_low_position[index] = False
        else:
            self.pwm_16_channel_module.set_pwm(index, 0, self.SERVO_MID_POSITION[index] - self.LOW_OFFSET_FROM_MID[index])
            self.servo_low_position[index] = True

        if func != None:
            func(index)


    def setServoLowPosition(self):
        for i in range (0, 6):
            self.servo_low_position[i] = True
            self.pwm_16_channel_module.set_pwm(i, 0, self.SERVO_MID_POSITION[i] - self.LOW_OFFSET_FROM_MID[i])


    def setServoMidPosition(self):
        for i in range (0, 6):
            self.pwm_16_channel_module.set_pwm(i, 0, self.SERVO_MID_POSITION[i])


    def setServoHighPosition(self):
        for i in range (0, 6):
            self.servo_low_position[i] = False
            self.pwm_16_channel_module.set_pwm(i, 0, self.SERVO_MID_POSITION[i]  + self.HIGH_OFFSET_FROM_MID[i])


servo = Servo()