import serial
from process_image import *
import matplotlib.pyplot as plt
import pandas as pd
from rich_dataframe import prettify
import numpy
import time
import signal
import readchar
import sys


# set state for graph
plt.style.use('dark_background')


# about baudrate
# rate at which your Ardunio transmits data
# that way we know at what rate we can sample the incoming data
# look at the Arduino C code that already has a baudrate specified...


def connectToArduino(portVal: str, baudrate: int):
    global serialInst
    serialInst = serial.Serial()
    serialInst.baudrate = 9600
    serialInst.port = portVal
    serialInst.open()           # listens to any incoming data until user stops the data stream in the terminal



def writeToCSV(finalDF: pd.DataFrame, filename: str):
    # prettify(finalDF)
    finalDF.to_csv(f'{filename}.csv', index=False)


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
        print('')
        print('\nSummary stats below will all be 0 when not in random mode.\n')
        summaryStats()
        print('Done.')
        exit(1)
    else:
        print('Invalid.')
        return


signal.signal(signal.SIGINT, handler)
finalDF = pd.DataFrame()


def updateLine(historyAxes, tiltHistory, currentImage):
    historyAxes.plot([pointTuple[0] for pointTuple in tiltHistory], [pointTuple[1] for pointTuple in tiltHistory])
    plt.title(f'{currentImage}')
    plt.draw()
    plt.pause(0.01) # is necessary for the plot to update for some reason


def addPointToHistory(tiltHistory: list, state: int, initialTime: float, historyAxes, currentImage: str):
    currentTime = time.time() - initialTime
    tiltHistory.append((currentTime, state)) # append a tuple (time, state)
    updateLine(historyAxes, tiltHistory, currentImage)



def detectTilt(imgFolder: list, outputFile: str, runRandom: bool):
    stillTilted = False
    stillNoTilt = False
    tiltHistory = []                # history meaning a time-based graphs
    historyAxes = plt.axes()
    initialTime = time.time()
    currentImage = 'N/A'
    newPotholeBin = 'N/A'
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
                    newPotholeBin = newPothole[0] # first value in list returned
                
                stillTilted = True
                stillNoTilt = False
                d = {'wasTilted': int(isTilted), 'imageFilename': currentImage, 'newPothole': newPotholeBin}
                tempDF = pd.DataFrame(d, index=[0])
                finalDF = pd.concat([tempDF, finalDF])
                writeToCSV(finalDF, outputFile)


            if not isTilted and not stillNoTilt:
                addPointToHistory(tiltHistory, 1, initialTime, historyAxes, currentImage)
                addPointToHistory(tiltHistory, 0, initialTime, historyAxes, currentImage)
                stillTilted = False
                stillNoTilt = True
                currentImage = 'N/A'
                d = {'wasTilted': int(isTilted), 'imageFilename': currentImage, 'newPothole': newPotholeBin}
                tempDF = pd.DataFrame(d, index=[0])
                finalDF = pd.concat([tempDF, finalDF])
                writeToCSV(finalDF, outputFile)


if __name__ == '__main__':
    
    print('Starting program!')
    imgFolder = glob.glob('img/*.jpg') # a list
    port = '/dev/cu.usbmodem144101'
    baudrate = 9600
    outputFile = 'output/tilt_results'

    '''
    args = a list with 1 thing in it
    position 0 of args = name of this program
    '''
    args = sys.argv[1:]
    if len(args) > 0 and args[0] == 'random': # only runs this mode if random specified as 3rd command-line argument
        connectToArduino(port, baudrate)
        detectTilt(imgFolder, outputFile, True)
        exit()


    connectToArduino(port, baudrate)
    detectTilt(imgFolder, outputFile, False)
