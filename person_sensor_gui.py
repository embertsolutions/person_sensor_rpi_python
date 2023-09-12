from tkinter import *

import io
import fcntl
import struct
import time

# The person sensor has the I2C ID of hex 62, or decimal 98.
PERSON_SENSOR_I2C_ADDRESS = 0x62

# We will be reading raw bytes over I2C, and we'll need to decode them into
# data structures. These strings define the format used for the decoding, and
# are derived from the layouts defined in the developer guide.
PERSON_SENSOR_I2C_HEADER_FORMAT = "BBH"
PERSON_SENSOR_I2C_HEADER_BYTE_COUNT = struct.calcsize(
    PERSON_SENSOR_I2C_HEADER_FORMAT)

PERSON_SENSOR_FACE_FORMAT = "BBBBBBbB"
PERSON_SENSOR_FACE_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_FACE_FORMAT)

PERSON_SENSOR_FACE_MAX = 4
PERSON_SENSOR_RESULT_FORMAT = PERSON_SENSOR_I2C_HEADER_FORMAT + \
    "B" + PERSON_SENSOR_FACE_FORMAT * PERSON_SENSOR_FACE_MAX + "H"
PERSON_SENSOR_RESULT_BYTE_COUNT = struct.calcsize(PERSON_SENSOR_RESULT_FORMAT)

# I2C channel 1 is connected to the GPIO pins
I2C_CHANNEL = 1
I2C_PERIPHERAL = 0x703

# How long to pause between sensor polls. milliseconds
PERSON_SENSOR_DELAY = 200

MIN_IDENTIFICATION_PERCENTAGE = 90

BOARDER = 100
MAX_RANGE = 256
SCALE = 4

i2c_handle = io.open("/dev/i2c-" + str(I2C_CHANNEL), "rb+", buffering=0)
fcntl.ioctl(i2c_handle, I2C_PERIPHERAL, PERSON_SENSOR_I2C_ADDRESS)

i2c_handle.write(bytearray([0x01, 0x01]))
i2c_handle.write(bytearray([0x02, 0x01]))
i2c_handle.write(bytearray([0x05, 0x01]))

personnames = ["DaveH", "Richard", "Roger", "DaveF", "E", "F", "G", "H", "-1"]

# Range 0-7
personid = 0

root = Tk()
root.title('Person Sensor')
root.resizable(0,0)
root.wm_attributes("-topmost", 1)

canvas = Canvas(root, width=(MAX_RANGE*SCALE)+BOARDER, height=(MAX_RANGE*SCALE)+BOARDER, bd=0, highlightthickness=0)
canvas.pack()



labeltext = StringVar()
labeltext.set("Calibrate = {}".format(personnames[personid]))

label = Label(root, textvariable=labeltext)
label.pack()



def button1_press():
    print("Clear")
    i2c_handle.write(bytearray([0x06]))
    global personid
    global personnames
    personid = 0
    print("personid = {}".format(personid))
    labeltext.set("Calibrate = {}".format(personnames[personid]))

def button2_press():
    print("Decrement ID#")
    global personid
    global personnames
    personid -= 1
    if personid < 0:
        personid = 7
    print("personid = {}".format(personid))
    labeltext.set("Calibrate = {}".format(personnames[personid]))

def button3_press():
    global personid
    global personnames
    print("Calibrate ID# = {}".format(personid))
    i2c_handle.write(bytearray([0x04, personid]))
    personid += 1
    if personid > 7:
        personid = 0
    print("personid = {}".format(personid))
    labeltext.set("Calibrate = {}".format(personnames[personid]))

def button4_press():
    print("Increment ID#")
    global personid
    global personnames
    personid += 1
    if personid > 7:
        personid = 0
    print("personid = {}".format(personid))
    labeltext.set("Calibrate = {}".format(personnames[personid]))    

class Rectangles:
    def __init__(self, canvas, color):
        self.canvas = canvas

    def draw(self):
        self.canvas.after(PERSON_SENSOR_DELAY, self.draw)
        self.canvas.delete("all")

        self.canvas.create_rectangle((BOARDER/2),(BOARDER/2),(MAX_RANGE*SCALE)+(BOARDER/2),(MAX_RANGE*SCALE)+(BOARDER/2), outline='black', width=5)

        try:
            read_bytes = i2c_handle.read(PERSON_SENSOR_RESULT_BYTE_COUNT)
        except OSError as error:
            print("No person sensor data found")
            print(error)
            time.sleep(PERSON_SENSOR_DELAY)
            return
        offset = 0
        (pad1, pad2, payload_bytes) = struct.unpack_from(
            PERSON_SENSOR_I2C_HEADER_FORMAT, read_bytes, offset)
        offset = offset + PERSON_SENSOR_I2C_HEADER_BYTE_COUNT

        (num_faces) = struct.unpack_from("B", read_bytes, offset)
        num_faces = int(num_faces[0])
        offset = offset + 1

        faces = []
        for i in range(num_faces):
            (box_confidence, box_left, box_top, box_right, box_bottom, id_confidence, id,
             is_facing) = struct.unpack_from(PERSON_SENSOR_FACE_FORMAT, read_bytes, offset)
            offset = offset + PERSON_SENSOR_FACE_BYTE_COUNT
            face = {
                "box_confidence": box_confidence,
                "box_left": box_left,
                "box_top": box_top,
                "box_right": box_right,
                "box_bottom": box_bottom,
                "id_confidence": id_confidence,
                "id": id,
                "name": personnames[id],
                "is_facing": is_facing,
            }
            faces.append(face)
            outlinecolour = 'black'
            if is_facing == True:
                outlinecolour = 'red'
            self.canvas.create_rectangle(((MAX_RANGE-box_left)*SCALE)+(BOARDER/2),(box_top*SCALE)+(BOARDER/2),((MAX_RANGE-box_right)*SCALE)+(BOARDER/2),(box_bottom*SCALE)+(BOARDER/2), outline=outlinecolour, width=5)
            if (i == 0) and (id != -1) and (is_facing == True) and (id_confidence >= MIN_IDENTIFICATION_PERCENTAGE):
            #if (id != -1):
                rectanglelabel = personnames[id]+"("+str(id_confidence)+")"
            else:
                rectanglelabel = str(box_confidence)

            self.canvas.create_text(((((MAX_RANGE-box_left)-((box_right-box_left)/2))*SCALE)+(BOARDER/2),((box_top-((box_top-box_bottom)/2))*SCALE)+(BOARDER/2)), text=rectanglelabel)


        checksum = struct.unpack_from("H", read_bytes, offset)

        #print(time.time(), num_faces, faces)

btn = Button(root, text = 'Clear', bd = '5',
              command = button1_press, width=5*SCALE)
# Set the position of button on the top of window.  
btn.pack(side = 'left', expand=True) 


btn = Button(root, text = 'Decrement', bd = '5',
              command = button2_press, width=5*SCALE)
# Set the position of button on the top of window.  
btn.pack(side = 'left', expand=True) 

btn = Button(root, text = 'Calibrate', bd = '5',
              command = button3_press, width=5*SCALE)
# Set the position of button on the top of window.  
btn.pack(side = 'left', expand=True) 

btn = Button(root, text = 'Increment', bd = '5',
              command = button4_press, width=5*SCALE)
# Set the position of button on the top of window.  
btn.pack(side = 'left', expand=True) 

rectangles = Rectangles(canvas, "red")
rectangles.draw()

root.mainloop()