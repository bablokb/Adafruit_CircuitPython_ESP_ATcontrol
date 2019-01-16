"""
This example will access an API, grab a number like hackaday skulls, github
stars, price of bitcoin, twitter followers... if you can find something that
spits out JSON data, we can display it!
"""
import gc
import time
import board
import busio
from digitalio import DigitalInOut
import adafruit_espatcontrol
import adafruit_espatcontrol_requests as requests
from adafruit_ht16k33 import segments
import neopixel

# Get wifi details and more from a settings.py file
try:
    from settings import settings
except ImportError:
    print("WiFi settings are kept in settings.py, please add them there!")
    raise

#              CONFIGURATION
PLAY_SOUND_ON_CHANGE = False
NEOPIXELS_ON_CHANGE = False
TIME_BETWEEN_QUERY = 60  # in seconds

# Some data sources and JSON locations to try out

# Bitcoin value in USD
DATA_SOURCE = "http://api.coindesk.com/v1/bpi/currentprice.json"
DATA_LOCATION = ["bpi", "USD", "rate_float"]

# Github stars! You can query 1ce a minute without an API key token
#DATA_SOURCE = "https://api.github.com/repos/adafruit/circuitpython"
#if 'github_token' in settings:
#    DATA_SOURCE += "?access_token="+settings['github_token']
#DATA_LOCATION = ["stargazers_count"]

# Youtube stats
#CHANNEL_ID = "UCpOlOeQjj7EsVnDh3zuCgsA" # this isn't a secret but you have to look it up
#DATA_SOURCE = "https://www.googleapis.com/youtube/v3/channels/?part=statistics&id=" \
#              + CHANNEL_ID +"&key="+settings['youtube_token']
# try also 'viewCount' or 'videoCount
#DATA_LOCATION = ["items", 0, "statistics", "subscriberCount"]


# Subreddit subscribers
#DATA_SOURCE = "https://www.reddit.com/r/circuitpython/about.json"
#DATA_LOCATION = ["data", "subscribers"]

# Hackaday Skulls (likes), requires an API key
#DATA_SOURCE = "https://api.hackaday.io/v1/projects/1340?api_key="+settings['hackaday_token']
#DATA_LOCATION = ["skulls"]

# Twitter followers
#DATA_SOURCE = "https://cdn.syndication.twimg.com/widgets/followbutton/info.json?" + \
#"screen_names=adafruit"
#DATA_LOCATION = [0, "followers_count"]

uart = busio.UART(board.TX, board.RX, timeout=0.1)
resetpin = DigitalInOut(board.D5)
rtspin = DigitalInOut(board.D9)

# Create the connection to the co-processor and reset
esp = adafruit_espatcontrol.ESP_ATcontrol(uart, 115200, run_baudrate=921600,
                                          reset_pin=resetpin,
                                          rts_pin=rtspin, debug=True)
esp.hard_reset()

requests.set_interface(esp)

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)
# Attach a 7 segment display and display -'s so we know its not live yet
display = segments.Seg7x4(i2c)
display.print('----')

# neopixels
if NEOPIXELS_ON_CHANGE:
    pixels = neopixel.NeoPixel(board.A1, 16, brightness=0.4, pixel_order=(1, 0, 2, 3))
    pixels.fill(0)

# music!
if PLAY_SOUND_ON_CHANGE:
    import audioio
    wave_file = open("coin.wav", "rb")
    wave = audioio.WaveFile(wave_file)

# we'll save the value in question
last_value = value = None
the_time = None
times = 0

def chime_light():
    """Light up LEDs and play a tune"""
    if NEOPIXELS_ON_CHANGE:
        for i in range(0, 100, 10):
            pixels.fill((i, i, i))
    if PLAY_SOUND_ON_CHANGE:
        with audioio.AudioOut(board.A0) as audio:
            audio.play(wave)
            while audio.playing:
                pass
    if NEOPIXELS_ON_CHANGE:
        for i in range(100, 0, -10):
            pixels.fill((i, i, i))
        pixels.fill(0)

while True:
    try:
        while not esp.is_connected:
            # settings dictionary must contain 'ssid' and 'password' at a minimum
            esp.connect(settings)

        the_time = esp.sntp_time

        # great, lets get the data
        print("Retrieving data source...", end='')
        r = requests.get(DATA_SOURCE)
        print("Reply is OK!")
    except (RuntimeError, adafruit_espatcontrol.OKError) as e:
        print("Failed to get data, retrying\n", e)
        continue
    #print('-'*40,)
    #print("Headers: ", r.headers)
    #print("Text:", r.text)
    #print('-'*40)

    value = r.json()
    for x in DATA_LOCATION:
        value = value[x]
    if not value:
        continue
    print(times, the_time, "value:", value)

    if last_value != value:
        chime_light() # animate the neopixels
        last_value = value
    times += 1

    # normally we wouldn't have to do this, but we get bad fragments
    r = value = None
    gc.collect()
    print(gc.mem_free())  # pylint: disable=no-member
    time.sleep(TIME_BETWEEN_QUERY)
