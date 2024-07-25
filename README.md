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
    Imports dan Konfigurasi Awal:
    - Menggunakan os, asyncio, logging, ClientSession, dan ClientError dari aiohttp, serta dotenv untuk memuat variabel lingkungan.
    - Menggunakan gate_api untuk mengakses API Gate.io, termasuk SpotApi, Configuration, ApiClient, dan ApiException.

    Inisialisasi GateioAPI:
    - Kelas GateioAPI menginisialisasi dengan api_key dan secret_key dari environment variables.
    - Mengonfigurasi ApiClient dan SpotApi dari gate_api.
    - Menambahkan konfigurasi rate_limit untuk membatasi jumlah permintaan per detik.
    - Logging untuk mencatat inisialisasi dan kesalahan.

    Metode get_all_symbols:
    - Mengambil semua pasangan mata uang kripto yang tersedia dari API Gate.io.
    - Menangani pengecualian ApiException dan mencatat kesalahan jika terjadi.

    Metode async_get_ticker_info:
    - Metode asinkron untuk mendapatkan informasi ticker dari API Gate.io menggunakan ClientSession.
    - Menangani permintaan dan menangani pengecualian jika terjadi kesalahan.

    Potensi masalah yang perlu diperhatikan:
    - Tangani pengecualian dan kesalahan jaringan dengan baik untuk menghindari kegagalan aplikasi.

# pandasa.py
    Imports dan Konfigurasi Awal:
    - Menggunakan logging untuk mencatat log dan pandas untuk pengolahan data.
    - Mengimpor QAbstractTableModel dan Qt dari PyQt5.QtCore.

    Inisialisasi Logging:
    - Menyiapkan konfigurasi logging untuk mencatat ke file (pandas.log) dan ke console

    Kelas PandasModel:
    Subclass dari QAbstractTableModel.
    - Metode __init__: Menginisialisasi dengan data yang diberikan dan mencatat inisialisasi.
    - Metode rowCount: Mengembalikan jumlah baris data.
    - Metode columnCount: Mengembalikan jumlah kolom data.
    - Metode data: Mengembalikan data untuk tampilan tabel berdasarkan indeks dan peran yang diberikan.
    - Mengembalikan nilai sebagai string dan menangani nilai NaN.
    - Metode headerData: Mengembalikan data header untuk kolom dan baris.
    - Metode sort: Mengurutkan data berdasarkan kolom yang ditentukan dan mencatat sebelum dan sesudah pengurutan (menampilkan 10 baris pertama sebelum sorting).
    
    Potensi masalah yang perlu diperhatikan:
    - Pastikan data yang diteruskan ke PandasModel valid dan tidak kosong.
    - Tangani perubahan data secara efisien untuk menghindari masalah kinerja pada tabel besar.

# workers.py
    Imports dan Konfigurasi Awal:
    - Menggunakan asyncio, pandas, logging, ClientSession dari aiohttp, datetime, QThread, dan pyqtSignal dari PyQt5.QtCore.
    - Mengimpor GateioAPI dari api.api_gateio.

    Inisialisasi Logging:
    - Menyiapkan konfigurasi logging untuk mencatat ke file (workers.log) dan ke console.

    Kelas QThreadWorker:
    - Subclass dari QThread.
    - Sinyal result_ready: Sinyal yang akan mengirimkan DataFrame Pandas saat data sudah siap.
    - Metode __init__: Menginisialisasi dengan daftar pasangan mata uang dan kunci API. Membuat instance GateioAPI.
    - Metode run: Memulai event loop asinkron untuk mendapatkan data pasar.
    - Metode fetch_data: Metode asinkron untuk mengambil data dari API Gate.io untuk setiap pasangan mata uang.
    - Menggunakan ClientSession untuk membuat permintaan HTTP.
    - Memproses data yang diterima dan mencatatnya.

    Kelas BalanceWorker:
    - Kelas ini belum terlihat dalam bagian kode yang dibaca. Namun, asumsi dari penggunaan di main_window.py, kelas ini kemungkinan besar mirip dengan QThreadWorker tetapi fokus pada mendapatkan saldo akun.

    Potensi masalah yang perlu diperhatikan:
    - Pastikan event loop asinkron dikelola dengan benar untuk menghindari kebocoran memori atau thread yang tidak berhenti.
    - Tangani pengecualian jaringan dengan baik untuk menghindari kegagalan aplikasi.

# main_window.py

# Kesimpulan
    - workers.py bertanggung jawab untuk mengambil data dari API Gate.io dan memancarkan sinyal dengan DataFrame hasil pengambilan data.
    - main_window.py menangani sinyal tersebut, memperbarui data di PandasModel, dan memastikan tampilan GUI diperbarui dengan data terbaru.
    - pandasa.py mengelola tampilan data dalam tabel GUI menggunakan PandasModel.

======================Designer=================
pyuic5 -o ui/ui_main_window.py ui/main_window.ui
===============================================
=================INSTALL=======================
pyinstaller --onedir --windowed --clean main.py
===============================================