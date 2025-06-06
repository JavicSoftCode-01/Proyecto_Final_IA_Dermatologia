# utils\logger.py

"""
Módulo de registro personalizado para la aplicación.
Este módulo proporciona una clase `CustomLogger` que permite registrar mensajes
con diferentes niveles de severidad (éxito, información, advertencia y error).
con un formato y colores específicos para mejorar la legibilidad en la consola.
"""

import logging
import sys

# Colores ANSI para consola
RESET = "\033[0m"
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"

# Emojis
EMOJIS = {
    'SUCCESS': '🟢✨',
    'INFO': '🔵ℹ️',
    'WARNING': '🟡⚠️',
    'ERROR': '🔴❌',
}

COLORS = {
    'SUCCESS': GREEN,
    'INFO': BLUE,
    'WARNING': YELLOW,
    'ERROR': RED,
}

class CustomLogger:
    def __init__(self, name=__name__):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log(self, level, origin, message):
        color = COLORS.get(level, '')
        emoji = EMOJIS.get(level, '')
        log_message = f"\n{color}{emoji} [{level}] {origin}: {message}{RESET}\n"
        if level == 'ERROR':
            self.logger.error(log_message)
        elif level == 'WARNING':
            self.logger.warning(log_message)
        elif level == 'SUCCESS':
            self.logger.info(log_message)
        else:
            self.logger.info(log_message)

    def success(self, origin, message):
        self.log('SUCCESS', origin, message)

    def info(self, origin, message):
        self.log('INFO', origin, message)

    def warning(self, origin, message):
        self.log('WARNING', origin, message)

    def error(self, origin, message):
        self.log('ERROR', origin, message)

    def debug(self, origin, message):
        self.log('INFO', origin, f"[DEBUG] {message}")

logger = CustomLogger()
