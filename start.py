#!/usr/bin/env python3
"""
Script de verificación e inicio del Bot SURTHILANAS
Verifica que todo esté configurado correctamente antes de iniciar el bot
"""

import os
import sys
from pathlib import Path

def print_header(text):
    """Imprime un encabezado formateado"""
    print("\n" + "="*50)
    print(f"  {text}")
    print("="*50)

def check_python_version():
    """Verifica la versión de Python"""
    print_header("Verificando versión de Python")
    
    version = sys.version_info
    required = (3, 11)
    
    if version >= required:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro}")
        print(f"   Se requiere Python {required[0]}.{required[1]} o superior")
        return False

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print_header("Verificando dependencias")
    
    required_packages = [
        'telegram',
        'gspread',
        'google.oauth2',
        'dotenv',
        'pytz'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    if missing:
        print("\nPara instalar las dependencias faltantes:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Verifica que el archivo .env exista"""
    print_header("Verificando archivo .env")
    
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("\nPara crear el archivo .env:")
        print("1. Copia el archivo de ejemplo: cp .env.example .env")
        print("2. Edita .env con tus credenciales")
        return False
    
    print("✅ Archivo .env existe")
    return True

def check_env_variables():
    """Verifica las variables de entorno críticas"""
    print_header("Verificando variables de entorno")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Token del bot de Telegram',
        'AUTHORIZED_USERS': 'IDs de usuarios autorizados',
        'GOOGLE_CREDENTIALS_FILE': 'Archivo de credenciales de Google',
        'VENTAS_SHEET_ID': 'ID de la hoja de ventas',
        'GASTOS_SHEET_ID': 'ID de la hoja de gastos'
    }
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Ocultar parte del valor por seguridad
            if 'TOKEN' in var or 'ID' in var:
                display_value = value[:10] + "..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: No configurado ({description})")
            missing.append(var)
    
    if missing:
        print("\nConfigura las variables faltantes en el archivo .env")
        return False
    
    return True

def check_credentials_file():
    """Verifica que el archivo de credenciales de Google exista"""
    print_header("Verificando credenciales de Google")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    
    if not os.path.exists(credentials_file):
        print(f"❌ Archivo {credentials_file} no encontrado")
        print("\nPara obtener las credenciales:")
        print("1. Ve a Google Cloud Console")
        print("2. Crea una Service Account")
        print("3. Descarga el archivo JSON de credenciales")
        print(f"4. Renómbralo a {credentials_file}")
        return False
    
    print(f"✅ Archivo {credentials_file} existe")
    return True

def check_file_structure():
    """Verifica que los archivos necesarios existan"""
    print_header("Verificando estructura de archivos")
    
    required_files = [
        'bot.py',
        'config.py',
        'google_sheets.py',
        'utils.py',
        'requirements.txt'
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing.append(file)
    
    if missing:
        print("\nArchivos faltantes detectados")
        return False
    
    return True

def test_google_connection():
    """Intenta conectar con Google Sheets"""
    print_header("Probando conexión a Google Sheets")
    
    try:
        from google_sheets import sheets_manager
        print("✅ Conexión a Google Sheets exitosa")
        return True
    except Exception as e:
        print(f"❌ Error al conectar con Google Sheets: {e}")
        print("\nVerifica:")
        print("1. Las credenciales son válidas")
        print("2. Las APIs están habilitadas en Google Cloud")
        print("3. Las hojas están compartidas con la Service Account")
        return False

def run_all_checks():
    """Ejecuta todas las verificaciones"""
    print("\n" + "🤖 VERIFICACIÓN DEL SISTEMA SURTHILANAS ".center(50, "="))
    
    checks = [
        ("Versión de Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Archivo .env", check_env_file),
        ("Variables de entorno", check_env_variables),
        ("Credenciales de Google", check_credentials_file),
        ("Estructura de archivos", check_file_structure),
        ("Conexión Google Sheets", test_google_connection)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Error en verificación '{name}': {e}")
            results.append(False)
    
    print_header("RESUMEN")
    passed = sum(results)
    total = len(results)
    
    print(f"\nVerificaciones completadas: {passed}/{total}")
    
    if all(results):
        print("\n✅ ¡Todo listo! El sistema está configurado correctamente.")
        print("\nPara iniciar el bot, ejecuta:")
        print("  python bot.py")
        return True
    else:
        print("\n❌ Hay problemas que deben resolverse antes de iniciar el bot.")
        print("\nRevisa los errores indicados arriba y corrígelos.")
        return False

def start_bot():
    """Inicia el bot si todas las verificaciones pasan"""
    if run_all_checks():
        print("\n" + "="*50)
        response = input("\n¿Deseas iniciar el bot ahora? (s/n): ")
        if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            print("\n🚀 Iniciando bot de SURTHILANAS...\n")
            import bot
            bot.main()
        else:
            print("\nBot no iniciado. Puedes iniciarlo manualmente con:")
            print("  python bot.py")
    else:
        sys.exit(1)

if __name__ == '__main__':
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\n\n👋 Verificación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
