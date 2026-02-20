"""
Bot de Telegram para SURTHILANAS
Sistema de registro financiero automatizado
"""

import logging
from functools import wraps
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from config import Config
from google_sheets import sheets_manager
from utils import (
    validar_fecha,
    validar_monto,
    validar_numero_factura,
    normalizar_texto,
    es_usuario_autorizado,
    formatear_monto,
    generar_resumen_financiero,
    crear_mensaje_confirmacion,
    obtener_rango_fechas,
    formatear_registro_venta,
    formatear_registro_gasto
)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL),
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Estados de conversación para VENTAS
VENTA_FECHA, VENTA_FACTURA, VENTA_CLIENTE, VENTA_MONTO, VENTA_PAGO, VENTA_OBS, VENTA_CONFIRMAR = range(7)

# Estados de conversación para GASTOS
GASTO_FECHA, GASTO_CATEGORIA, GASTO_PROVEEDOR, GASTO_MONTO, GASTO_PAGO, GASTO_OBS, GASTO_CONFIRMAR = range(7, 14)

# Estados de conversación para REPORTES
REPORTE_TIPO = 14

# Estados de conversación para BUSCAR VENTA
BUSCAR_VENTA_FACTURA, BUSCAR_VENTA_ACCION = range(15, 17)

# Estados de conversación para EDITAR VENTA
EDITAR_VENTA_CAMPO, EDITAR_VENTA_VALOR, EDITAR_VENTA_CONFIRMAR = range(17, 20)

# Estados de conversación para ELIMINAR (desde /eliminar)
ELIMINAR_TIPO = 20
ELIMINAR_CONFIRMAR = 21

# FIX BUG 4: Estado separado para eliminar desde /buscar
ELIMINAR_DESDE_BUSCAR = 29

# Estados de conversación para BUSCAR GASTO
BUSCAR_GASTO_CRITERIO, BUSCAR_GASTO_VALOR, BUSCAR_GASTO_SELECCION, BUSCAR_GASTO_ACCION = range(22, 26)

# Estados de conversación para EDITAR GASTO
EDITAR_GASTO_CAMPO, EDITAR_GASTO_VALOR, EDITAR_GASTO_CONFIRMAR = range(26, 29)


# FIX BUG 1: Decorador con @wraps para preservar __name__ de la función
# Sin esto, los ConversationHandlers no pueden identificar la función de entrada
def requiere_autorizacion(func):
    """Decorador que verifica si el usuario está autorizado"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not es_usuario_autorizado(user_id):
            await update.message.reply_text(
                "❌ No tienes autorización para usar este bot.\n"
                "Contacta al administrador del sistema."
            )
            logger.warning(f"Intento de acceso no autorizado: {user_id}")
            return ConversationHandler.END
        return await func(update, context)
    return wrapper

# ============================================
# COMANDOS BÁSICOS
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - Mensaje de bienvenida"""
    user = update.effective_user

    if not es_usuario_autorizado(user.id):
        await update.message.reply_text(
            "❌ No tienes autorización para usar este bot."
        )
        return

    mensaje = f"""
🏢 <b>SURTHILANAS - Sistema Financiero</b>

¡Hola {user.first_name}! 👋

Este bot te permite gestionar las finanzas de tu empresa de forma simple y eficiente.

<b>📋 Comandos disponibles:</b>

💰 <b>/venta</b> - Registrar una venta individual
📅 <b>/cierreday</b> - Registrar cierre total del día
💸 <b>/gasto</b> - Registrar un nuevo gasto
📊 <b>/reporte</b> - Ver reportes financieros
📈 <b>/estado</b> - Ver estado actual
🔍 <b>/buscar</b> - Buscar y editar una venta
🗑️ <b>/eliminar</b> - Eliminar último registro
🤖 <b>/analisis</b> - Análisis inteligente con IA
🔮 <b>/prediccion</b> - Predicción de ventas (ML)
🔍 <b>/anomalias</b> - Detectar transacciones atípicas
📈 <b>/tendencias</b> - Análisis de tendencias
💡 <b>/insights</b> - Recomendaciones inteligentes
❓ <b>/ayuda</b> - Ver esta ayuda
🚫 <b>/cancelar</b> - Cancelar operación actual

<b>Todos los datos se guardan automáticamente en Google Drive.</b>

¿Qué deseas hacer?
    """

    await update.message.reply_text(mensaje, parse_mode='HTML')

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /ayuda - Muestra información de ayuda"""
    mensaje = """
📖 <b>GUÍA DE USO</b>

<b>Registro de transacciones:</b>
💰 <b>/venta</b> - Registrar una venta individual (factura opcional)
📅 <b>/cierreday</b> - Registrar cierre total del día por medio de pago
💸 <b>/gasto</b> - Registrar un nuevo gasto

<b>Consultas y gestión:</b>
🔍 <b>/buscar</b> - Buscar y editar una venta por factura
🗑️ <b>/eliminar</b> - Eliminar último registro
📊 <b>/reporte</b> - Ver reportes financieros
📈 <b>/estado</b> - Ver estado actual del mes

<b>Análisis con Inteligencia Artificial:</b>
🤖 <b>/analisis</b> - Preguntas en lenguaje natural
🔮 <b>/prediccion</b> - Predicción de ventas con ML
🔍 <b>/anomalias</b> - Detectar transacciones atípicas
📈 <b>/tendencias</b> - Análisis temporal
💡 <b>/insights</b> - Recomendaciones personalizadas

<b>Otros:</b>
❓ <b>/ayuda</b> - Ver esta ayuda
🚫 <b>/cancelar</b> - Cancelar operación actual

<b>Consejos:</b>
• Puedes escribir 'hoy' para la fecha actual
• Los montos deben ser números positivos
• Usa /cancelar para detener cualquier operación
    """
    await update.message.reply_text(mensaje, parse_mode='HTML')

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela la operación actual"""
    await update.message.reply_text(
        "❌ Operación cancelada.\n"
        "Usa /start para ver los comandos disponibles.",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# FLUJO DE REGISTRO DE VENTAS
# ============================================

@requiere_autorizacion
async def venta_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el flujo de registro de venta"""
    await update.message.reply_text(
        "💰 <b>REGISTRO DE VENTA</b>\n\n"
        "Ingresa la fecha de la venta:\n"
        "• Escribe 'hoy' para usar la fecha actual\n"
        "• O ingresa en formato DD/MM/AAAA (ej: 15/01/2025)\n\n"
        "💡 <i>Para el cierre total del día usa /cierreday</i>",
        parse_mode='HTML'
    )
    return VENTA_FECHA

async def venta_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    fecha_input = update.message.text.strip()
    es_valida, fecha = validar_fecha(fecha_input)

    if not es_valida:
        await update.message.reply_text(
            "❌ Fecha inválida. Usa formato DD/MM/AAAA o escribe 'hoy'."
        )
        return VENTA_FECHA

    context.user_data['venta_fecha'] = fecha
    await update.message.reply_text(
        f"✅ Fecha: {fecha}\n\n"
        "Número de factura (opcional):\n"
        "• Ingresa el número o '-' para omitir"
    )
    return VENTA_FACTURA

async def venta_factura(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    numero = update.message.text.strip()

    # Factura es opcional: '-' o 's/n' la omite
    if numero in ['-', 's/n', 'S/N', 'sin', 'Sin']:
        numero = 'S/N'
    elif not validar_numero_factura(numero):
        await update.message.reply_text(
            "❌ Número de factura inválido (máximo 20 caracteres).\n"
            "Escribe el número o '-' para omitir."
        )
        return VENTA_FACTURA

    context.user_data['venta_factura'] = numero
    await update.message.reply_text(
        f"✅ Factura: {numero}\n\n"
        "Nombre del cliente (opcional):\n"
        "• Escribe el nombre o '-' para omitir"
    )
    return VENTA_CLIENTE

async def venta_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cliente = normalizar_texto(update.message.text)
    context.user_data['venta_cliente'] = cliente

    await update.message.reply_text(
        f"✅ Cliente: {cliente}\n\n"
        "Ingresa el monto de la venta (solo números):"
    )
    return VENTA_MONTO

async def venta_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    monto_input = update.message.text.strip()
    es_valido, monto = validar_monto(monto_input)

    if not es_valido:
        await update.message.reply_text(
            "❌ Monto inválido. Ingresa solo números positivos."
        )
        return VENTA_MONTO

    context.user_data['venta_monto'] = monto

    keyboard = [
        ['Efectivo', 'Transferencia'],
        ['Tarjeta débito', 'Tarjeta crédito'],
        ['Otro']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ Monto: {formatear_monto(monto)}\n\n"
        "Selecciona el medio de pago:",
        reply_markup=reply_markup
    )
    return VENTA_PAGO

async def venta_pago(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    medio_pago = update.message.text.strip()
    context.user_data['venta_pago'] = medio_pago

    await update.message.reply_text(
        f"✅ Medio de pago: {medio_pago}\n\n"
        "Observaciones (opcional):\n"
        "• Escribe un comentario o '-' para omitir",
        reply_markup=ReplyKeyboardRemove()
    )
    return VENTA_OBS

async def venta_observaciones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    observaciones = normalizar_texto(update.message.text)
    context.user_data['venta_obs'] = observaciones

    datos_venta = {
        'fecha': context.user_data['venta_fecha'],
        'numero_factura': context.user_data['venta_factura'],
        'cliente': context.user_data['venta_cliente'],
        'monto': context.user_data['venta_monto'],
        'medio_pago': context.user_data['venta_pago'],
        'observaciones': observaciones
    }

    mensaje_confirmacion = crear_mensaje_confirmacion('venta', datos_venta)

    keyboard = [['Sí', 'No']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(mensaje_confirmacion, reply_markup=reply_markup)
    return VENTA_CONFIRMAR

async def venta_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.strip().lower()

    if respuesta not in ['sí', 'si', 'yes', 's']:
        await update.message.reply_text(
            "❌ Venta cancelada.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    datos_venta = {
        'fecha': context.user_data['venta_fecha'],
        'numero_factura': context.user_data['venta_factura'],
        'cliente': context.user_data['venta_cliente'],
        'monto': context.user_data['venta_monto'],
        'medio_pago': context.user_data['venta_pago'],
        'observaciones': context.user_data['venta_obs']
    }

    exito = sheets_manager.registrar_venta(datos_venta)

    if exito:
        await update.message.reply_text(
            "✅ <b>Venta registrada exitosamente</b>\n\n"
            f"Factura: {datos_venta['numero_factura']}\n"
            f"Monto: {formatear_monto(datos_venta['monto'])}\n\n"
            "Usa /reporte para ver el resumen financiero.",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "❌ Error al guardar la venta. Intenta nuevamente.",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# FLUJO DE REGISTRO DE GASTOS
# ============================================

@requiere_autorizacion
async def gasto_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "💸 <b>REGISTRO DE GASTO</b>\n\n"
        "Ingresa la fecha del gasto:\n"
        "• Escribe 'hoy' para usar la fecha actual\n"
        "• O ingresa en formato DD/MM/AAAA",
        parse_mode='HTML'
    )
    return GASTO_FECHA

async def gasto_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    fecha_input = update.message.text.strip()
    es_valida, fecha = validar_fecha(fecha_input)

    if not es_valida:
        await update.message.reply_text(
            "❌ Fecha inválida. Usa formato DD/MM/AAAA o escribe 'hoy'."
        )
        return GASTO_FECHA

    context.user_data['gasto_fecha'] = fecha

    categorias = Config.CATEGORIAS_GASTOS
    keyboard = [[cat] for cat in categorias]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ Fecha: {fecha}\n\n"
        "Selecciona la categoría del gasto:",
        reply_markup=reply_markup
    )
    return GASTO_CATEGORIA

async def gasto_categoria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    categoria = update.message.text.strip()
    context.user_data['gasto_categoria'] = categoria

    await update.message.reply_text(
        f"✅ Categoría: {categoria}\n\n"
        "Nombre del proveedor (opcional):\n"
        "• Escribe el nombre o '-' para omitir",
        reply_markup=ReplyKeyboardRemove()
    )
    return GASTO_PROVEEDOR

async def gasto_proveedor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    proveedor = normalizar_texto(update.message.text)
    context.user_data['gasto_proveedor'] = proveedor

    await update.message.reply_text(
        f"✅ Proveedor: {proveedor}\n\n"
        "Ingresa el monto del gasto:"
    )
    return GASTO_MONTO

async def gasto_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    monto_input = update.message.text.strip()
    es_valido, monto = validar_monto(monto_input)

    if not es_valido:
        await update.message.reply_text(
            "❌ Monto inválido. Ingresa solo números positivos."
        )
        return GASTO_MONTO

    context.user_data['gasto_monto'] = monto

    keyboard = [
        ['Efectivo', 'Transferencia'],
        ['Tarjeta débito', 'Tarjeta crédito'],
        ['Otro']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ Monto: {formatear_monto(monto)}\n\n"
        "Selecciona el medio de pago:",
        reply_markup=reply_markup
    )
    return GASTO_PAGO

async def gasto_pago(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    medio_pago = update.message.text.strip()
    context.user_data['gasto_pago'] = medio_pago

    await update.message.reply_text(
        f"✅ Medio de pago: {medio_pago}\n\n"
        "Observaciones (opcional):\n"
        "• Escribe un comentario o '-' para omitir",
        reply_markup=ReplyKeyboardRemove()
    )
    return GASTO_OBS

async def gasto_observaciones(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    observaciones = normalizar_texto(update.message.text)
    context.user_data['gasto_obs'] = observaciones

    datos_gasto = {
        'fecha': context.user_data['gasto_fecha'],
        'categoria': context.user_data['gasto_categoria'],
        'proveedor': context.user_data['gasto_proveedor'],
        'monto': context.user_data['gasto_monto'],
        'medio_pago': context.user_data['gasto_pago'],
        'observaciones': observaciones
    }

    mensaje_confirmacion = crear_mensaje_confirmacion('gasto', datos_gasto)

    keyboard = [['Sí', 'No']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(mensaje_confirmacion, reply_markup=reply_markup)
    return GASTO_CONFIRMAR

async def gasto_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.strip().lower()

    if respuesta not in ['sí', 'si', 'yes', 's']:
        await update.message.reply_text(
            "❌ Gasto cancelado.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    datos_gasto = {
        'fecha': context.user_data['gasto_fecha'],
        'categoria': context.user_data['gasto_categoria'],
        'proveedor': context.user_data['gasto_proveedor'],
        'monto': context.user_data['gasto_monto'],
        'medio_pago': context.user_data['gasto_pago'],
        'observaciones': context.user_data['gasto_obs']
    }

    exito = sheets_manager.registrar_gasto(datos_gasto)

    if exito:
        await update.message.reply_text(
            "✅ <b>Gasto registrado exitosamente</b>\n\n"
            f"Categoría: {datos_gasto['categoria']}\n"
            f"Monto: {formatear_monto(datos_gasto['monto'])}\n\n"
            "Usa /reporte para ver el resumen financiero.",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "❌ Error al guardar el gasto. Intenta nuevamente.",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# REPORTES
# ============================================

@requiere_autorizacion
async def reporte_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ['Hoy', 'Esta semana'],
        ['Este mes', 'Todo']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "📊 <b>GENERAR REPORTE</b>\n\n"
        "Selecciona el período:",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return REPORTE_TIPO

async def reporte_generar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    periodo = update.message.text.strip().lower()

    fecha_inicio, fecha_fin = None, None
    titulo_periodo = ""

    if periodo == 'hoy':
        fecha_inicio, fecha_fin = obtener_rango_fechas('hoy')
        titulo_periodo = "HOY"
    elif periodo == 'esta semana':
        fecha_inicio, fecha_fin = obtener_rango_fechas('semana')
        titulo_periodo = "ESTA SEMANA"
    elif periodo == 'este mes':
        fecha_inicio, fecha_fin = obtener_rango_fechas('mes')
        titulo_periodo = "ESTE MES"
    else:
        titulo_periodo = "TOTAL"

    totales = sheets_manager.calcular_totales(fecha_inicio, fecha_fin)

    resumen = f"📊 <b>REPORTE - {titulo_periodo}</b>\n"
    resumen += "━━━━━━━━━━━━━━━━━━━━\n\n"
    resumen += f"💰 <b>Total Ventas:</b> {formatear_monto(totales['total_ventas'])}\n"
    resumen += f"   ({totales['num_ventas']} registros)\n\n"
    resumen += f"💸 <b>Total Gastos:</b> {formatear_monto(totales['total_gastos'])}\n"
    resumen += f"   ({totales['num_gastos']} registros)\n\n"
    resumen += "━━━━━━━━━━━━━━━━━━━━\n"

    if totales['utilidad'] >= 0:
        resumen += f"✅ <b>Utilidad:</b> {formatear_monto(totales['utilidad'])}\n"
    else:
        resumen += f"⚠️ <b>Pérdida:</b> {formatear_monto(abs(totales['utilidad']))}\n"

    resumen += f"📈 <b>Margen:</b> {totales['margen']:.1f}%"

    await update.message.reply_text(
        resumen,
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

@requiere_autorizacion
async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    totales = sheets_manager.calcular_totales(*obtener_rango_fechas('mes'))
    resumen = generar_resumen_financiero(totales)
    await update.message.reply_text(resumen)

# ============================================
# BUSCAR Y EDITAR VENTAS
# ============================================

@requiere_autorizacion
async def buscar_venta_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🔍 <b>BUSCAR VENTA</b>\n\n"
        "Ingresa el número de factura que deseas buscar:",
        parse_mode='HTML'
    )
    return BUSCAR_VENTA_FACTURA

async def buscar_venta_factura(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    numero_factura = update.message.text.strip()
    venta = sheets_manager.buscar_venta_por_factura(numero_factura)

    if not venta:
        await update.message.reply_text(
            f"❌ No se encontró ninguna venta con la factura: {numero_factura}\n\n"
            "Verifica el número e intenta con /buscar"
        )
        return ConversationHandler.END

    context.user_data['venta_encontrada'] = venta

    mensaje = formatear_registro_venta(venta)
    mensaje += "\n━━━━━━━━━━━━━━━━\n¿Qué deseas hacer?"

    keyboard = [['Editar', 'Eliminar'], ['Cancelar']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(mensaje, reply_markup=reply_markup)
    return BUSCAR_VENTA_ACCION

async def buscar_venta_accion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    accion = update.message.text.strip().lower()

    if accion == 'cancelar':
        await update.message.reply_text("❌ Operación cancelada", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    elif accion == 'editar':
        keyboard = [
            ['Fecha', 'Cliente'],
            ['Monto', 'Medio de pago'],
            ['Observaciones', 'Cancelar']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            "✏️ <b>EDITAR VENTA</b>\n\n¿Qué campo deseas editar?",
            parse_mode='HTML',
            reply_markup=reply_markup
        )
        return EDITAR_VENTA_CAMPO

    elif accion == 'eliminar':
        venta = context.user_data.get('venta_encontrada')
        keyboard = [['Sí, eliminar', 'No, cancelar']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        mensaje = "⚠️ <b>CONFIRMAR ELIMINACIÓN</b>\n\n"
        mensaje += "¿Estás seguro de que deseas eliminar esta venta?\n\n"
        mensaje += formatear_registro_venta(venta)
        mensaje += "\n⚠️ Esta acción no se puede deshacer."

        await update.message.reply_text(mensaje, parse_mode='HTML', reply_markup=reply_markup)
        context.user_data['eliminar_tipo'] = 'venta'
        context.user_data['registro_eliminar'] = venta
        # FIX BUG 4: usar estado separado para no colisionar con /eliminar
        return ELIMINAR_DESDE_BUSCAR

    return ConversationHandler.END

# FIX BUG 4: Handler de confirmación separado para eliminar desde /buscar
async def eliminar_desde_buscar_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.strip().lower()

    if 'no' in respuesta or 'cancelar' in respuesta:
        await update.message.reply_text("❌ Eliminación cancelada", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    registro = context.user_data.get('registro_eliminar')
    tipo = context.user_data.get('eliminar_tipo', 'venta')

    exito = sheets_manager.eliminar_registro(registro['fila'], tipo)

    if exito:
        await update.message.reply_text(
            f"✅ <b>{tipo.capitalize()} eliminada exitosamente</b>",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "❌ Error al eliminar el registro. Intenta nuevamente.",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END

async def editar_venta_campo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    campo = update.message.text.strip().lower()

    if campo == 'cancelar':
        await update.message.reply_text("❌ Edición cancelada", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    campo_map = {
        'fecha': 'fecha',
        'cliente': 'cliente',
        'monto': 'monto',
        'medio de pago': 'medio_pago',
        'observaciones': 'observaciones'
    }

    if campo not in campo_map:
        await update.message.reply_text("❌ Campo no válido. Intenta nuevamente.")
        return EDITAR_VENTA_CAMPO

    context.user_data['campo_editar'] = campo_map[campo]
    context.user_data['campo_nombre'] = campo

    venta = context.user_data.get('venta_encontrada')
    valor_actual = venta.get(campo_map[campo], '-')

    await update.message.reply_text(
        f"Valor actual de <b>{campo}</b>: {valor_actual}\n\n"
        f"Ingresa el nuevo valor para <b>{campo}</b>:",
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    return EDITAR_VENTA_VALOR

async def editar_venta_valor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nuevo_valor = update.message.text.strip()
    campo = context.user_data.get('campo_editar')

    if campo == 'fecha':
        es_valida, fecha = validar_fecha(nuevo_valor)
        if not es_valida:
            await update.message.reply_text("❌ Fecha inválida. Intenta nuevamente:")
            return EDITAR_VENTA_VALOR
        nuevo_valor = fecha

    elif campo == 'monto':
        es_valido, monto = validar_monto(nuevo_valor)
        if not es_valido:
            await update.message.reply_text("❌ Monto inválido. Intenta nuevamente:")
            return EDITAR_VENTA_VALOR
        nuevo_valor = monto

    elif campo in ['cliente', 'observaciones']:
        nuevo_valor = normalizar_texto(nuevo_valor)

    context.user_data['nuevo_valor'] = nuevo_valor

    venta = context.user_data.get('venta_encontrada').copy()
    venta[campo] = nuevo_valor

    mensaje = crear_mensaje_confirmacion('venta', venta)
    mensaje = mensaje.replace("CONFIRMAR VENTA", "CONFIRMAR CAMBIOS")
    mensaje = mensaje.replace("¿Confirmas el registro?", "¿Confirmas los cambios?")

    keyboard = [['Sí', 'No']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(mensaje, reply_markup=reply_markup)
    return EDITAR_VENTA_CONFIRMAR

async def editar_venta_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.strip().lower()

    if respuesta not in ['sí', 'si', 'yes', 's']:
        await update.message.reply_text("❌ Cambios cancelados", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    venta = context.user_data.get('venta_encontrada')
    campo = context.user_data.get('campo_editar')
    nuevo_valor = context.user_data.get('nuevo_valor')
    venta[campo] = nuevo_valor

    exito = sheets_manager.editar_venta(venta['fila'], venta)

    if exito:
        await update.message.reply_text(
            "✅ <b>Venta editada exitosamente</b>\n\n"
            f"Campo modificado: {context.user_data.get('campo_nombre')}\n"
            f"Nuevo valor: {formatear_monto(nuevo_valor) if campo == 'monto' else nuevo_valor}",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "❌ Error al guardar los cambios. Intenta nuevamente.",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# ELIMINAR ÚLTIMO REGISTRO
# ============================================

@requiere_autorizacion
async def eliminar_ultimo_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [['Última venta', 'Último gasto'], ['Cancelar']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🗑️ <b>ELIMINAR REGISTRO</b>\n\n¿Qué deseas eliminar?",
        parse_mode='HTML',
        reply_markup=reply_markup
    )
    return ELIMINAR_TIPO

async def eliminar_tipo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    opcion = update.message.text.strip().lower()

    if opcion == 'cancelar':
        await update.message.reply_text("❌ Operación cancelada", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    tipo = 'venta' if 'venta' in opcion else 'gasto'
    registro = sheets_manager.obtener_ultimo_registro(tipo)

    if not registro:
        await update.message.reply_text(
            f"❌ No hay registros de {tipo}s para eliminar",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    context.user_data['registro_eliminar'] = registro
    context.user_data['eliminar_tipo'] = tipo

    mensaje = formatear_registro_venta(registro) if tipo == 'venta' else formatear_registro_gasto(registro)

    keyboard = [['Sí, eliminar', 'No, cancelar']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    confirmacion = "⚠️ <b>CONFIRMAR ELIMINACIÓN</b>\n\n"
    confirmacion += "¿Estás seguro de eliminar este registro?\n\n"
    confirmacion += mensaje
    confirmacion += "\n⚠️ Esta acción no se puede deshacer."

    await update.message.reply_text(confirmacion, parse_mode='HTML', reply_markup=reply_markup)
    return ELIMINAR_CONFIRMAR

async def eliminar_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.strip().lower()

    if 'no' in respuesta or 'cancelar' in respuesta:
        await update.message.reply_text("❌ Eliminación cancelada", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return ConversationHandler.END

    registro = context.user_data.get('registro_eliminar')
    tipo = context.user_data.get('eliminar_tipo')

    exito = sheets_manager.eliminar_registro(registro['fila'], tipo)

    if exito:
        await update.message.reply_text(
            f"✅ <b>{tipo.capitalize()} eliminada exitosamente</b>",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "❌ Error al eliminar el registro. Intenta nuevamente.",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# FLUJO DE CIERRE DIARIO DE VENTAS (/cierreday)
# ============================================

# Estados para cierre diario (desde 31 para no colisionar)
CDAY_FECHA = 31
CDAY_EFECTIVO = 32
CDAY_TRANSFERENCIA = 33
CDAY_TARJETA_DEB = 34
CDAY_TARJETA_CRED = 35
CDAY_OTRO = 36
CDAY_OBS = 37
CDAY_CONFIRMAR = 38

MEDIOS_CIERRE = ['Efectivo', 'Transferencia', 'Tarjeta débito', 'Tarjeta crédito', 'Otro']

@requiere_autorizacion
async def cierreday_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el flujo de cierre diario de ventas"""
    await update.message.reply_text(
        "📅 <b>CIERRE DE VENTAS DEL DÍA</b>\n\n"
        "Registra el total de ventas del día desglosado por medio de pago.\n\n"
        "Ingresa la fecha del cierre:\n"
        "• Escribe 'hoy' para usar la fecha actual\n"
        "• O ingresa en formato DD/MM/AAAA",
        parse_mode='HTML'
    )
    return CDAY_FECHA

async def cierreday_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    fecha_input = update.message.text.strip()
    es_valida, fecha = validar_fecha(fecha_input)

    if not es_valida:
        await update.message.reply_text(
            "❌ Fecha inválida. Usa formato DD/MM/AAAA o escribe 'hoy'."
        )
        return CDAY_FECHA

    context.user_data['cday_fecha'] = fecha
    context.user_data['cday_montos'] = {}

    await update.message.reply_text(
        f"✅ Fecha: {fecha}\n\n"
        "💵 <b>Ventas en EFECTIVO:</b>\n"
        "• Ingresa el monto o '0' si no hubo",
        parse_mode='HTML'
    )
    return CDAY_EFECTIVO

async def cierreday_efectivo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    if texto == '0':
        monto = 0.0
    else:
        es_valido, monto = validar_monto(texto)
        if not es_valido:
            await update.message.reply_text("❌ Monto inválido. Ingresa un número o '0'.")
            return CDAY_EFECTIVO

    context.user_data['cday_montos']['Efectivo'] = monto

    await update.message.reply_text(
        f"✅ Efectivo: {formatear_monto(monto)}\n\n"
        "🔄 <b>Ventas por TRANSFERENCIA:</b>\n"
        "• Ingresa el monto o '0' si no hubo",
        parse_mode='HTML'
    )
    return CDAY_TRANSFERENCIA

async def cierreday_transferencia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    if texto == '0':
        monto = 0.0
    else:
        es_valido, monto = validar_monto(texto)
        if not es_valido:
            await update.message.reply_text("❌ Monto inválido. Ingresa un número o '0'.")
            return CDAY_TRANSFERENCIA

    context.user_data['cday_montos']['Transferencia'] = monto

    await update.message.reply_text(
        f"✅ Transferencia: {formatear_monto(monto)}\n\n"
        "💳 <b>Ventas con TARJETA DÉBITO:</b>\n"
        "• Ingresa el monto o '0' si no hubo",
        parse_mode='HTML'
    )
    return CDAY_TARJETA_DEB

async def cierreday_tarjeta_deb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    if texto == '0':
        monto = 0.0
    else:
        es_valido, monto = validar_monto(texto)
        if not es_valido:
            await update.message.reply_text("❌ Monto inválido. Ingresa un número o '0'.")
            return CDAY_TARJETA_DEB

    context.user_data['cday_montos']['Tarjeta débito'] = monto

    await update.message.reply_text(
        f"✅ Tarjeta débito: {formatear_monto(monto)}\n\n"
        "💳 <b>Ventas con TARJETA CRÉDITO:</b>\n"
        "• Ingresa el monto o '0' si no hubo",
        parse_mode='HTML'
    )
    return CDAY_TARJETA_CRED

async def cierreday_tarjeta_cred(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    if texto == '0':
        monto = 0.0
    else:
        es_valido, monto = validar_monto(texto)
        if not es_valido:
            await update.message.reply_text("❌ Monto inválido. Ingresa un número o '0'.")
            return CDAY_TARJETA_CRED

    context.user_data['cday_montos']['Tarjeta crédito'] = monto

    await update.message.reply_text(
        f"✅ Tarjeta crédito: {formatear_monto(monto)}\n\n"
        "🔹 <b>Otros medios de pago:</b>\n"
        "• Ingresa el monto o '0' si no hubo",
        parse_mode='HTML'
    )
    return CDAY_OTRO

async def cierreday_otro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    if texto == '0':
        monto = 0.0
    else:
        es_valido, monto = validar_monto(texto)
        if not es_valido:
            await update.message.reply_text("❌ Monto inválido. Ingresa un número o '0'.")
            return CDAY_OTRO

    context.user_data['cday_montos']['Otro'] = monto

    await update.message.reply_text(
        f"✅ Otros: {formatear_monto(monto)}\n\n"
        "📝 Observaciones del día (opcional):\n"
        "• Escribe un comentario o '-' para omitir",
        parse_mode='HTML'
    )
    return CDAY_OBS

async def cierreday_obs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    obs = normalizar_texto(update.message.text)
    context.user_data['cday_obs'] = obs

    montos = context.user_data['cday_montos']
    total = sum(montos.values())
    fecha = context.user_data['cday_fecha']

    # Construir mensaje de confirmación
    msg = "📅 <b>CONFIRMAR CIERRE DEL DÍA</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"📅 Fecha: {fecha}\n\n"
    msg += "<b>Desglose por medio de pago:</b>\n"

    for medio, monto in montos.items():
        if monto > 0:
            msg += f"  • {medio}: {formatear_monto(monto)}\n"

    msg += f"\n💰 <b>TOTAL DEL DÍA: {formatear_monto(total)}</b>\n"
    msg += f"📝 Obs: {obs}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += "¿Confirmas el cierre? (Sí/No)"

    keyboard = [['Sí', 'No']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(msg, parse_mode='HTML', reply_markup=reply_markup)
    return CDAY_CONFIRMAR

async def cierreday_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    respuesta = update.message.text.strip().lower()

    if respuesta not in ['sí', 'si', 'yes', 's']:
        await update.message.reply_text(
            "❌ Cierre cancelado.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END

    montos = context.user_data['cday_montos']
    total = sum(montos.values())
    fecha = context.user_data['cday_fecha']
    obs = context.user_data['cday_obs']

    datos_cierre = {
        'fecha': fecha,
        'efectivo': montos.get('Efectivo', 0),
        'transferencia': montos.get('Transferencia', 0),
        'tarjeta_debito': montos.get('Tarjeta débito', 0),
        'tarjeta_credito': montos.get('Tarjeta crédito', 0),
        'otro': montos.get('Otro', 0),
        'total': total,
        'observaciones': obs
    }

    exito = sheets_manager.registrar_cierre_diario(datos_cierre)

    if exito:
        msg = "✅ <b>Cierre del día registrado exitosamente</b>\n\n"
        msg += f"📅 Fecha: {fecha}\n"
        for medio, monto in montos.items():
            if monto > 0:
                msg += f"  • {medio}: {formatear_monto(monto)}\n"
        msg += f"\n💰 <b>Total: {formatear_monto(total)}</b>\n\n"
        msg += "Usa /reporte para ver el resumen financiero."

        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text(
            "❌ Error al guardar el cierre. Intenta nuevamente.",
            reply_markup=ReplyKeyboardRemove()
        )

    context.user_data.clear()
    return ConversationHandler.END

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main() -> None:
    """Inicializa y ejecuta el bot"""

    # FIX BUG 6 y 7: Inicializar el módulo ML e integrar sus handlers
    from bot_ml_funciones import inicializar_analizador_ml, obtener_handlers_ml
    import os

    excel_path = os.getenv('EXCEL_DATA_PATH', 'data/IF_surthilanas_año_2024.xlsx')
    if not inicializar_analizador_ml(excel_path):
        logger.warning("⚠️  Módulo ML no disponible. Los comandos /analisis, /prediccion, etc. estarán deshabilitados.")

    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Handlers básicos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("estado", estado))

    # Conversation Handler: VENTAS
    conv_venta = ConversationHandler(
        entry_points=[CommandHandler("venta", venta_inicio)],
        states={
            VENTA_FECHA:     [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_fecha)],
            VENTA_FACTURA:   [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_factura)],
            VENTA_CLIENTE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_cliente)],
            VENTA_MONTO:     [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_monto)],
            VENTA_PAGO:      [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_pago)],
            VENTA_OBS:       [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_observaciones)],
            VENTA_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversation Handler: GASTOS
    conv_gasto = ConversationHandler(
        entry_points=[CommandHandler("gasto", gasto_inicio)],
        states={
            GASTO_FECHA:      [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_fecha)],
            GASTO_CATEGORIA:  [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_categoria)],
            GASTO_PROVEEDOR:  [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_proveedor)],
            GASTO_MONTO:      [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_monto)],
            GASTO_PAGO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_pago)],
            GASTO_OBS:        [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_observaciones)],
            GASTO_CONFIRMAR:  [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversation Handler: REPORTES
    conv_reporte = ConversationHandler(
        entry_points=[CommandHandler("reporte", reporte_inicio)],
        states={
            REPORTE_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, reporte_generar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversation Handler: BUSCAR VENTA
    # FIX BUG 4: ELIMINAR_DESDE_BUSCAR es el estado de confirmación exclusivo de este handler
    conv_buscar_venta = ConversationHandler(
        entry_points=[CommandHandler("buscar", buscar_venta_inicio)],
        states={
            BUSCAR_VENTA_FACTURA:    [MessageHandler(filters.TEXT & ~filters.COMMAND, buscar_venta_factura)],
            BUSCAR_VENTA_ACCION:     [MessageHandler(filters.TEXT & ~filters.COMMAND, buscar_venta_accion)],
            EDITAR_VENTA_CAMPO:      [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_venta_campo)],
            EDITAR_VENTA_VALOR:      [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_venta_valor)],
            EDITAR_VENTA_CONFIRMAR:  [MessageHandler(filters.TEXT & ~filters.COMMAND, editar_venta_confirmar)],
            ELIMINAR_DESDE_BUSCAR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, eliminar_desde_buscar_confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversation Handler: ELIMINAR ÚLTIMO
    conv_eliminar = ConversationHandler(
        entry_points=[CommandHandler("eliminar", eliminar_ultimo_inicio)],
        states={
            ELIMINAR_TIPO:     [MessageHandler(filters.TEXT & ~filters.COMMAND, eliminar_tipo)],
            ELIMINAR_CONFIRMAR:[MessageHandler(filters.TEXT & ~filters.COMMAND, eliminar_confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    # Conversation Handler: CIERRE DIARIO
    conv_cierreday = ConversationHandler(
        entry_points=[CommandHandler("cierreday", cierreday_inicio)],
        states={
            CDAY_FECHA:        [MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_fecha)],
            CDAY_EFECTIVO:     [MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_efectivo)],
            CDAY_TRANSFERENCIA:[MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_transferencia)],
            CDAY_TARJETA_DEB:  [MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_tarjeta_deb)],
            CDAY_TARJETA_CRED: [MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_tarjeta_cred)],
            CDAY_OTRO:         [MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_otro)],
            CDAY_OBS:          [MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_obs)],
            CDAY_CONFIRMAR:    [MessageHandler(filters.TEXT & ~filters.COMMAND, cierreday_confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    application.add_handler(conv_venta)
    application.add_handler(conv_gasto)
    application.add_handler(conv_reporte)
    application.add_handler(conv_buscar_venta)
    application.add_handler(conv_eliminar)
    application.add_handler(conv_cierreday)

    # FIX BUG 6: Registrar handlers del módulo ML
    handlers_ml = obtener_handlers_ml()
    application.add_handler(handlers_ml['conv_analisis'])
    application.add_handler(handlers_ml['cmd_prediccion'])
    application.add_handler(handlers_ml['cmd_anomalias'])
    application.add_handler(handlers_ml['cmd_tendencias'])
    application.add_handler(handlers_ml['cmd_insights'])

    logger.info("🤖 Bot de SURTHILANAS iniciado")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()