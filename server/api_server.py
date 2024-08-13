from flask import Flask, request, jsonify
from modul_server import DataHandler
import threading

app = Flask(__name__)
data_handler = None

def start_modul_server():
    global data_handler
    data_handler = DataHandler()
    data_handler.start_websocket()

@app.route('/add_pair', methods=['POST'])
def add_pair():
    pair = request.json.get('pair')
    if pair:
        data_handler.add_pair(pair)
        return jsonify({"message": f"Pair {pair} added successfully"}), 200
    else:
        return jsonify({"error": "Pair is missing"}), 400

if __name__ == '__main__':
    # Mulai modul_server.py sebagai thread
    threading.Thread(target=start_modul_server, daemon=True).start()
    
    # Jalankan Flask API
    app.run(host='0.0.0.0', port=5000)
