import logging

import paho.mqtt.client as mqtt

from services.state import StateService
from utils.mqtt_parser import MQTTParser

from config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC_CCXT_OHLCV

log = logging.getLogger()


class MqttClient:
    def __init__(self):
        self.client = mqtt.Client(client_id="CCXT-OHLCV-Fetcher", clean_session=True, userdata=None)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        self.parser = MQTTParser()
        self.ohlcv_config_service = StateService.get_instance()

    def __enter__(self):
        try:
            self.client.connect(MQTT_HOST, MQTT_PORT)
        except Exception as e:
            raise ConnectionError("Unable to connect to mqtt broker at '{}:{}'".format(MQTT_HOST, MQTT_PORT))
        self.client.loop_start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic, qos=0):
        pass

    def unsubscribe(self, topic):
        pass

    def publish(self, topic, payload, qos=1, retain=False):
        self.client.publish(topic, payload, qos, retain)

    # The callback for when the client receives a CONNACK response from the server.
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.debug("Successfully connected to broker: '{}'".format(mqtt.connack_string(rc)))
        else:
            log.debug("Error connecting to broker: '{}'".format(mqtt.connack_string(rc)))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(MQTT_TOPIC_CCXT_OHLCV)
        print(MQTT_TOPIC_CCXT_OHLCV)
        client.message_callback_add(MQTT_TOPIC_CCXT_OHLCV, self.on_ccxt_ohlcv_message)

    def on_ccxt_ohlcv_message(self, client, userdata, msg):
        print(type(msg.topic))
        print('received ccxt message ' + msg.payload.decode())
        if 'ccxt/ohlcv/add' in msg.topic:
            descriptor = self.parser.parse_ccxt_ohlcv_topic(msg.topic, msg.payload)
            self.ohlcv_config_service.add(descriptor)
        elif 'ccxt/ohlcv/remove' in msg.topic:
            descriptor = self.parser.parse_ccxt_ohlcv_topic(msg.topic, msg.payload)

    # The callback for when a PUBLISH message is received from the server.
    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            log.warning("Unexpected disconnection.")

    def _on_message(self, client, userdata, msg):
        log.debug(msg.topic + " " + str(msg.payload))

    def _on_publish(self, client, userdata, mid):
        pass

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def _on_unsubscribe(self, client, userdata, mid):
        pass


if __name__ == '__main__':
    with MqttClient() as mqttc:
        # mqttc.publish(topic='ccxt', payload='runeuening from python')
        while True:
            pass
