# trading-crypto
 untuk trading crypto dengan HTTP API

# sulato-trade
 untuk trading ke beberapa exchanger menggunakan HTTP API

### Struktur
project_root/
│
├── 
│   
│
├── 
│   
│
├── ui/
│   ├── main_window.ui
│   └── ui_main_window.py
│
├── api/
│   └── api_gateio.py
│
│
│
├── tanalysis/
│   
│
├── main.py
└── requirements.txt


# api_gateio.py

    Impor Modul:
    os, asyncio, dotenv, requests, aiohttp, tenacity, logging: Berbagai modul yang digunakan untuk manajemen lingkungan, HTTP requests, asynchronous programming, retries, dan logging.
    
    Load Environment Variables:
    - Menggunakan load_dotenv() untuk memuat API key dan secret key dari file .env.

    Setup Logging:
    - Menyiapkan logging untuk mencatat log ke file config.log.

    Class GateioAPI:
    - init: Menginisialisasi API key, secret key, dan base URL.
    - get_all_symbols: Mendapatkan semua simbol pasar yang tersedia di Gate.io dengan mencoba ulang hingga 5 kali jika terjadi kesalahan.
    - async_get_ticker_info: Mengambil informasi ticker untuk simbol tertentu secara asinkron.
    - async_get_order_book: Mengambil order book untuk simbol tertentu secara asinkron.
    - check_balance: Memeriksa saldo akun dengan mencoba ulang hingga 5 kali jika terjadi kesalahan.
    - get_open_orders: Mendapatkan semua order yang terbuka untuk daftar simbol yang diberikan.
    - get_closed_orders: Mendapatkan semua order yang sudah tertutup untuk daftar simbol yang diberikan.
    - get_server_time: Mengambil waktu server dari Gate.io.

    Fungsi Asinkron:
    - fetch_data_every_15_seconds: Fungsi ini mengambil informasi ticker untuk simbol tertentu setiap 15 detik dan mencatat log.

    Penggunaan Contoh:
    - Inisialisasi objek GateioAPI.
    - Mendapatkan semua simbol pasar dan mencetaknya.
    - Menjalankan fungsi fetch_data_every_15_seconds secara asinkron untuk simbol 'BTC_USDT'.

# main_window.py
    PandasModel:
    - Inisialisasi Model (__init__): Menghubungkan pandas DataFrame dengan QTableView.
    - rowCount: Mengembalikan jumlah baris dalam DataFrame.
    - columnCount: Mengembalikan jumlah kolom dalam DataFrame.
    - data: Mengembalikan data untuk sel tertentu dalam DataFrame.
    - headerData: Mengembalikan data header untuk kolom atau baris tertentu.
    - update_data: Memperbarui model dengan data baru dan mereset tampilan.

    MainWindow:
    - Inisialisasi Jendela Utama (__init__): Mengatur antarmuka pengguna dan model tabel, serta menginisialisasi API Gate.io.
    - fetch_data: Mengambil data dari API dan memperbarui model dengan informasi terbaru.
    - schedule_update: Menjadwalkan pembaruan data setiap 5 detik menggunakan timer.

======================Designer=================
pyuic5 -o ui/ui_main_window.py ui/main_window.ui
===============================================
=================INSTALL=======================
pyinstaller --onedir --windowed --clean main.py
===============================================