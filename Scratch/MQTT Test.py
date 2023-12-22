import paho.mqtt.client as mqtt #import the client1

def on_connect(client, userdata, flags, rc):  # The callback for when the client connects to the broker
    print("Connected with result code {0}".format(str(rc)))
    # Print result of connection attempt client.subscribe("digitest/test1")
    # Subscribe to the topic “digitest/test1”, receive any messages published on it
def on_message(mqtt_client, userdata, message):
    print("Message received-> " + message.topic + " " + str(message.payload))


broker_address="127.0.0.1"
#broker_address="iot.eclipse.org" #use external broker
client = mqtt.Client("P1") #create new instance
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker_address) #connect to broker
client.publish("house/main-light","OON")#publish
client.subscribe("#")


client.loop_start()

while True:
    pass
