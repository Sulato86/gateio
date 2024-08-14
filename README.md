1. Data Retrieval (Pengambilan Data Pasar)
API Integration: Core engine harus dapat berinteraksi dengan API dari bursa (misalnya Binance, Coinbase, atau lainnya) untuk mengambil data pasar secara real-time. Data ini biasanya mencakup harga terakhir (ticker), order book (kedalaman pasar), volume perdagangan, dan data lainnya yang relevan.
WebSocket: Untuk mendapatkan data yang lebih cepat dan real-time, core engine dapat menggunakan WebSocket daripada polling API REST. WebSocket memungkinkan robot trading untuk menerima data pasar langsung begitu ada perubahan.
2. Market Data Processing (Pengolahan Data Pasar)
Preprocessing: Data yang diambil dari bursa mungkin memerlukan preprocessing, seperti normalisasi atau penghapusan outlier, sebelum dapat digunakan oleh algoritma.
Technical Indicators: Core engine dapat menghitung berbagai indikator teknikal seperti Moving Averages, RSI (Relative Strength Index), MACD (Moving Average Convergence Divergence), Bollinger Bands, dan lainnya. Indikator ini membantu dalam pengambilan keputusan trading.
Signal Generation: Berdasarkan data pasar yang telah diproses dan indikator teknikal, core engine akan menghasilkan sinyal trading, seperti sinyal untuk membeli, menjual, atau tidak melakukan apa-apa.
3. Strategy Execution (Eksekusi Strategi)
Trading Strategy Implementation: Komponen ini mengimplementasikan strategi trading yang sudah ditentukan sebelumnya. Strategi bisa berupa aturan yang sederhana (misalnya beli ketika RSI di bawah 30, jual ketika di atas 70) atau bisa menjadi lebih kompleks, melibatkan algoritma machine learning atau model matematika.
Risk Management: Core engine harus memiliki komponen manajemen risiko untuk menentukan jumlah modal yang akan diperdagangkan, menetapkan stop-loss, dan take-profit untuk membatasi kerugian dan mengunci keuntungan.
Position Sizing: Menentukan ukuran posisi yang sesuai berdasarkan risiko yang telah ditetapkan dan modal yang tersedia.
4. Order Execution (Eksekusi Order)
Order Placement: Setelah sinyal trading dihasilkan, core engine akan menempatkan order ke bursa. Ini bisa berupa market order (eksekusi segera pada harga pasar saat ini) atau limit order (eksekusi pada harga tertentu).
Order Management: Core engine juga harus mampu mengelola order yang sedang berjalan, seperti membatalkan order yang belum tereksekusi atau menyesuaikan order yang sudah ada berdasarkan kondisi pasar yang berubah.
Slippage Management: Saat eksekusi order, core engine perlu mempertimbangkan slippage, yaitu perbedaan antara harga yang diharapkan dan harga eksekusi sebenarnya. Ini sangat penting dalam pasar yang bergerak cepat.
5. Risk and Money Management (Manajemen Risiko dan Modal)
Stop-Loss and Take-Profit: Menetapkan level stop-loss untuk meminimalkan kerugian jika pasar bergerak melawan posisi, dan take-profit untuk mengamankan keuntungan saat target tercapai.
Position Sizing: Menentukan seberapa besar modal yang akan diperdagangkan dalam setiap transaksi berdasarkan risiko yang telah ditetapkan.
Portfolio Management: Mengelola keseluruhan portofolio untuk memastikan diversifikasi dan untuk memantau eksposur terhadap risiko tertentu.
6. Backtesting (Pengujian Kembali)
Historical Data: Sebelum strategi trading diterapkan di pasar nyata, strategi tersebut harus diuji menggunakan data historis untuk melihat bagaimana performanya di masa lalu.
Performance Metrics: Setelah backtesting, core engine harus dapat menghitung metrik performa seperti Sharpe ratio, drawdown, win rate, dan lain-lain untuk mengevaluasi efektivitas strategi.
7. Real-Time Monitoring (Pemantauan Waktu Nyata)
Market Conditions: Core engine harus memantau kondisi pasar secara terus-menerus untuk mendeteksi perubahan yang mungkin memerlukan penyesuaian strategi atau pengambilan keputusan yang berbeda.
Health Monitoring: Pemantauan kesehatan sistem, termasuk latensi dalam mendapatkan data pasar, keberhasilan eksekusi order, dan stabilitas koneksi ke bursa.
8. Logging and Reporting (Pencatatan dan Pelaporan)
Trade Logging: Setiap transaksi yang dilakukan oleh robot harus dicatat dengan detail untuk keperluan audit dan analisis performa.
Error Handling and Logging: Core engine harus mencatat setiap kesalahan atau masalah yang terjadi selama operasi, sehingga dapat dianalisis dan diperbaiki.
Reporting: Laporan berkala mengenai performa trading, profit/loss, dan status portofolio untuk memberikan gambaran menyeluruh kepada pengguna.
9. Adaptation and Learning (Adaptasi dan Pembelajaran)
Machine Learning: Jika menggunakan machine learning, core engine harus memiliki kemampuan untuk memperbarui model berdasarkan data baru dan mengadaptasi strategi trading secara dinamis.
Strategy Optimization: Berdasarkan performa trading yang lalu, core engine bisa menyesuaikan parameter strategi untuk mengoptimalkan hasil di masa mendatang.
10. Security and Compliance (Keamanan dan Kepatuhan)
API Key Management: Mengelola kunci API dengan aman, memastikan bahwa kunci API dienkripsi dan tidak mudah diakses oleh pihak yang tidak berwenang.
Regulatory Compliance: Memastikan bahwa semua aktivitas trading mematuhi peraturan yang berlaku, seperti pencatatan yang benar untuk keperluan pajak dan kepatuhan hukum.





======================Designer=================
pyuic5 -o ui/ui_main_window.py ui/main_window.ui
pyuic5 -o server/server_control.py server/server_control.ui
===============================================
=================INSTALL=======================
pyinstaller --onedir --windowed --clean main_window.py
===============================================
==================FLOWCHART====================
pyreverse -o plantuml -p full -A .
