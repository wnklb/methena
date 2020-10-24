from time import sleep

import paho.mqtt.client as mqtt


class MqttClient:
    def __init__(self):
        self.client = mqtt.Client(client_id="CCXT-OHLCV-Fetcher", clean_session=True, userdata=None)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def __enter__(self):
        self.run()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def run(self):
        self.connect()
        self.start()

    def connect(self):
        self.client.connect(host='localhost')

    def disconnect(self):
        self.client.disconnect()

    def start(self):
        self.client.loop_start()

    def stop(self):
        self.client.loop_stop()

    def subscribe(self):
        pass

    def unsubscribe(self):
        pass

    def publish(self, topic, payload, qos=1, retain=False):
        self.client.publish(topic, payload, qos, retain)

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(self, client, userdata, flags, rc):
        print("MQTT client connected to borker '{}' with result code ".format(str(rc)))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("ccxt")

    # The callback for when a PUBLISH message is received from the server.
    def _on_disconnect(client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection.")

    def _on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))

    def _on_publish(client, userdata, mid):
        print('Message published')

    def _on_subscribe(client, userdata, mid, granted_qos):
        pass

    def _on_unsubscribe(client, userdata, mid):
        pass


if __name__ == '__main__':
    with MqttClient() as mqttc:
        mqttc.publish(topic='ccxt', payload='running from python')
