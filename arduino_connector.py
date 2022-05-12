'''
these links for may 12:
http://www.mikeburdis.com/wp/notes/plotting-serial-port-data-using-python-and-matplotlib/
https://jakevdp.github.io/blog/2012/08/18/matplotlib-animation-tutorial/
https://matplotlib.org/2.0.2/examples/animation/simple_anim.html
https://www.youtube.com/watch?v=wEbGhYjn4QI
https://akumar34.github.io/data.html
https://dev.socrata.com/foundry/data.providenceri.gov/tisk-wsvu
'''




import serial
from process_image import *
from plot_data import *
import matplotlib.pyplot as plt
import pandas as pd
from rich_dataframe import prettify
import numpy
import time
import signal
import readchar
import sys


# about baudrate
# rate at which your Ardunio transmits data
# that way we know at what rate we can sample the incoming data
# look at the Arduino C code that already has a baudrate specified...


def connectToArduino(portVal: str, baudrate: int):
    global serialInst
    serialInst = serial.Serial()
    serialInst.baudrate = 9600
    serialInst.port = portVal
    serialInst.open() # listen any incoming data until user stops the data stream in the terminal



def writeToCSV(df: pd.DataFrame, filename: str):
    df.to_csv(f'{filename}.csv', index=False)


def handler(signum, frame):
    '''
    Reference:
    
    Adapted from this code
    https://code-maven.com/catch-control-c-in-python
    '''

    msg = '\nCtrl-c was pressed. Type q = quit; w = write to CSV, plot, then quit; c = continue.'
    print(msg, end='', flush=True)
    res = readchar.readchar()
    if res == 'q':
        print('')
        exit(1)
    elif res == 'c':
        print('', end='\r', flush=True)
        print(' ' * len(msg), end='', flush=True) # clear the printed line
        print('    ', end='\r', flush=True)
    elif res == 'w':
        writeToCSV(finalDF, 'output/tilt_results')
        results = pd.read_csv('output/tilt_results.csv')
        postProcessPlot(results)
        print('')
        summaryStats()
        print('Done.')
        exit(1)
    else:
        print('Invalid.')
        return


signal.signal(signal.SIGINT, handler)
finalDF = pd.DataFrame()


def updateLine(historyAxes, tiltHistory, currentImage):
    # [pointTuple[0] for pointTuple in tiltHistory]         # x = time
    # print([pointTuple[1] for pointTuple in tiltHistory])    # y = state
    # print(tiltHistory)

    historyAxes.plot([pointTuple[0] for pointTuple in tiltHistory], [pointTuple[1] for pointTuple in tiltHistory])
    plt.title(f'{currentImage}')
    plt.draw()
    plt.pause(0.01) # is necessary for the plot to update for some reason
    # plt.show()


def addPointToHistory(tiltHistory: list, state: int, initialTime: float, historyAxes, currentImage: str):
    currentTime = time.time() - initialTime
    tiltHistory.append((currentTime, state)) # append a tuple (time, state)
    updateLine(historyAxes, tiltHistory, currentImage)



def detectTilt(imgFolder: list, runRandom: bool):
# def detectTilt(imgFolder: list):
    '''
    next generation list:
    1) degree of tilt
    2) LED display
    3) train binary classifier (i.e. classification algorithm)
    4) associate image data with geotag/GPS coordinates
    '''


    stillTilted = False
    stillNoTilt = False
    tiltHistory = []                # history meaning a time-based graphs
    # historyPlot, = plt.plot([], [])
    # plt.xlim(0, 30)
    # plt.ylim(0, 2)
    historyAxes = plt.axes()
    # plt.show()
    initialTime = time.time()
    currentImage = ''
    newPothole = 'N/A'
    addPointToHistory(tiltHistory, 0, initialTime, historyAxes, currentImage)
    global finalDF


    while True:

        if serialInst.in_waiting: # data in the buffer
            
            # read incoming bytes from serial
            packet = serialInst.readline()
            
            # in order to read that out as a string from Arduino, we have to decode
            try:
                newState = packet.decode('utf').replace('\n', '') # returns b'\r\n'
                isTilted = (int(newState) == 1)
            except:
                # Arduino does not fire up clean...
                print(f'Bad initial package: {newState=}') # leftover line feed in the buffer
                continue
            # print(isTilted) # check this should be False until tilted...


            if isTilted and not stillTilted: # only processes only first time output is 1, meaning a tilt was detected
                print('Tilted. Now processing image...')

                if len(imgFolder) > 0:
                    currentImage = imgFolder[0]
                    currentImage = currentImage[4:]
                    print(f'Current image: {currentImage}')
                else:
                    print('No more images to validate Arduino data...')
                    return

                # this creates an event for square wave
                addPointToHistory(tiltHistory, 0, initialTime, historyAxes, currentImage)
                addPointToHistory(tiltHistory, 1, initialTime, historyAxes, currentImage)

                if not runRandom:
                    processImage(imgFolder)
                    # imgFolder.pop(0)
                else:
                    newPothole = randomMode(imgFolder)
                
                stillTilted = True
                stillNoTilt = False


            if not isTilted and not stillNoTilt:
                addPointToHistory(tiltHistory, 1, initialTime, historyAxes, currentImage)
                addPointToHistory(tiltHistory, 0, initialTime, historyAxes, currentImage)
                stillTilted = False
                stillNoTilt = True
                # currentImage = 'N/A'

            
            # dataframe capture
            # d = {'wasTilted': int(isTilted), 'imageFilename': currentImage, 'newPothole': newPothole[0]}
            # # imgFolder.pop(0)

            # tempDF = pd.DataFrame(d, index=[0])
            # finalDF = pd.concat([tempDF, finalDF])
            # prettify(finalDF)

            # # writes to a file each iteration
            # writeToCSV(finalDF, 'output/tilt_results')



if __name__ == '__main__':
    
    print('Starting program!')
    imgFolder = glob.glob('img/*.jpg') # a list
    port = '/dev/cu.usbmodem144101'
    baudrate = 9600

    '''
    args = a list with 1 thing in it
    position 0 of args = name of this program
    '''
    args = sys.argv[1:]
    if len(args) > 0 and args[0] == 'random': # random parameter to make it only run this if statement
        connectToArduino(port, baudrate)
        detectTilt(imgFolder, True)
        exit()


    connectToArduino(port, baudrate)
    detectTilt(imgFolder, False)