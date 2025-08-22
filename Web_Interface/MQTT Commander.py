import paho.mqtt.client as mqtt

def setup_mqtt():
    broker_address = config["mqtt_broker_address"]
    mqtt_client = mqtt.Client("interlocking")  # create new instance
    mqtt_client.connect(broker_address)  # connect to broker
    mqtt_client.on_message = on_message
    mqtt_client.subscribe("set/#")
    mqtt_client.loop_start()
    mqtt_client.publish("interlocking", "running")  # publish
    return mqtt_client

list_of_secto

commands_list = {"Occupy Section A" : {"set/section/A/occstatus" : 5},
                 "Occupy Section B" : {"set/section/Q/occstatus" : 5}}

