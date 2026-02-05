"""
Configuración centralizada del sistema SURTHILANAS
Carga variables de entorno y configuraciones globales
"""

import os
from dotenv import load_dotenv
from typing import List

# Cargar variables de entorno
load_dotenv()

class Config:
    """Clase de configuración centralizada"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    AUTHORIZED_USERS: List[int] = [
        int(user_id.strip()) 
        for user_id in os.getenv('AUTHORIZED_USERS', '').split(',') 
        if user_id.strip()
    ]
    
    # Google Drive
    GOOGLE_CREDENTIALS_FILE: str = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    VENTAS_SHEET_ID: str = os.getenv('VENTAS_SHEET_ID', '')
    GASTOS_SHEET_ID: str = os.getenv('GASTOS_SHEET_ID', '')
    
    # General
    TIMEZONE: str = os.getenv('TIMEZONE', 'America/Bogota')
    MONEDA: str = os.getenv('MONEDA', 'COP')
    LOCALE: str = os.getenv('LOCALE', 'es_CO')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'surthilanas_bot.log')
    
    # Categorías de gastos predefinidas
    CATEGORIAS_GASTOS = [
        'Servicios públicos',
        'Nómina',
        'Materia prima',
        'Transporte',
        'Marketing',
        'Mantenimiento',
        'Otros'
    ]
    
    # Medios de pago aceptados
    MEDIOS_PAGO = [
        'Efectivo',
        'Transferencia',
        'Tarjeta débito',
        'Tarjeta crédito',
        'Cheque',
        'Otro'
    ]
    
    @classmethod
    def validate(cls) -> bool:
        """Valida que las configuraciones críticas estén presentes"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN no está configurado")
        if not cls.AUTHORIZED_USERS:
            raise ValueError("AUTHORIZED_USERS no está configurado")
        if not cls.VENTAS_SHEET_ID or not cls.GASTOS_SHEET_ID:
            raise ValueError("IDs de Google Sheets no están configurados")
        return True

# Validar configuración al importar
try:
    Config.validate()
except ValueError as e:
    print(f"⚠️  ADVERTENCIA: {e}")
    print("Por favor, configura el archivo .env correctamente")
