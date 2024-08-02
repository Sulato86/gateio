# trading-crypto
 untuk trading crypto dengan HTTP API

### Struktur
crypto-trading-app/
│
├── controller/
│   ├── csv_handler.py
│   ├── pandasa.py
│   └── workers.py
│
├── api/
│   └── api_gateio.py
│
├── ui/
│   └── ui_main_window.py
│
├── .env
├── main.py
├── requirements.txt
└── README.md

# api_gateio.py
    - get_all_symbols: Mengambil semua simbol pasangan mata uang dari API.
    - rate_limited_fetch: Mengambil data dari URL dengan pembatasan laju permintaan.
    - async_get_ticker_info: Mengambil informasi ticker untuk simbol tertentu secara asinkron.
    - get_account_balance: Mengambil saldo akun dari API.
    - get_open_orders: Mengambil pesanan terbuka untuk simbol tertentu dari API.
    - get_closed_orders: Mengambil pesanan yang telah selesai untuk simbol tertentu dari API.
    - get_server_time: Mengambil waktu server dari API.
    - create_order: Membuat pesanan baru dengan parameter tertentu.
    - cancel_order: Membatalkan pesanan berdasarkan ID pesanan dan simbol.
    - get_trade_history: Mengambil riwayat perdagangan untuk simbol tertentu dari API.
    - fetch_tickers_for_symbols: Mengambil informasi ticker untuk beberapa simbol secara asinkron menggunakan async_get_ticker_info.

# pandasa.py
    Kelas PandasModel:
        __init__: Inisialisasi instance model dengan data yang diberikan dalam bentuk DataFrame.
        rowCount: Mengembalikan jumlah baris dalam DataFrame.
        columnCount: Mengembalikan jumlah kolom dalam DataFrame.
        data: Mengambil data dari DataFrame untuk ditampilkan di tabel. Mengembalikan nilai sebagai string, dan mengembalikan string kosong jika nilai adalah NaN.
        headerData: Mengambil data header untuk kolom dan baris. Mengembalikan nama kolom untuk header horizontal dan indeks baris untuk header vertikal.
        sort: Mengurutkan data berdasarkan kolom yang dipilih. Mengubah layout sebelum dan sesudah pengurutan untuk memperbarui tampilan tabel.
        update_data: Memperbarui data dalam model dengan DataFrame baru. Mengubah layout sebelum dan sesudah pembaruan untuk memperbarui tampilan tabel.

# workers.py
    Kelas QThreadWorker:
        __init__: Menginisialisasi instance dengan daftar pasangan mata uang dan kunci API.
        run: Menjalankan loop event asinkron untuk mengambil data secara periodik.
        run_fetch_data: Fungsi asinkron yang terus mengambil data setiap 10 detik.
        fetch_data: Mengambil data ticker untuk setiap pasangan mata uang dan mengirim hasilnya melalui sinyal result_ready.
        stop: Menghentikan loop pengambilan data.

    Kelas BalanceWorker:
        __init__: Menginisialisasi instance dengan kunci API.
        run: Mengambil saldo akun dari API dan mengirim hasilnya melalui sinyal balance_signal

# main_window.py
    - Kelas CustomSortFilterProxyModel:
    Kelas ini mengatur cara penyortiran data pada tabel. Ini memungkinkan penyortiran khusus berdasarkan tipe data di setiap kolom.

    - Kelas MainWindow:
    __init__: Inisialisasi komponen GUI, API Gate.io, dan data yang akan ditampilkan di tabel.
        - Inisialisasi API menggunakan kunci API dan rahasia dari variabel lingkungan.
        - Inisialisasi pasangan mata uang yang akan ditampilkan.
        - Mengatur model data untuk tampilan pasar dan akun.
        - Menghubungkan sinyal dan slot untuk pembaruan data dan tindakan pengguna.
    update_model_market: Memperbarui model data pasar dengan data baru yang diterima.
    update_model_account: Memperbarui model data akun dengan data baru yang diterima.
    update_balance: Memperbarui saldo akun dengan data baru yang diterima.
    add_pair: Menambahkan pasangan mata uang baru ke dalam daftar dan memperbarui tampilan.
    export_marketdata_to_csv: Mengekspor data pasar ke file CSV.
    on_export_finished: Menampilkan pesan setelah ekspor selesai.
    closeEvent: Menghentikan worker thread saat aplikasi ditutup.

# csv_handler.py
    Kelas ExportWorker:
    progress: Sinyal yang digunakan untuk mengirim kemajuan ekspor dalam bentuk persentase.
    finished: Sinyal yang digunakan untuk mengirim pesan ketika proses ekspor selesai atau gagal.
    __init__: Inisialisasi instance dengan model data dan path file tujuan ekspor.
    run: Metode utama yang dijalankan saat thread dimulai.
        - Membuka file CSV untuk menulis.
        - Menulis header kolom berdasarkan data dari model.
        - Mengiterasi baris data dalam model, menulis setiap baris ke file CSV, dan memperbarui sinyal kemajuan.
        - Mengirim sinyal finished dengan pesan sukses atau gagal tergantung hasil proses ekspor.

# Tugas dan Fungsi Kode yang Berkaitan dengan Lainnya:
    - main_window.py: Ini adalah file utama yang mengelola antarmuka pengguna (GUI) dan mengintegrasikan berbagai komponen seperti pengolahan data, pekerja latar belakang (workers), dan API Gate.io.
    - workers.py: Mengandung kelas QThreadWorker untuk mengambil data ticker dari API dan BalanceWorker untuk mengambil saldo akun. Kedua kelas ini menggunakan threading untuk menjalankan tugas asinkron secara paralel.
    - pandasa.py: Menyediakan model data untuk tabel yang ditampilkan di GUI. PandasModel mengubah DataFrame menjadi model tabel yang dapat digunakan oleh PyQt, dan CustomSortFilterProxyModel memungkinkan penyortiran dan pemfilteran data.
    - csv_handler.py: Mengelola impor dan ekspor data dari dan ke file CSV. Mengandung pekerja latar belakang (ExportWorker dan ExportNotifPriceWorker) untuk menangani operasi ini tanpa mengunci GUI.
    - api_gateio.py: Menyediakan fungsi untuk berinteraksi dengan API Gate.io, termasuk mengambil simbol, saldo akun, pesanan terbuka, pesanan tertutup, waktu server, dan riwayat perdagangan.

# Optimasi untuk Tiap Kode:
    - main_window.py:
        - Memastikan penggunaan thread worker yang efisien dengan memeriksa status thread sebelum memulai yang baru.
        - Memastikan pembaruan model tabel hanya ketika data baru tersedia untuk mengurangi beban pada GUI.

    - workers.py:
        - Menggunakan asyncio dan aiohttp untuk mengambil data secara efisien dan mengurangi latensi jaringan.
        - Menambahkan pengecekan status yang lebih sering untuk menghentikan thread dengan cepat jika diperlukan.

    - pandasa.py:
        - Menambahkan caching untuk hasil penyortiran dan pemfilteran jika data tidak berubah untuk meningkatkan kinerja.

    - csv_handler.py:
        - Menggunakan metode batch untuk membaca dan menulis file CSV jika dataset sangat besar untuk mengurangi penggunaan memori.

    - api_gateio.py:
        - Mengimplementasikan retry mechanism untuk permintaan API yang gagal karena masalah jaringan sementara.

======================Designer=================
pyuic5 -o ui/ui_main_window.py ui/main_window.ui
===============================================
=================INSTALL=======================
pyinstaller --onedir --windowed --clean main_window.py
===============================================
==================FLOWCHART====================
doxygen Doxyfile
