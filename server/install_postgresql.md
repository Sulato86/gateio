# INSTALL PostgreSQL
1. Perbarui Sistem
    
    sudo apt update
    sudo apt upgrade

2. Instal PostgreSQL

    sudo apt install postgresql postgresql-contrib
    sudo apt-get install build-essential libpq-dev python3-dev

3. Mulai dan Aktifkan Layanan PostgreSQL

    sudo systemctl status postgresql
    sudo systemctl enable postgresql

4. Konfigurasi Awal PostgreSQL

    sudo -i -u postgres
    psql

5. Membuat Pengguna dan Basis Data

    CREATE USER nama_pengguna WITH PASSWORD 'kata_sandi';
    CREATE DATABASE nama_database OWNER nama_pengguna;

6. Mengatur Hak Akses

    GRANT ALL PRIVILEGES ON DATABASE nama_database TO nama_pengguna;

7. Akses dari Jarak Jauh (Opsional)

    sudo nano /etc/postgresql/14/main/postgresql.conf

    Temukan dan ubah baris berikut:
    #listen_addresses = 'localhost'

    Menjadi:
    listen_addresses = '*'

    Edit file pg_hba.conf untuk mengizinkan koneksi dari IP tertentu:
    sudo nano /etc/postgresql/14/main/pg_hba.conf

    Tambahkan baris berikut:
    host    all             all             0.0.0.0/0               md5

    Restart PostgreSQL untuk menerapkan perubahan:
    sudo systemctl restart postgresql

8. Ganti password user 'postgres'

    1. Masuk ke Shell PostgreSQL sebagai Pengguna postgres
    sudo -i -u postgres
    psql

    2. Ganti Password Pengguna postgres
    ALTER USER postgres WITH PASSWORD 'kata_sandi_baru';

    3. Keluar dari Shell PostgreSQL
    \q

    4. Verifikasi Perubahan
    psql -U postgres
    Kemudian, Anda akan diminta untuk memasukkan password baru yang telah Anda tetapkan.