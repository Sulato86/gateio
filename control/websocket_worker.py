import logging
import asyncio
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot
from api.websocket_gateio import GateIOWebSocket

# Inisialisasi logger
logger = logging.getLogger('websocket_worker')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('websocket_worker.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class WebSocketWorker(QThread):
    """
    Kelas untuk menjalankan koneksi WebSocket di dalam thread terpisah.
    """
    message_received = pyqtSignal(dict)
    balance_received = pyqtSignal(list)

    def __init__(self, pairs=None):
        """
        Inisialisasi WebSocketWorker dengan pasangan mata uang yang diberikan.

        Args:
            pairs (list): Daftar pasangan mata uang untuk disubscribe.
        """
        super().__init__()
        self.gateio_ws = GateIOWebSocket(self.send_message_to_ui, pairs)
        self.loop = None
        self.stop_event = asyncio.Event()
        logger.debug("WebSocketWorker initialized with pairs: %s", pairs)

    def run(self):
        """
        Memulai thread dan event loop untuk koneksi WebSocket.
        """
        logger.debug("WebSocketWorker thread started")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.connect())
        except RuntimeError as e:
            logger.error(f"Runtime error: {e}")
        finally:
            logger.debug("Closing event loop")
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()

    async def connect(self):
        """
        Menghubungkan ke WebSocket dan mencoba kembali jika terputus.
        """
        while not self.stop_event.is_set():
            try:
                logger.info("Starting WebSocket connection")
                await self.gateio_ws.run()
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                await asyncio.sleep(5)
                logger.info("Retrying WebSocket connection in 5 seconds")

    def send_message_to_ui(self, message):
        """
        Mengirim pesan yang diterima dari WebSocket ke UI.

        Args:
            message (dict): Pesan yang diterima dari WebSocket.
        """
        logger.debug(f"Emitting message to UI: {message}")
        self.message_received.emit(message)

    def stop(self):
        """
        Menghentikan thread dan menutup koneksi WebSocket.
        """
        logger.debug("Stopping WebSocketWorker")
        if self.loop:
            self.stop_event.set()
            self.loop.call_soon_threadsafe(self.loop.stop)
            logger.debug("Event loop stop called")

    @pyqtSlot(str)
    def add_pair(self, pair):
        """
        Menambahkan pasangan mata uang baru untuk disubscribe.

        Args:
            pair (str): Pasangan mata uang yang akan ditambahkan.
        """
        logger.info(f"Adding new pair: {pair}")
        if pair not in self.gateio_ws.pairs:
            self.gateio_ws.pairs.append(pair)
            logger.debug(f"Pair {pair} added to the list, attempting to subscribe.")
            future = asyncio.run_coroutine_threadsafe(self.gateio_ws.subscribe_to_pair(pair), self.loop)
            future.add_done_callback(self._handle_subscribe_result)
        else:
            logger.info(f"Pair {pair} already exists.")
        logger.debug(f"Current pairs: {self.gateio_ws.pairs}")

    @pyqtSlot(str)
    def remove_pair(self, pair):
        """
        Menghapus pasangan mata uang dari subscription.

        Args:
            pair (str): Pasangan mata uang yang akan dihapus.
        """
        logger.info(f"Removing pair: {pair}")
        if pair in self.gateio_ws.pairs:
            self.gateio_ws.pairs.remove(pair)
            logger.debug(f"Pair {pair} removed from the list, attempting to unsubscribe.")
            future = asyncio.run_coroutine_threadsafe(self.gateio_ws.unsubscribe_from_pair(pair), self.loop)
            future.add_done_callback(self._handle_unsubscribe_result)

            if pair not in self.gateio_ws.pairs:
                logger.debug(f"Pair {pair} successfully removed from WebSocket tracking.")
            else:
                logger.error(f"Pair {pair} still exists in WebSocket tracking.")
        else:
            logger.info(f"Pair {pair} does not exist.")
        logger.debug(f"Current pairs: {self.gateio_ws.pairs}")

    def _handle_subscribe_result(self, future):
        """
        Menghandle hasil dari operasi subscribe.

        Args:
            future (concurrent.futures.Future): Objek future dari operasi subscribe.
        """
        try:
            result = future.result()
            logger.info(f"Subscription result: {result}")
        except Exception as e:
            logger.error(f"Subscription error: {e}")

    def _handle_unsubscribe_result(self, future):
        """
        Menghandle hasil dari operasi unsubscribe.

        Args:
            future (concurrent.futures.Future): Objek future dari operasi unsubscribe.
        """
        try:
            result = future.result()
            logger.info(f"Unsubscription result: {result}")
        except Exception as e:
            logger.error(f"Unsubscription error: {e}")
