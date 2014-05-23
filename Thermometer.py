WHITE = 1
BLACK = 0

import sys
import os
sys.path.append('/home/pi/gratis/PlatformWithOS/demo')
from EPD import EPD
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import MCP9808
import threading
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot
import numpy
import random
import datetime
import matplotlib.dates as mdates

def fig2data ( fig ):
    """
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    # draw the renderer
    fig.canvas.draw ( )
 
    # Get the RGBA buffer from the figure
    w,h = fig.canvas.get_width_height()
    buf = numpy.fromstring ( fig.canvas.tostring_argb(), dtype=numpy.uint8 )
    buf.shape = ( w, h,4 )
 
    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = numpy.roll ( buf, 3, axis = 2 )
    return buf

def fig2img ( fig ):
    """
    @brief Convert a Matplotlib figure to a PIL Image in RGBA format and return it
    @param fig a matplotlib figure
    @return a Python Imaging Library ( PIL ) image
    """
    # put the figure pixmap into a numpy array
    buf = fig2data ( fig )
    w, h, d = buf.shape
    return Image.fromstring( "RGBA", ( w ,h ), buf.tostring( ) )

dates = numpy.array([])
rollingTemperatures = numpy.zeros(shape=(12))
temperatures = numpy.array([])
updateCounter = 0
fullRefreshCounter = 5
lineSetup = False

font = ImageFont.truetype("/home/pi/Quicksand-Bold.otf", 30)
font2 = ImageFont.truetype("/home/pi/Quicksand-Bold.otf", 15)
epd = EPD()

figure = 0
ax = 0

if (os.path.isfile("dates.npy")):
    dates = numpy.load("dates.npy")
if (os.path.isfile("temperatures.npy")):
    temperatures = numpy.load("temperatures.npy")

def setupFigure():
    global figure, ax
    figure = matplotlib.pyplot.figure(frameon=False, figsize=(3.3,2.2), facecolor='white')
    ax = figure.add_axes([0.13, 0, 0.87, 0.8])
    ax.axis('on', antialiased=False)
    ax.xaxis.set_ticks_position('top')
    ax.xaxis.grid(True)
    ax.yaxis.grid(True)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)

    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)

    ax.xaxis_date()
    figure.autofmt_xdate(ha='right', rotation=-30)

    for tick in ax.xaxis.get_major_ticks():
        tick.tick1On = tick.tick2On = False
    for tick in ax.yaxis.get_major_ticks():
        tick.tick1On = tick.tick2On = False

def drawGraph():
    global figure, ax, lineSetup, dates
    matplotlib.pyplot.rc('font', weight='bold')

    line, = ax.plot(dates, temperatures, color='k')
    line.set_antialiased(False)

    annotation = ax.annotate("{:.2f}°C".format(temperatures[-1]), xy=(dates[-1], temperatures[-1]), xytext=(0, 2), textcoords='offset points', horizontalalignment='right', verticalalignment='bottom')

    if not lineSetup:
        gridlinesX = ax.xaxis.get_gridlines()
        [gridline.set_antialiased(False) for gridline in gridlinesX]
        gridlinesY = ax.yaxis.get_gridlines()
        [gridline.set_antialiased(False) for gridline in gridlinesY]
        lineSetup = True

    baseImage = Image.new('RGBA', epd.size, (255,255,255,255))

    immm = fig2img(figure)
    newImage = Image.alpha_composite(baseImage, immm)

    newImage.save("screen.png")

    epd.display(newImage.convert("1", dither=Image.FLOYDSTEINBERG))
    annotation.remove()

def update():
    global temperatures, dates, updateCounter, rollingTemperatures, fullRefreshCounter

    currentSensorValue = MCP9808.readTemperature()
    rollingTemperatures[updateCounter] = currentSensorValue

    updateCounter += 1
    
    if (updateCounter >= 12):
        fullRefreshCounter -= 1
        average = rollingTemperatures.sum() / 12
        print("Average: {:f}".format(average))
        temperatures = numpy.append(temperatures, average)

        currentDateTime = datetime.datetime.now()
        dates = numpy.append(dates, currentDateTime)

        drawGraph()

        if (fullRefreshCounter <= 0):
            epd.update()
            fullRefreshCounter = 5
            numpy.save("dates", dates)
            numpy.save("temperatures", temperatures)
        else:
            epd.partial_update()
        updateCounter = 0
    threading.Timer(5, update).start()

setupFigure()
drawGraph()
epd.update()
update()
