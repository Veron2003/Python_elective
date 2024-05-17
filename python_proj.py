import RPi.GPIO as GPIO
import sys
from time import *
import requests
import json
from mfrc522 import SimpleMFRC522
import I2C_LCD_driver
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(x, GPIO.OUT) #control for dc motor
my_pwm=GPIO.PWM(x,50) #pwm freq is 50hz

#matrix,row and col are for keypad
matrix=[[1,2,3],[4,5,6],[7,8,9],["A",0,"B"]]
row=[13,21,20,26]
col=[19,6,16]
for i in range(3):
    GPIO.setup(COL[i],GPIO.OUT)
    GPIO.output(COL[i],1)

for j in range(4):
    GPIO.setup(row[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)


def normal():
    #led display 'Welcome' and 'Select the product'
    #camera take photo
    #temperature and humidity sensor take readings


def select_product():
    #led display the price of products selected
    #if product that is not available is selected, display not availale
    
def payment():
    #make sure payment is made
    #read rfid card asnd deduct amount that is stored on a remote site


def dispense():
    #turn motor a certain way to dispense the product
    #m=20 or any number)
    #my_pwm.start(m)

def send_data():
    #send data to webpage or app
    
