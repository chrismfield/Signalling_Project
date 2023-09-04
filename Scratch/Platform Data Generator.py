import json
import datetime

with open(r'C:\Users\Chris\Dropbox\Personal Projects\Python\Signalling Project\Sample Station Data.json', 'r',
          encoding="utf-8") as inputfile:
    inputstring = inputfile.read()
inputdatadict = json.loads(inputstring)

print(inputdatadict['Name'])
print('Reference Point: ' + inputdatadict['referencepoint'])


class StoppingWindow:
    pass


class GradientProfile():
    def __init__(self):
        self.Q_SCALE = 0
        self.D_GRADIENT = 0
        self.GDIR = 0
        self.G_A = 0
        self.N_ITER = 0  # NOTE DUPLICATE VARIABLE USED FOR DIFFERENT PURPOSES
        self.D_GRADIENTk = 0
        self.Q_GDIRk = 0
        self.A_Ak = 0


class SpeedLimitProfile():
    def __init__(self):
        self.D_STATIC = 0
        self.V_STATIC = 0
        self.Q_FRONT = 0
        self.N_ITER = 0  # NOTE DUPLICATE VARIABLE USED FOR DIFFERENT PURPOSES
        self.D_STATICl = 0
        self.V_STATICl = 0
        self.Q_FRONTl = 0


class Packet44Data():
    def __init__(self):
        self.bgname = ""
        self.NID_PACKET = 44  # Packet44
        self.Q_DIR = 1  # Always 01
        self.L_PACKET = 0  # 13 bit length of packet, including header
        self.NID_XUSER = 9  # Always 9
        self.NID_UKSYS = 15  # Identifies ABDO Application
        self.T_UKSTART = 0  # CLARIFICATION REQUIRED
        self.T_UKFINISH = 0  # CLARIFICATION REQUIRED
        self.NID_STATION = 0  # Lookup station code
        self.D_DOOR_RELEASE = 0  # Distance to start of the door release window - 16 bits units of ????
        self.L_DOOR_RELEASE = 0  # Length of the door release window - 16 bits units of????
        self.Q_DOOR_SIDE = 11  # Door side to be released - CHECK CODING 2 bits
        self.D_PDOOR_RELEASE = 22  # Exact stopping position relative to ???? in units of ???? 12 bits
        self.Q_CONFIGURATION = 0  # Identifies what train type the packet applies to (5 or 10 car) CHECK CODING 8 bits
        # need to add in gradient and speed profile as required from their classes.


testinstance = Packet44Data()
testgradient = GradientProfile()
testspeedprofile = SpeedLimitProfile()

ct = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

with open('C:\\Users\\Chris\\Dropbox\\Personal Projects\\Python\\Signalling Project' + inputdatadict['Name'] \
        + ' WithClassOutput.json', 'w', encoding="utf-8") as outputfile:
    json.dump({'Generated at ': ct, 'InputInfo': inputdatadict, 'Packet44OutputForInitialisation': testinstance.__dict__},
              outputfile, indent=2)
