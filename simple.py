import RPi.GPIO as GPIO
import sys
import spidev
import time
from time import sleep
import Adafruit_DHT
from datetime import datetime
import requests
import json
from mfrc522 import SimpleMFRC522
import dht11
import I2C_LCD_driver
import threading
import requests
from flask import Flask, render_template
import sqlite3

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(21,GPIO.OUT)#dht11
GPIO.setup(24,GPIO.OUT) #LED, set GPIO 24 as output
GPIO.setup(18,GPIO.OUT) #buzzer, set GPIO 18 as output
buzzer_pwm = GPIO.PWM(18,100) #set 100Hz PWM output at GPIO 18 (buzzer)
#use PWM.start(1) to activate
GPIO.setup(23, GPIO.OUT) #dc motor
motor_pwm=GPIO.PWM(23,50) #motor pwm freq is 50hz
GPIO.setup(25,GPIO.OUT) #GPIO25 as Trig
GPIO.setup(27,GPIO.IN) #GPIO27 as Echo

token = "7149694600:AAHor-sOzlvoK31bEhiclzTbaA0ZZdVzQlc"
chat_id='6202818384'

reader = SimpleMFRC522()
auth_list = ['660319679370', '168851789560'] #put the content of tags into this list
#simulate the amount of credit in the card
#only for testing, should be removed in production
account = {
    "660319679370":50,
    "168851789560":2.3
    }

MATRIX=[[1,2,3],[4,5,6],[7,8,9],["*",0,"#"]]
ROW=[6,20,19,13]
COL=[12,5,16]
#set column pins as outputs
for i in range(3):
    GPIO.setup(COL[i],GPIO.OUT)
    GPIO.output(COL[i],1)
#set row pins as inputs, with pull up
for j in range(4):
    GPIO.setup(ROW[j],GPIO.IN,pull_up_down=GPIO.PUD_UP)

LCD = I2C_LCD_driver.lcd() #instantiate an lcd object, call it LCD
LCD.backlight(1)

product_dict ={
    "1":{
        "name":"Panadol with Optizorb Caplets",
        "price":7.9,
        "quantity":15
    },
    "2":{
        "name":"Hansaplast Plasters",
        "price":2.7,
        "quantity":14
    },
    "3":{
        "name":"Whisper Wings Pads",
        "price":6.2,
        "quantity":12
    }
}

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS products(id INTEGER UNIQUE, name TEXT, price , quantity)")
    data = [
        (1,"Panadol with Optizorb Caplets",7.9,15),
        (2,"Hansaplast Plasters",2.7,14),
        (3,"Whisper Wiings Pads",6.2,12)
    ]
    c.executemany("INSERT OR IGNORE INTO products VALUES(?,?,?,?)", data)
    c.execute('''
        CREATE TABLE IF NOT EXISTS temp_humi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            humi TEXT NOT NULL,
            temp TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def beep(dc,duration):
    buzzer_pwm.start(dc) #duty cycle (0.0 <= dc <= 100.0)
    sleep(duration) #in seconds
    buzzer_pwm.stop()
    
def dispense(dc,duration):
    #turn motor a certain way to dispense the product
    #m=20 or any number)
    #my_pwm.start(m)
    GPIO.output(23,1)
    sleep(duration)
    GPIO.output(23,0)
    
def ultrasound():
    #produce a 10us pulse at Trig
    GPIO.output(25,1) 
    time.sleep(0.00001)
    GPIO.output(25,0)
    #measure pulse width (i.e. time of flight) at Echo
    StartTime=time.time()
    StopTime=time.time()
    while GPIO.input(27)==0:
        StartTime=time.time() #capture start of high pulse       
    while GPIO.input(27)==1:
        StopTime=time.time() #capture end of high pulse
    ElapsedTime=StopTime-StartTime
    #compute distance in cm, from time of flight
    Distance=(ElapsedTime*34300)/2
       #distance=time*speed of ultrasound,
       #/2 because to & fro
    return Distance

def keypad():
    #scan keypad
    while (True):
        for i in range(3): #loop thru’ all columns
            GPIO.output(COL[i],0) #pull one column pin low
            for j in range(4): #check which row pin becomes low
                if GPIO.input(ROW[j])==0: #if a key is pressed
                    print (MATRIX[j][i]) #print the key pressed
                    key_pressed=MATRIX[j][i]
                    while GPIO.input(ROW[j])==0: #debounce
                        sleep(0.1)
                    return int(key_pressed)
            GPIO.output(COL[i],1) #write back default value of 1
            
def lcd(content,line,*offset):
    LCD.backlight(1) #turn backlight on 
    #LCD.lcd_display_string("LCD Display Test", 1) #write on line 1
    #LCD.lcd_display_string("Address = 0x27", 2, 2) #write on line 2
              #starting on 3rd column
    LCD.lcd_display_string(content, line,*offset)
    
def clear_lcd():
    LCD.lcd_clear()
    
def display_item_price(i):
    if str(i) in product_dict:
        print("display_item_price works. Key pressed: ",i," Product: ", product_dict[str(i)]["price"])
        return product_dict[str(i)]["price"]
    else:
        return -1
    
def display_item_price1(i):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    i = str(i)
    c.execute("SELECT COUNT (1) FROM products WHERE id = ?",i)
    res = c.fetchone()[0]
    c.execute("SELECT quantity FROM products WHERE id=?", i)   
    res2 = c.fetchone()[0]
    if res > 0 & res2 > 0:  
        c.execute("SELECT price FROM products WHERE id=?", i)   
        price = c.fetchall() 
        conn.close()
        print (price,"|",type(price))
        for e in price:
            p = float(e[0])
        return p
    else:
        conn.close()
        return -1

def change_item_count(i):
    product_dict[str(i)]["quantity"]-=1
    print("change_item_count works. New item quantity: ",product_dict[str(i)]["quantity"])
    return 0

def change_item_count1(i):
    conn = sqlite3.connect('database.db')
    #checks if product is inside database
    c = conn.cursor()
    i = str(i)
    c.execute("SELECT COUNT (1) FROM products WHERE id = ?",i)
    res = c.fetchone()[0]
    if res > 0:  
        q1 = c.execute("SELECT quantity FROM products WHERE id=?", i)
        old_quant = c.fetchall()
        for e in old_quant:
            old_q = int(e[0]) 
        new_q = old_q -1
        c.execute("UPDATE products SET quantity = ? WHERE id = ?", (new_q, i))
        conn.commit()
        conn.close()
        return (new_q)
    else:
        conn.close()
        return -1

def payment(i):
    while True:
        #print("Hold card near the reader to check if it is in the database")
        id = str(reader.read_id())
        beep(100,0.5)
        #f = open("authlist.txt", "r+")
        #if f.mode == "r+":
        #      auth=f.read()
        if id in auth_list: #if id in auth
              #number = auth.split('\n')
              #pos = number.index(id)
              #print("Card with UID", id, "found in database entry #", pos, "; access granted")
            res = product_dict[str(i)]["price"]
            if account[id] <= res:
                account[id]-= res
                print("Enough credit on ",id)
                return 0
            else:
                print("Not enough credit on ",id)
                return 1
        else:
              print("Card with UID ", id, " not found in database; access denied")
              return 1
          
def payment1(key_pressed):
    #make sure payment is made
    #read rfid card and deduct amount
    while True:
        #print("Hold card near the reader to check if it is in the database")
        id = str(reader.read_id())
        beep(100,0.5)
        #f = open("authlist.txt", "r+")
        #if f.mode == "r+":
        #      auth=f.read()
        if id in auth_list: #if id in auth
              #number = auth.split('\n')
              #pos = number.index(id)
              #print("Card with UID", id, "found in database entry #", pos, "; access granted")
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            res = c.execute("SELECT price FROM products WHERE id= ?",str(key_pressed))
            res = c.fetchall()
            conn.close
            for e in res:
                r=float(e[0])
            if account[id] <= r:
                account[id]-= r
                return 0
            else:
                return 1
        else:
              #print("Card with UID", id, "not found in database; access denied")
              return 1
          
def send_message(key):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    key = str(key)
    n = c.execute("SELECT id FROM products WHERE id = ?",key)
    q = c.execute("SELECT quantity FROM products WHERE id =?",key)
    num = c.fetchone()
    for i in num:
        numnum = int(i)
    conn.close
    t1 = datetime.now()
    t2 = t1.strftime('%Y-%m-%d %H:%M:%S')
    message = "A purchase was made on {} for item {}. New quantity: {}".format(t2, key, numnum)
    url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(token, chat_id,message)
    print(requests.get(url).json)
          
def website():
    app = Flask(__name__)
    @app.route('/')
    def website():
        return render_template('/home/pi/Desktop/IoTe/Training_Kit/Templates/index1.html')
    if __name__=='__main__':
        app.run(host = '172.23.45.86', port= 8080)

    
    
def vending_machine():
    #ultrasound detect for customer
    init_db()
    while True:
        distance=ultrasound()
    #lcd display welcome, keeps checking for customers
        if distance > 10:
            distance=ultrasound()
            lcd("Welcome!",1)
        else:
    #customer is detected
            print("Customer detected.")
            clear_lcd()
            lcd("Please select ",1)
            lcd("an item",2)
    #check what button is pressed
            key_pressed = keypad()
    #find the product coresponding to key_pressed
            price=display_item_price1(key_pressed)
            clear_lcd()
    #display price on lcd
            while price == -1:
                lcd("Item not",1)
                lcd("available",2)
                key_pressed = keypad()
                price=display_item_price1(key_pressed)
            clear_lcd()
            lcd("${:.2f}".format(price),1)
            lcd("Tap to pay",2)
    #transaction
            code=payment1(key_pressed)
            if code != 0:
                clear_lcd()
                lcd("Payment",1)              
                lcd("error",2)
            else:
                clear_lcd()
                lcd("Success",1)
    #change item count
                change_item_count1(key_pressed)
    #send telegram message
                #send_message(key_pressed)
    #LED lights up
                GPIO.output(24,1)
    #motor turns
                dispense(100,1)
    #LCD display successful
                clear_lcd()
                lcd("Thank you",1)
                send_message(key_pressed)
            GPIO.output(24,0)
            key_pressed=0
            clear_lcd()
            
while True:
    # create threads
    thread1 = threading.Thread(target=vending_machine)
    #thread2 = threading.Thread(target=read_moisture)
    thread3 = threading.Thread(target=website)

    # start threads
    thread1.start()
    #thread2.start()
    thread3.start()

    # wait for threads to finish
    thread1.join()
    #thread2.join()
    thread3.join()