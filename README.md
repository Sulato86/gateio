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

# Keterkaitan Antar Bagian:
Interaksi dengan API Gate.io:
    - api/api_gateio.py menyediakan metode untuk berinteraksi dengan API Gate.io.
    - controller/workers.py menggunakan kelas GateioAPI untuk mengambil data dari API Gate.io.

Pembaruan Data di Tabel PyQt:
    - controller/pandasa.py menyediakan model tabel PandasModel yang digunakan untuk menampilkan data di GUI.
    - controller/workers.py memperbarui model tabel dengan data yang diambil dari API Gate.io.

Ekspor Data ke CSV:
    - controller/csv_handler.py menyediakan ExportWorker untuk mengekspor data dari model tabel ke file CSV.
    - MainWindow menghubungkan tombol ekspor di GUI dengan ExportWorker.

Antarmuka Pengguna:
    - ui/ui_main_window.py mendefinisikan antarmuka pengguna utama.
    - MainWindow mengatur model tabel, memulai pekerja untuk mengambil data, dan menangani interaksi pengguna.

======================Designer=================
pyuic5 -o ui/ui_main_window.py ui/main_window.ui
===============================================
=================INSTALL=======================
pyinstaller --onedir --windowed --clean main.py
===============================================