import asyncio
import functools
import logging

import paho.mqtt.client as mqtt

from config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC_CCXT_OHLCV
from services import CCXTService, StateService
from utils.mqtt_parser import MQTTParser
from utils.singleton import Singleton

log = logging.getLogger('methena')


class MqttClient(Singleton):
    client = None
    parser = MQTTParser()
    ccxt_service = CCXTService()
    state_service = StateService()
    log.debug('Create MqttClient')

    def __init__(self, loop):
        if self.client is None:
            self.client = mqtt.Client(client_id='CCXT-OHLCV-Fetcher', clean_session=True,
                                      userdata=None)
            self.client.on_connect = self.__on_connect
            self.client.on_disconnect = self.__on_disconnect
            self.client.on_message = self.__on_message
            self.client.on_publish = self.__on_publish
            self.client.on_subscribe = self.__on_subscribe
            self.client.on_unsubscribe = self.__on_unsubscribe
        self.loop = loop
        log.debug('Initialized MqttClient')

    def start(self):
        try:
            self.client.connect(MQTT_HOST, MQTT_PORT)
        except Exception as e:
            raise ConnectionError('Unable to connect to mqtt broker at {}:{}. Error: {}'.format(
                MQTT_HOST, MQTT_PORT, e))
        self.client.loop_start()
        log.info('MQTT loop started')
        return self

    def stop(self):
        self.client.loop_stop()
        log.info('MQTT loop stopped')
        self.client.disconnect()
        log.info('MQTT client disconnected from {}:{}'.format(MQTT_HOST, MQTT_PORT))

    def subscribe(self, topic, qos=0):
        pass

    def unsubscribe(self, topic):
        pass

    def publish(self, topic, payload, qos=1, retain=False):
        self.client.publish(topic, payload, qos, retain)

    # The callback for when the client receives a CONNACK response from the server.
    def __on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            log.info('MQTT client successfully connected to broker at {}:{}'.format(MQTT_HOST,
                                                                                    MQTT_PORT))
        else:
            log.warning('MQTT failed connecting to broker at {}:{}'.format(MQTT_HOST, MQTT_PORT))
            # TODO: raise exception that we were unable to connect

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(MQTT_TOPIC_CCXT_OHLCV)
        client.message_callback_add(MQTT_TOPIC_CCXT_OHLCV, self.on_ccxt_ohlcv_message)

    def on_ccxt_ohlcv_message(self, client, userdata, msg):
        log.info('MQTT received topic: {}'.format(msg.topic))
        raw_descriptor = self.parser.parse_ccxt_ohlcv_topic(msg.topic, msg.payload)
        if 'ccxt/ohlcv/add' in msg.topic:
            self.__on_ccxt_ohlcv_message_add(raw_descriptor)
        elif 'ccxt/ohlcv/remove' in msg.topic:
            self.__on_ccxt_ohlcv_message_remove(raw_descriptor)
        elif 'ccxt/ohlcv/replace' in msg.topic:
            pass

    def __on_ccxt_ohlcv_message_add(self, raw_descriptor):
        exchanges = raw_descriptor[0]
        if exchanges == '*':
            exchanges = self.ccxt_service.get_exchanges()
        task = asyncio.ensure_future(self.ccxt_service.init_exchange_markets(exchanges),
                                     loop=self.loop)
        task.add_done_callback(
            functools.partial(self.__callback_on_ccxt_ohlcv_message_add, raw_descriptor))

    def __callback_on_ccxt_ohlcv_message_add(self, raw_descriptor, result):
        descriptor = self.ccxt_service.build_descriptor(raw_descriptor)
        descriptor_validated = self.ccxt_service.validate_descriptor(descriptor)
        self.state_service.add_descriptor(descriptor_validated)

    def __on_ccxt_ohlcv_message_remove(self, raw_descriptor):
        descriptor = self.ccxt_service.build_descriptor(raw_descriptor)
        descriptor_validated = self.ccxt_service.validate_descriptor(descriptor)
        self.state_service.remove_descriptor(descriptor_validated)

    # The callback for when a PUBLISH message is received from the server.
    def __on_disconnect(self, client, userdata, rc):
        if rc != 0:
            log.warning('MQTT disconnected unexpectedly from {}:{}.'.format(MQTT_HOST, MQTT_PORT))

    def __on_message(self, client, userdata, msg):
        log.debug(msg.topic + ' ' + str(msg.payload))

    def __on_publish(self, client, userdata, mid):
        pass

    def __on_subscribe(self, client, userdata, mid, granted_qos):
        pass

    def __on_unsubscribe(self, client, userdata, mid):
        pass
