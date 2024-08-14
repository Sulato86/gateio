# Mengatur journal log

    Melihat Log:
    sudo journalctl -u api_server.service

    Mengedit File Konfigurasi journald:
    sudo nano /etc/systemd/journald.conf

    Tambahkan atau Ubah Pengaturan:
    [Journal]
    SystemMaxUse=1G
    MaxRetentionSec=2week
    SystemMaxFileSize=100M

    Restart systemd-journald:
    sudo systemctl restart systemd-journald

    Perintah untuk Menghapus Log Lebih Tua dari 2 Jam:
    sudo journalctl --vacuum-time=2h


# mengubah timezone pada server Linux
    1. Periksa Timezone Saat Ini:
        timedatectl

    2. Daftar Timezone yang Tersedia:
        timedatectl list-timezones
        timedatectl list-timezones | grep Asia

    3. Ubah Timezone:
        sudo timedatectl set-timezone <timezone>
        sudo timedatectl set-timezone Asia/Singapore

    4. Verifikasi Perubahan:
        timedatectl

    5. Sinkronisasi Waktu (Opsional):
        sudo timedatectl set-ntp true

# Install Anaconda

    download anaconda:
    wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh

    Aktifkan Anaconda:
    source ~/anaconda3/bin/activate

    Membuat Environment Baru:
    conda create --name nama_environment python=3.12

    Aktifkan Environtment Baru:
    conda activate nama_environment

    install dependencies untuk psycopg2
    sudo apt-get install build-essential libpq-dev python3-dev
    
    Install package library
    pip install -r requirements.txt

    # non anaconda
    Aktifkan Virtual Environment
    source venv/bin/activate

    Install Dependensi
    pip install -r requirements.txt

    Menonaktifkan Virtual Environment
    deactivate

# Systemd
    copy api_server.service ke /etc/systemd/system

    Reload systemd
    sudo systemctl daemon-reload

    Aktifkan Service agar Berjalan Otomatis Saat Boot:
    sudo systemctl enable api_server.service

    Mulai Service:
    sudo systemctl start api_server.service

    Stop Service:
    sudo systemctl stop api_server.service

    Memeriksa Status:
    sudo systemctl status api_server.service

    Restart Service:
    sudo systemctl restart api_server.service

# Redis untuk celery

    Test redis;
    redis-cli ping

    Menjalankan Redis;
    redis-server

    Install Redis Tools;
    apt install redis-tools

    Install Redis Server;
    sudo apt install redis-server

    Menjalankan celery;
    celery -A tasks worker --loglevel=info

# Worker Celery

    Melihat Worker Celery yang Sedang Berjalan;
    Menggunakan Perintah ps
    ps aux | grep 'celery worker'

    Menggunakan pgrep
    pgrep -f 'celery worker'

    Menghentikan dengan pkill
    pkill -f 'celery worker'

    Menghentikan dengan kill
    kill <PID>
