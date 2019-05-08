# IR Controlled Lights for the Adafruit Circuit Playground Express
# Written for core-electronics.com.au
# For use on two Circuit Playgrounds, pressing button A or B on one board
# turns on a short light animation on the receiving board.

from adafruit_circuitplayground.express import cpx
import board
import random
import time
import pulseio
import array 

hitKtr = 0
badgeColors = [(0,255,0),(255,255,0),(255,70,0),(255,0,0)]

# Create IR input, maximum of 59 bits. 
pulseIn = pulseio.PulseIn(board.IR_RX, maxlen=59, idle_state=True)
# Clears any artifacts
pulseIn.clear()
pulseIn.resume() 

# Creates IR output pulse
pwm = pulseio.PWMOut(board.IR_TX, frequency=38000, duty_cycle=2 ** 15)
pulse = pulseio.PulseOut(pwm)

# Array for button A pulse, this is the pulse output when the button is pressed
# Inputs are compared against this same array
# array.array('H', [x]) must be used for IR pulse arrays when using pulseio
# indented to multiple lines so its easier to see
pulse_A = array.array('H', [9355, 4469, 639, 512, 633, 517, 640, 512, 633, 516, 
    640, 508, 637, 512, 634, 513, 633, 514, 631, 1623, 636, 1623, 638, 1620, 639, 
    1619, 641, 1617, 633, 1625, 635, 515, 640, 1617, 643, 507, 639, 1619, 640, 
    1620, 640, 508, 638, 514, 641, 509, 637, 513, 643, 508, 638, 1620, 639, 511, 
    634, 515, 641, 1617, 643])
pulse_B = array.array('H', [9284, 2233, 636, 65535, 9238, 4501, 607, 564, 602, 
    517, 629, 519, 637, 539, 606, 542, 583, 538, 609, 567, 576, 570, 576, 1679, 
    581, 1648, 612, 1672, 577, 1678, 572, 1692, 568, 1650, 631, 541, 573, 1680, 
    601, 1625, 635, 510, 604, 541, 605, 540, 626, 1654, 575, 570, 607, 511, 603, 
    569, 598, 546, 578, 1676, 605])

# Fuzzy pulse comparison function. Fuzzyness is % error
def fuzzy_pulse_compare(pulse1, pulse2, fuzzyness=1):
    if len(pulse1) != len(pulse2):
        return False
    for i in range(len(pulse1)):
        threshold = int(pulse1[i] * fuzzyness)
        if abs(pulse1[i] - pulse2[i]) > threshold:
            return False
    return True
    
# Initializes NeoPixel ring
cpx.pixels.brightness= 0.05
cpx.pixels.fill((0, 0, 0))
cpx.pixels.show() 

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 85:
        return (int(pos*3), int(255 - (pos*3)), 0)
    elif pos < 170:
        pos -= 85
        return (int(255 - (pos*3)), 0, int(pos*3))
    else:
        pos -= 170
        return (0, int(pos*3), int(255 - pos*3))

def badgeHit(wait, hitKtr):
    cpx.pixels.fill(badgeColors[hitKtr])
    cpx.pixels.show() 
    time.sleep(wait)
    if (hitKtr < 3):
        cpx.pixels.fill((0, 0, 0,))
 
# neopixel animation for random white sparkles
def sparkles(wait):  # Random sparkles - lights just one LED at a time
    i = random.randint(0, len(cpx.pixels) - 1)  # Choose random pixel
    cpx.pixels[i] = ((255, 255, 255))  # Set it to current color
    cpx.pixels.write()  # Refresh LED states
# Set same pixel to "off" color now but DON'T refresh...
# it stays on for now...bot this and the next random
# pixel will be refreshed on the next pass.
    cpx.pixels[i] = [0, 0, 0]
    time.sleep(0.008)  # 8 millisecond delay

# NeoPixel animation to create a rotating rainbow 
def rainbow_cycle(wait):
    for j in range(30):
        for i in range(len(cpx.pixels)):
            idx = int((i * 256 / len(cpx.pixels)) + j*20)
            cpx.pixels[i] = wheel(idx & 255)
        cpx.pixels.show()
        time.sleep(wait)
    cpx.pixels.fill((0, 0, 0,))

# serial print once when activated    
print('IR Activated!')
    
while True:
# when button is pressed, send IR pulse
# detection is paused then cleared and resumed after a short pause
# this prevents reflected detection of own IR
    while cpx.button_a:
        pulseIn.pause()  # pauses IR detection
        pulse.send(pulse_A)  # sends IR pulse
        time.sleep(.2)  # wait so pulses dont run together
        pulseIn.clear()  # clear any detected pulses to remove partial artifacts
        pulseIn.resume()  # resumes IR detection
    while cpx.button_b:
        pulseIn.pause()
        pulse.send(pulse_B)
        time.sleep(.2)
        pulseIn.clear()
        pulseIn.resume()
    
# Wait for a pulse to be detected of desired length
    while len(pulseIn) >= 59:  # our array is 59 bytes so anything shorter ignore
        pulseIn.pause()  
# converts pulseIn raw data into useable array
        detected = array.array('H', [pulseIn[x] for x in range(len(pulseIn))])  
        print(len(pulseIn))
        print(detected) 
        
    # Got a pulse, now compare against stored pulse_A and pulse_B
        if fuzzy_pulse_compare(pulse_A, detected):  
            print('Received correct Button A control press!')
            t_end = time.monotonic() + 2  # saves time 2 seconds in the future
            while time.monotonic() < t_end: # plays sparkels until time is up
                sparkles(.001)
            hitKtr = 0
            cpx.pixels.fill((0, 0, 0,))
        
        if fuzzy_pulse_compare(pulse_B, detected):
            print('Received correct Button B control press!')
            t_end = time.monotonic() + 2
            while time.monotonic() < t_end:
                badgeHit(.001, hitKtr)
            hitKtr = hitKtr + 1

        time.sleep(.1)      
        pulseIn.clear()      
        pulseIn.resume()
