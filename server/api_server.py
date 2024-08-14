import asyncio
import threading
import sys
import psycopg2
from flask import Flask, request, jsonify
from data_handler import DataHandler
from logging_config import configure_logging

app = Flask(__name__)

logger = configure_logging('api_server', 'logs/api_server.log')

data_handler = None

def start_modul_server():
    global data_handler
    data_handler = DataHandler()
    data_handler.start_websocket()

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

@app.route('/get_candlestick_data', methods=['GET'])
def get_candlestick_data():
    try:
        pair = request.args.get('pair')
        period = int(request.args.get('period'))
        limit = int(request.args.get('limit', 100))
        if not pair or not period:
            logger.warning("Pair dan periode tidak diberikan dalam permintaan.")
            return jsonify({"error": "Pair and period are required"}), 400
        data = data_handler.fetch_candlestick_data(pair, period, limit)
        if not data:
            return jsonify({"error": "No data available"}), 404
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Failed to fetch candlestick data: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    threading.Thread(target=start_modul_server, daemon=True).start()
    logger.info("API server dimulai, menunggu permintaan...")
    app.run(host='0.0.0.0', port=5000)
