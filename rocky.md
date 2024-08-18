# Firewall

    Izinkan SSH (Port 22) untuk tetap dapat mengakses VPS:
    sudo firewall-cmd --permanent --add-service=ssh

    Izinkan HTTP dan HTTPS (Port 80 dan 443) untuk lalu lintas web:
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https

    Izinkan Port Lain yang Dibutuhkan:
    sudo firewall-cmd --permanent --add-port=8080/tcp

    Cek Konfigurasi Firewall
    sudo firewall-cmd --permanent --list-all

    Nonaktifkan Sementara Firewalld
    sudo systemctl stop firewalld
    sudo systemctl disable firewalld

# Install Postgresql
    
    # Install the repository RPM:
    sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm

    # Disable the built-in PostgreSQL module:
    sudo dnf -qy module disable postgresql

    # Install PostgreSQL:
    sudo dnf install -y postgresql16-server

    # Optionally initialize the database and enable automatic start:
    sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
    sudo systemctl enable postgresql-16
    sudo systemctl start postgresql-16

    # Akses PostgreSQL 16
    sudo -i -u postgres
    psql

    # Ganti Password Pengguna postgres
    ALTER USER postgres WITH PASSWORD 'kata_sandi_baru';

    # Akses remote (/var/lib/pgsql/16/data/)

    Edit postgresql.conf:
    listen_addresses = '*'

    Edit pg_hba.conf:
    host    all             all             0.0.0.0/0               md5

    # Restart postgresql
    sudo systemctl restart postgresql-16

# Install Anaconda

    download anaconda:
    wget https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh

    Aktifkan Anaconda:
    source ~/anaconda3/bin/activate

    Menambahkan PATH:
    echo 'export PATH="~/anaconda3/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc

    Membuat Environment Baru:
    conda create --name nama_environment python=3.12

    Aktifkan Environtment Baru:
    conda activate nama_environment

    List conda environment
    conda env list
    conda info --envs

    Mengubah environtment defaul
    nano ~/.bashrc
    Tambahkan
    conda activate myenv
    Terapkan Perubahan
    source ~/.bashrc
    
    Install package library
    pip install -r requirements.txt

    # non anaconda
    Aktifkan Virtual Environment
    source venv/bin/activate

    Install Dependensi
    pip install -r requirements.txt

    Menonaktifkan Virtual Environment
    deactivate

# Install Redis untuk celery

    Instal Redis
    sudo dnf install epel-release
    sudo dnf install redis

    Mulai dan Aktifkan Redis
    sudo systemctl start redis
    sudo systemctl enable redis

    Verifikasi Redis Berjalan dengan Benar
    sudo ss -plunt | grep 6379
    sudo systemctl status redis

    Test redis;
    redis-cli ping

    Cek Firewall
    sudo firewall-cmd --permanent --add-port=6379/tcp
    sudo firewall-cmd --reload

    Menjalankan Redis;
    redis-server

    Menjalankan celery;
    celery -A tasks worker --loglevel=info

    Install redis di environmen
    pip install -U redis
    pip install -U kombu celery

# Worker Celery

    Install celery
    pip install celery

    Melihat Worker Celery yang Sedang Berjalan;
    Menggunakan Perintah ps
    ps aux | grep 'celery worker'

    Menggunakan pgrep
    pgrep -f 'celery worker'

    Menghentikan dengan pkill
    pkill -f 'celery worker'

    Menghentikan dengan kill
    kill <PID>

# ws_gateio.py

    Start ws_gateio.py
    systemctl start ws_gateio