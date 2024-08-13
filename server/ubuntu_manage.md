Buat Virtual Environment
python3 -m venv venv

Aktifkan Virtual Environment
source venv/bin/activate

Install Dependensi
pip install -r requirements.txt

Menonaktifkan Virtual Environment
deactivate

Reload systemd dan Aktifkan Service:

    Reload systemd
    sudo systemctl daemon-reload

    Aktifkan Service agar Berjalan Otomatis Saat Boot:
    sudo systemctl enable api_server.service

    Mulai Service:
    sudo systemctl start api_server.service

    Memeriksa Status:
    sudo systemctl status api_server.service

    Restart Service:
    sudo systemctl restart api_server.service

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


#mengubah timezone pada server Linux
    1. Periksa Timezone Saat Ini:
        timedatectl

    2. Daftar Timezone yang Tersedia:
        timedatectl list-timezones
        timedatectl list-timezones | grep Asia

    3. Ubah Timezone:
        sudo timedatectl set-timezone <timezone>
        sudo timedatectl set-timezone Asia/Jakarta

    4. Verifikasi Perubahan:
        timedatectl

    5. Sinkronisasi Waktu (Opsional):
        sudo timedatectl set-ntp true