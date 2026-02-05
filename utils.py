"""
Módulo de utilidades y validaciones
Funciones auxiliares para el sistema
"""

from datetime import datetime
from typing import Optional, Tuple
import re
import pytz
from config import Config

def validar_fecha(fecha_str: str) -> Tuple[bool, Optional[str]]:
    """
    Valida y formatea una fecha
    
    Args:
        fecha_str: String con la fecha (puede ser 'hoy' o DD/MM/AAAA)
    
    Returns:
        Tuple[bool, Optional[str]]: (es_valida, fecha_formateada)
    """
    if fecha_str.lower() == 'hoy':
        tz = pytz.timezone(Config.TIMEZONE)
        return True, datetime.now(tz).strftime('%d/%m/%Y')
    
    # Validar formato DD/MM/AAAA
    patron = r'^\d{2}/\d{2}/\d{4}$'
    if not re.match(patron, fecha_str):
        return False, None
    
    try:
        # Intentar parsear la fecha
        datetime.strptime(fecha_str, '%d/%m/%Y')
        return True, fecha_str
    except ValueError:
        return False, None

def validar_monto(monto_str: str) -> Tuple[bool, Optional[float]]:
    """
    Valida y convierte un monto a float
    
    Args:
        monto_str: String con el monto
    
    Returns:
        Tuple[bool, Optional[float]]: (es_valido, monto_float)
    """
    try:
        # Remover separadores de miles y reemplazar coma por punto
        monto_limpio = monto_str.replace(',', '').replace('.', '')
        monto = float(monto_limpio)
        
        if monto <= 0:
            return False, None
        
        return True, monto
    except ValueError:
        return False, None

def formatear_monto(monto: float) -> str:
    """
    Formatea un monto para mostrar
    
    Args:
        monto: Monto numérico
    
    Returns:
        str: Monto formateado (ej: $1,250,000)
    """
    return f"${monto:,.0f}".replace(',', '.')

def validar_numero_factura(numero: str) -> bool:
    """
    Valida formato de número de factura
    
    Args:
        numero: Número de factura
    
    Returns:
        bool: True si es válido
    """
    # Debe tener al menos 1 carácter y máximo 20
    return len(numero) >= 1 and len(numero) <= 20

def normalizar_texto(texto: str, max_length: int = 200) -> str:
    """
    Normaliza y limita un texto
    
    Args:
        texto: Texto a normalizar
        max_length: Longitud máxima
    
    Returns:
        str: Texto normalizado
    """
    if not texto or texto.strip() == '-':
        return '-'
    return texto.strip()[:max_length]

def es_usuario_autorizado(user_id: int) -> bool:
    """
    Verifica si un usuario está autorizado
    
    Args:
        user_id: ID del usuario de Telegram
    
    Returns:
        bool: True si está autorizado
    """
    return user_id in Config.AUTHORIZED_USERS

def obtener_rango_fechas(periodo: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Obtiene el rango de fechas para un período
    
    Args:
        periodo: 'hoy', 'semana', 'mes', o 'personalizado'
    
    Returns:
        Tuple[fecha_inicio, fecha_fin] en formato DD/MM/AAAA
    """
    tz = pytz.timezone(Config.TIMEZONE)
    hoy = datetime.now(tz)
    
    if periodo == 'hoy':
        fecha = hoy.strftime('%d/%m/%Y')
        return fecha, fecha
    
    elif periodo == 'semana':
        # Inicio de semana (lunes)
        inicio_semana = hoy - datetime.timedelta(days=hoy.weekday())
        return inicio_semana.strftime('%d/%m/%Y'), hoy.strftime('%d/%m/%Y')
    
    elif periodo == 'mes':
        # Primer día del mes
        inicio_mes = hoy.replace(day=1)
        return inicio_mes.strftime('%d/%m/%Y'), hoy.strftime('%d/%m/%Y')
    
    return None, None

def generar_resumen_financiero(totales: dict) -> str:
    """
    Genera un resumen financiero formateado
    
    Args:
        totales: Dict con datos financieros
    
    Returns:
        str: Resumen formateado
    """
    resumen = "📊 RESUMEN FINANCIERO\n"
    resumen += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    resumen += f"💰 Total Ventas: {formatear_monto(totales['total_ventas'])}\n"
    resumen += f"   ({totales['num_ventas']} registros)\n\n"
    
    resumen += f"💸 Total Gastos: {formatear_monto(totales['total_gastos'])}\n"
    resumen += f"   ({totales['num_gastos']} registros)\n\n"
    
    resumen += "━━━━━━━━━━━━━━━━━━━━\n"
    
    utilidad = totales['utilidad']
    if utilidad >= 0:
        resumen += f"✅ Utilidad: {formatear_monto(utilidad)}\n"
    else:
        resumen += f"⚠️ Pérdida: {formatear_monto(abs(utilidad))}\n"
    
    margen = totales['margen']
    resumen += f"📈 Margen: {margen:.1f}%\n"
    
    return resumen

def crear_mensaje_confirmacion(tipo: str, datos: dict) -> str:
    """
    Crea mensaje de confirmación antes de guardar
    
    Args:
        tipo: 'venta' o 'gasto'
        datos: Dict con los datos a guardar
    
    Returns:
        str: Mensaje de confirmación
    """
    if tipo == 'venta':
        msg = "✅ CONFIRMAR VENTA\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        msg += f"📅 Fecha: {datos.get('fecha')}\n"
        msg += f"📄 Factura: {datos.get('numero_factura')}\n"
        msg += f"👤 Cliente: {datos.get('cliente', '-')}\n"
        msg += f"💰 Monto: {formatear_monto(datos.get('monto', 0))}\n"
        msg += f"💳 Pago: {datos.get('medio_pago')}\n"
        msg += f"📝 Obs: {datos.get('observaciones', '-')}\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        msg += "¿Confirmas el registro? (Sí/No)"
    
    elif tipo == 'gasto':
        msg = "✅ CONFIRMAR GASTO\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        msg += f"📅 Fecha: {datos.get('fecha')}\n"
        msg += f"📂 Categoría: {datos.get('categoria')}\n"
        msg += f"🏢 Proveedor: {datos.get('proveedor', '-')}\n"
        msg += f"💰 Monto: {formatear_monto(datos.get('monto', 0))}\n"
        msg += f"💳 Pago: {datos.get('medio_pago')}\n"
        msg += f"📝 Obs: {datos.get('observaciones', '-')}\n"
        msg += "━━━━━━━━━━━━━━━━\n"
        msg += "¿Confirmas el registro? (Sí/No)"
    
    return msg
