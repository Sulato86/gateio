import asyncio
import threading
import sys
import psycopg2
from flask import Flask, request, jsonify
from modul_server import DataHandler
from logging_config import configure_logging  # Pastikan impor konfigurasi logging yang benar

# Inisialisasi Flask
app = Flask(__name__)

# Inisialisasi logger
logger = configure_logging('api_server', 'logs/api_server.log')

# Inisialisasi DataHandler
data_handler = None

def start_modul_server():
    global data_handler
    data_handler = DataHandler()
    data_handler.start_websocket()

# Route untuk menambah pair
@app.route('/add_pair', methods=['POST'])
def add_pair():
    try:
        pair = request.json.get('pair')
        logger.info(f"Menerima permintaan untuk menambahkan pair: {pair}")
        if pair:
            data_handler.add_pair(pair)
            logger.info(f"Pair {pair} ditambahkan ke websocket.")
            return jsonify({"message": f"Pair {pair} added successfully"}), 200
        else:
            logger.warning("Permintaan POST tidak memiliki field 'pair'.")
            return jsonify({"error": "Pair is missing"}), 400
    except Exception as e:
        logger.error(f"Terjadi kesalahan saat memproses permintaan POST: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Mulai modul_server.py sebagai thread
    threading.Thread(target=start_modul_server, daemon=True).start()

    # Jalankan Flask API
    logger.info("API server dimulai, menunggu permintaan...")
    app.run(host='0.0.0.0', port=5000)
