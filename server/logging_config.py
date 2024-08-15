import logging
import os
from logging.handlers import RotatingFileHandler

def configure_logging(logger_name, log_file, level=logging.DEBUG, max_bytes=1024*1024*5, backup_count=1):
    """
    Mengonfigurasi logger dengan file handler yang berotasi dan console handler.

    :param logger_name: Nama dari logger.
    :param log_file: Lokasi file log.
    :param level: Level logging (default: logging.DEBUG).
    :param max_bytes: Ukuran maksimum file log sebelum berotasi (default: 5MB).
    :param backup_count: Jumlah maksimum file log backup yang disimpan (default: 5).
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    if not logger.handlers:
        # Pastikan direktori log ada
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # File handler dengan rotasi
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # Menambahkan handlers ke logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
