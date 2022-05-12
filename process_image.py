import cv2 as cv2 # pip install opencv-python
import glob
import random
import pprint

'''
pothole dataset from Kaggle:
https://www.kaggle.com/datasets/sachinpatel21/pothole-image-dataset?resource=download


data description:
A zipped folder containing 600+ .jpg images of the Road with Potholes.
These images are web scrapped from google, it might have some noisy or duplicate images.
'''



def processImage(imgFolder: list):
    '''
    program called this function when arduino tilted
    so this function will take in first image from a sequential list
    then discard it
    so we simulate the idea of cycling through new incoming data
    '''

    print('Processed!')
    imgFolder.pop(0)    # discard that from list



def assignBinaryValues(imgFolder) ->dict:
    '''
    takes in a list of images
    assigns 0 or 1's randomly to all pothole pictures
    stashes away these key-value pairs

    notes:
    random() gives a value between 0 or 1
    round() rounds that value up or down to either 0 or 1
    '''

    imgDict = dict()
    for img in imgFolder:
        # if img not in imgDict:
        filename = img[4:]
        imgDict[filename] = round(random.random())
    # pprint.pprint(imgDict)
    return imgDict



totalNewPotholes = 0
totalPotholes = 0
def summaryStats():
    print(f'{totalNewPotholes=}')
    print(f'{totalPotholes=}')


def randomMode(imgFolder):
    '''
    takes in list of images
    if tilt detector detects one that was a 0,
    then it tags it & updates value at that key to 1 & writes it to a file
    '''

    imgDict = assignBinaryValues(imgFolder)

    # for img in imgFolder:
    #     filename = img[4:]
    #     if imgDict[filename] == 1:

    image = imgFolder[0]
    filename = image[4:]
    newPothole = 0          # binary value
    global totalNewPotholes
    global totalPotholes

    if imgDict[filename] == 1:
        print(f'\n{imgDict[filename]}: matched a current record!\n')
    else:
        print(f'\n{imgDict[filename]}: new pothole detected!\n')
        newPothole = 1
        totalNewPotholes += 1

    totalPotholes += 1
    
    # discard from list & dictionary
    imgFolder.pop(0)
    imgDict.pop(filename, None)

    return [newPothole, totalNewPotholes, totalPotholes]



if __name__ == '__main__':

    imgFolder = glob.glob('img/*.jpeg')
    # processImage(imgFolder)
    randomMode(imgFolder)