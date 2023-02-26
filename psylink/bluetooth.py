#from bleak import BleakClient, BleakScanner
import simplepyble
adapter = simplepyble.Adapter.get_adapters()[0]


from psylink.config import DEFAULT_BLE_ADDRESS, ASSUMED_BLE_LATENCY
from threading import Thread, Event
from queue import Queue
import logging
import time


class BLECharacteristics:
    SENSOR = '0a3d3fd8-2f1c-46fd-bf46-eaef2fda91e5'
    CNF_CHANNELS = '0a3d3fd8-2f1c-46fd-bf46-eaef2fda91e6'


class BLEBackend:
    MAX_PIPE_SIZE = 10

    def __init__(self, address=DEFAULT_BLE_ADDRESS):
        self.address = address
        self.pipe = Queue(maxsize=self.MAX_PIPE_SIZE)
        self.stop_event = Event()
        self.client = None
        self.thread = None
        self.is_initialized = False
        self.init()

    def reset(self):
        self.stop_event.clear()
        while not self.pipe.empty():
            self.pipe.get()

    def init(self):
        pass

    def get_latency(self):
        # Would be awesome if I can actually get the latency somehow
        return ASSUMED_BLE_LATENCY

    def is_connected(self):
        return bool(self.thread and self.thread.is_alive())

    def connect(self):
        print("Part 3")
        raise NotImplementedError("Please Override this in subclass")

    def disconnect(self):
        raise NotImplementedError("Please Override this in subclass")

    def read(self, characteristic_uuid):
        raise NotImplementedError("Please Override this in subclass")

    def read_sensor(self):
        return self.read(BLECharacteristics.SENSOR)

    def read_channels(self):
        return self.read(BLECharacteristics.CNF_CHANNELS)

    def thread_start(self, disconnect_on_stop=False):
        if self.thread is not None:
            logging.warning("Attempted to start BLE thread while it was already running")
            return

        self.reset()
        self.thread = Thread(
            target=self.thread_loop,
            args=(self.stop_event, self.pipe, disconnect_on_stop)
        )
        self.thread.start()

    def thread_stop(self):
        if self.thread is None:
            logging.info("Not stopping BLE thread because it's not running")
        else:
            self.stop_event.set()
            self.thread = None

    def thread_loop(self, stop_event, pipe, disconnect_on_stop):
        try:
            while not stop_event.is_set():
                content = self.read_sensor()
                timestamp = time.time()
                pipe.put(dict(timestamp=timestamp, content=content))
        finally:
            if disconnect_on_stop:
                self.disconnect()


class BLEGATTBackend(BLEBackend):
    def init(self):
        adapter.scan_for(5000)
        peripherals = adapter.scan_get_results()
        for i, peripheral in enumerate(peripherals):
            if peripheral.address() == self.address:
                self.client = peripheral

    def connect(self):
        self.client.connect()

    def disconnect(self):
        self.client.disconnect()

    def read(self,characteristic_uuid):
        service_uuid = '0a3d3fd8-2f1c-46fd-bf46-eaef2fda91e4'
        char_uuid = '0a3d3fd8-2f1c-46fd-bf46-eaef2fda91e5'
        try:
            return self.client.read(service_uuid, characteristic_uuid)
        except:
            self.disconnect()
            print("It messed up")





class BleakBackend(BLEBackend):
    # Doesn't work as of yet due to asyncio entanglement
    def init(self):
        import bleak
        self.client = bleak.BleakClient(self.address)

    async def connect(self):
        await self.client.connect()

    def disconnect(self):
        import asyncio
        asyncio.get_event_loop().run_until_complete(self.client.disconnect())

    def read(self, characteristic_uuid):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
                self.client.read_gatt_char(characteristic_uuid))


BACKENDS = dict(
    #bleak=BleakBackend,
    BLE_GATT=BLEGATTBackend,
)
