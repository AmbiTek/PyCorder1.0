# Records both screen and stereo mix. Includes a GUI and automatic stopper.
# In Version 1.9, change the sd.rec() to an output stream to capture.
import cv2 as cv
import numpy as np
import pyautogui
#import keyboard
from pydub import AudioSegment
from pydub.playback import play
import pyaudio
import wave
import moviepy.editor as mpe
import sounddevice as sd
from scipy.io.wavfile import write
from scipy.io import wavfile
from multiprocessing import Pool
from multiprocessing import Process, Pipe, Queue, freeze_support
import multiprocessing as mpr
from threading import Thread
import time
import datetime as dt
import os
import sys
import dill
from tkinter import *
from tkinter import ttk
# Modules for noise reduction
#import sox
#import noisereduce as nr

dill.dumps(Pipe)
dill.dumps(mpr)
#dill.dumps(keyboard)
y = 0
keys = []       
z = 0
x = 0
VERIFY = False
START_LOCK = True
FileOut_PATH = "TotalVideo.mp4"

timeRead = 0
elapsed = 0
tik = 0
frames = []
data = []
myrecording = []
fs = 44100  # Sample rate
seconds = 7260  # Duration of recording (7,260s)
sd.default.device = ["Stereo Mix", 1] # This allows you to record the computer's audio

# Second time keeper
class Clock:

    x = 0
    LOG = 0
    
    def __init__(self, start_time):
        self.start_time = start_time

    def begin(self):
        x = self.x
        while x == 0:
            time.sleep(1)
            LOG = setattr(self, "LOG", self.LOG + 1)
            #print(self.LOG) <- Used in testing

    def break_clock(self):
        x = setattr(self, "x", 1)

    def get_current_time(self):
        LOG = getattr(self, "LOG")
        return LOG


def KeepTime():
    print("Timer Began...")
    if __name__ == "__main__":
        t1 = Thread(target=Clock.begin, args=(Timer, ))
        t1.start()

Timer = Clock(0)

# Error handling
def Cancel_R():
    print("Oops. You forgot to press record :)")

def deviceR(conn2):
    global timeRead
    global elapsed
    global tik
    global myrecording
    global VERIFY2
    SUMMON = 1
    print("Recording")
    while True:
        """
        # DEBUGGING PURPOSES
        if keyboard.is_pressed('p'):
            SUMMON += 1
        if SUMMON == 1:
            KeepTime()
            SUMMON += 1
        if keyboard.is_pressed('l'):
            print(Timer.get_current_time())
            """
        
        # STOPS program from running KeepTime() multiple times, preventing creation of multiple threads!
        if SUMMON == 1:
            KeepTime()
            tik = time.perf_counter() # Is used for time keeping
            myrecording = sd.rec(int(seconds*fs), samplerate=fs, channels=2, dtype='int16')
            SUMMON += 1
        # Stops Recording manually
        global VERIFY
        if VERIFY == True:
            if SUMMON == 1:
                Cancel_R()
                continue
            sd.stop()  # Wait until recording is finished
            tok = time.perf_counter() # Used for time keeping
            elapsed = int(tok - tik) # Time took to record
            timeRead = elapsed + 1 # Offset to get full recording
            write('DeviceSound.wav', fs, myrecording)  # Save as WAVE file
            process_audio()
            break
        """
        TESTING: Variable can hold video data
        if keyboard.is_pressed('e'):
            data_check = myrecording[:]
            write('RecordingData.wav', fs, data_check)
            break
            """
        # Stops recording automatically
        if Timer.get_current_time() == 7260:
            sd.stop()
            Timer.break_clock()
            tok = time.perf_counter()
            elapsed = int(tok - tik) # Time took to record
            timeRead = elapsed + 1 # Offset to get full recording
            write('DeviceSound.wav', fs, myrecording)  # Save as MP3 file
            process_audio()
            break


def process_audio():
    global timeRead
    fN = "DeviceSound.wav"
    #This loop reads only what was recorded in the previous recording
    stream = wave.open(fN, "rb")
    for i in range(int((44100 / (1024 * 32)) * timeRead)):
        data = stream.readframes(1024 * 32)
        frame_data = np.array(data)
        frames.append(frame_data)
    stream.close()
    # save audio file
    # open the file in 'write bytes' mode
    wf = wave.open("Extracted.mp3", "wb")
    # set the channels
    wf.setnchannels(2)
    # set the sample width
    wf.setsampwidth(2)
    # set the sample rate
    wf.setframerate(44100)
    # write the frames as bytes
    wf.writeframes(b"".join(frames))
    # close the file
    wf.close()
    # Removes giant file
    if os.path.exists("DeviceSound.wav"):
        os.remove("DeviceSound.wav")
        print("Path deleted!")
    else:
        print("The file does not exist")


    


# PLAN B: Record frames into list. And process in an external function.
# screen record method
def record_thy_scrn(conn, cue):
    # display screen resolution, get it from your OS settings
    SCREEN_SIZE = (1920, 1080)
    # define the codec
    fourcc = cv.VideoWriter_fourcc(*"XVID")
    # create the video write object
    out = cv.VideoWriter("output.mkv", fourcc, 20.0, (SCREEN_SIZE))
    global y
    while True:
        # make a screenshot
        img = pyautogui.screenshot()
        # img = pyautogui.screenshot(region=(0, 0, 300, 400))
        # convert these pixels to a proper numpy array to work with OpenCV
        frame = np.array(img)
        # convert colors from BGR to RGB
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        # write the frame
        out.write(frame)
        if cue.empty() == False:
            conn.send([keys])
            cv.destroyAllWindows()
            out.release()
            cue.get_nowait()
            break 



def increase_var():
    global z
    z += 1
    print(z)
    

def release_video():
    global keys
    Thyme = dt.datetime.now()
    Sec = Thyme.second
    Min = Thyme.minute
    Hour = Thyme.hour
    Comb = str(Hour) + str(Min) + str(Sec) + ".mp4"
    FileOut_PATH = Comb
    m = mpe.VideoFileClip("output.mkv")
    s = mpe.AudioFileClip("Extracted.mp3")
    result = m.set_audio(s)
    result.write_videofile(FileOut_PATH)
    print("Started processing frame data...")
    os.remove("output.mkv")
    os.remove("Extracted.mp3")
    print("Count function proccessed.")


def CallBack(val = False):
    return val

q = Queue()
parent_conn, child_conn = Pipe(duplex=True)
sound_par, sound_chi = Pipe(duplex=True)
p1 = Process(target = record_thy_scrn, args = (child_conn, q))
p2 = Thread(target = deviceR, args = (sound_chi, ))
    
def MASTER_REC():
    global START_LOCK
    global p1
    if __name__ == "__main__":
        mpr.freeze_support()
        if START_LOCK == False:
            print("Can't start twice.")
        else:
            p1.start()
            p2.start()
            START_LOCK = False
            lbl["textvariable"] = stat
            stat.set("Now Recording.")
            print(CallBack(9 > 10))
            print("p1 process started.")
        
# Opens another window possibly due to reocrd_thy_screen() being started in
# a process. Creating a window of that process.
# EDIT: Nope, win.mainloop was causing the ruckus.
def MASTER_F():
    global x
    global p1
    global p2
    global VERIFY
    global START_LOCK
    if START_LOCK == False:
        VERIFY = CallBack(5<6)
        q.put("Stop now.")
        p1.join()
        p2.join()
        p1.terminate()
        print("p2 finished.")
        print("Did it!!!")
        print("y = " + str(y))
        increase_var()
        if z == 1:
            x = x + 1
            print("x was increased!")          
        if x == 1:
            release_video()
            x = x + 1
            lbl["textvariable"] = stat
            stat.set("Status: Done Recording!")
            START_LOCK = True
            
    
win = Tk()
win.title("PyCorder")
#win.geometry("1000x500")
win.resizable(FALSE, FALSE)
frame = ttk.Frame(win, width=500, height=250)
frame.grid(columnspan=3, rowspan=3)

# Status
stat = StringVar()
lbl = ttk.Label(win, text="Status: Not Recording...")
lbl.grid(column=1, row=0)
#lbl.pack()
#lbl.place(x=420, y=100)

# Start Button
B = Button(win, text="Start", command=MASTER_REC, width="10", height="1")
B.grid(column=0, row=1)
#B.pack()
#B.place(x=400, y=250)

# Stop Button
A = Button(win, text="Stop", command=MASTER_F, width="10", height="1")
A.grid(column=2, row=1)
#A.pack()
#A.place(x=500, y=250)

#win.mainloop()
