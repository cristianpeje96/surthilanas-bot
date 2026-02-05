"""
Bot de Telegram para SURTHILANAS
Sistema de registro financiero automatizado
"""

import logging
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
    obtener_rango_fechas
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

# Decorador para verificar autorización
def requiere_autorizacion(func):
    """Decorador que verifica si el usuario está autorizado"""
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

💰 <b>/venta</b> - Registrar una nueva venta
💸 <b>/gasto</b> - Registrar un nuevo gasto
📊 <b>/reporte</b> - Ver reportes financieros
📈 <b>/estado</b> - Ver estado actual
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

<b>Para registrar una venta:</b>
1. Usa /venta
2. Sigue las instrucciones paso a paso
3. Confirma antes de guardar

<b>Para registrar un gasto:</b>
1. Usa /gasto
2. Selecciona la categoría
3. Ingresa los datos solicitados

<b>Para ver reportes:</b>
1. Usa /reporte
2. Selecciona el período (hoy/semana/mes)
3. Revisa el resumen financiero

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
        "• O ingresa en formato DD/MM/AAAA (ej: 15/01/2025)",
        parse_mode='HTML'
    )
    return VENTA_FECHA

async def venta_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa la fecha de la venta"""
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
        "Ahora ingresa el número de factura:"
    )
    return VENTA_FACTURA

async def venta_factura(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa el número de factura"""
    numero = update.message.text.strip()
    
    if not validar_numero_factura(numero):
        await update.message.reply_text(
            "❌ Número de factura inválido (máximo 20 caracteres)."
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
    """Procesa el nombre del cliente"""
    cliente = normalizar_texto(update.message.text)
    context.user_data['venta_cliente'] = cliente
    
    await update.message.reply_text(
        f"✅ Cliente: {cliente}\n\n"
        "Ingresa el monto de la venta (solo números):"
    )
    return VENTA_MONTO

async def venta_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa el monto de la venta"""
    monto_input = update.message.text.strip()
    es_valido, monto = validar_monto(monto_input)
    
    if not es_valido:
        await update.message.reply_text(
            "❌ Monto inválido. Ingresa solo números positivos."
        )
        return VENTA_MONTO
    
    context.user_data['venta_monto'] = monto
    
    # Teclado con opciones de medio de pago
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
    """Procesa el medio de pago"""
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
    """Procesa las observaciones y muestra confirmación"""
    observaciones = normalizar_texto(update.message.text)
    context.user_data['venta_obs'] = observaciones
    
    # Preparar datos para confirmación
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
    """Confirma y guarda la venta"""
    respuesta = update.message.text.strip().lower()
    
    if respuesta not in ['sí', 'si', 'yes', 's']:
        await update.message.reply_text(
            "❌ Venta cancelada.",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    # Guardar en Google Sheets
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
    """Inicia el flujo de registro de gasto"""
    await update.message.reply_text(
        "💸 <b>REGISTRO DE GASTO</b>\n\n"
        "Ingresa la fecha del gasto:\n"
        "• Escribe 'hoy' para usar la fecha actual\n"
        "• O ingresa en formato DD/MM/AAAA",
        parse_mode='HTML'
    )
    return GASTO_FECHA

async def gasto_fecha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa la fecha del gasto"""
    fecha_input = update.message.text.strip()
    es_valida, fecha = validar_fecha(fecha_input)
    
    if not es_valida:
        await update.message.reply_text(
            "❌ Fecha inválida. Usa formato DD/MM/AAAA o escribe 'hoy'."
        )
        return GASTO_FECHA
    
    context.user_data['gasto_fecha'] = fecha
    
    # Teclado con categorías
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
    """Procesa la categoría del gasto"""
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
    """Procesa el proveedor"""
    proveedor = normalizar_texto(update.message.text)
    context.user_data['gasto_proveedor'] = proveedor
    
    await update.message.reply_text(
        f"✅ Proveedor: {proveedor}\n\n"
        "Ingresa el monto del gasto:"
    )
    return GASTO_MONTO

async def gasto_monto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa el monto del gasto"""
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
    """Procesa el medio de pago"""
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
    """Procesa las observaciones y muestra confirmación"""
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
    """Confirma y guarda el gasto"""
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
    """Inicia el flujo de generación de reportes"""
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
    """Genera el reporte según el período seleccionado"""
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
    
    # Obtener totales
    totales = sheets_manager.calcular_totales(fecha_inicio, fecha_fin)
    
    # Generar resumen
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
    """Muestra el estado financiero actual del mes"""
    totales = sheets_manager.calcular_totales(*obtener_rango_fechas('mes'))
    resumen = generar_resumen_financiero(totales)
    await update.message.reply_text(resumen)

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def main() -> None:
    """Inicializa y ejecuta el bot"""
    
    # Crear aplicación
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Handlers de comandos básicos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("estado", estado))
    
    # Conversation Handler para VENTAS
    conv_venta = ConversationHandler(
        entry_points=[CommandHandler("venta", venta_inicio)],
        states={
            VENTA_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_fecha)],
            VENTA_FACTURA: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_factura)],
            VENTA_CLIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_cliente)],
            VENTA_MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_monto)],
            VENTA_PAGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_pago)],
            VENTA_OBS: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_observaciones)],
            VENTA_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, venta_confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )
    
    # Conversation Handler para GASTOS
    conv_gasto = ConversationHandler(
        entry_points=[CommandHandler("gasto", gasto_inicio)],
        states={
            GASTO_FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_fecha)],
            GASTO_CATEGORIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_categoria)],
            GASTO_PROVEEDOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_proveedor)],
            GASTO_MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_monto)],
            GASTO_PAGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_pago)],
            GASTO_OBS: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_observaciones)],
            GASTO_CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, gasto_confirmar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )
    
    # Conversation Handler para REPORTES
    conv_reporte = ConversationHandler(
        entry_points=[CommandHandler("reporte", reporte_inicio)],
        states={
            REPORTE_TIPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, reporte_generar)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )
    
    application.add_handler(conv_venta)
    application.add_handler(conv_gasto)
    application.add_handler(conv_reporte)
    
    # Iniciar bot
    logger.info("🤖 Bot de SURTHILANAS iniciado")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
