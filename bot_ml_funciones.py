"""
Funciones del bot de Telegram para análisis inteligente con ML
Integración del AnalizadorFinancieroML con el bot de SURTHILANAS
"""

from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler,
    CommandHandler, MessageHandler, filters
)
from ml_analisis import AnalizadorFinancieroML
from utils import es_usuario_autorizado  # FIX BUG 5: usar la misma función del bot principal
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Estado de conversación para análisis inteligente
ANALISIS_PREGUNTA = 30

# Instancia global del analizador
analizador_ml: AnalizadorFinancieroML | None = None


def inicializar_analizador_ml(ruta_excel: str) -> bool:
    """
    Inicializa el analizador ML con los datos de SURTHILANAS

    Args:
        ruta_excel: Ruta al archivo Excel con datos financieros
    """
    global analizador_ml
    try:
        analizador_ml = AnalizadorFinancieroML(ruta_excel)
        logger.info("✅ Analizador ML inicializado correctamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error al inicializar analizador ML: {e}")
        return False


# FIX BUG 5: Decorador que usa es_usuario_autorizado() de utils.py (misma fuente que bot.py)
def requiere_autorizacion(func):
    """Decorador que verifica si el usuario está autorizado"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not es_usuario_autorizado(user_id):
            await update.message.reply_text(
                "🔒 No tienes autorización para usar este comando.\n"
                "Contacta al administrador del sistema."
            )
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapper


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela cualquier conversación activa del módulo ML"""
    await update.message.reply_text(
        "❌ Operación cancelada.\n"
        "Usa /menu para ver los comandos disponibles."
    )
    return ConversationHandler.END


# ============================================
# COMANDO /analisis - ANÁLISIS INTELIGENTE
# ============================================

@requiere_autorizacion
async def analisis_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el análisis inteligente con ML"""

    if analizador_ml is None:
        await update.message.reply_text(
            "❌ El analizador inteligente no está disponible.\n"
            "Contacta al administrador del sistema."
        )
        return ConversationHandler.END

    mensaje = (
        "🤖 <b>ANÁLISIS INTELIGENTE CON IA</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Puedo ayudarte a analizar las finanzas de tu empresa usando "
        "inteligencia artificial y machine learning.\n\n"
        "<b>📊 Puedes preguntarme:</b>\n\n"
        "• ¿Cuál es el resumen general?\n"
        "• ¿Cuáles son mis principales gastos?\n"
        "• ¿Cuáles son mis mejores categorías de ingreso?\n"
        "• ¿Cómo ha sido la tendencia mensual?\n"
        "• ¿Hay transacciones anómalas o sospechosas?\n"
        "• ¿Cuánto venderé el próximo mes?\n"
        "• ¿Qué puedo mejorar en mis finanzas?\n\n"
        "💬 <b>Escribe tu pregunta:</b>"
    )

    await update.message.reply_text(mensaje, parse_mode='HTML')
    return ANALISIS_PREGUNTA


async def analisis_pregunta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Procesa la pregunta del usuario y genera respuesta con ML"""

    pregunta = update.message.text.strip()

    if not pregunta:
        await update.message.reply_text("❌ Por favor escribe una pregunta válida.")
        return ANALISIS_PREGUNTA

    try:
        await update.message.chat.send_action(action="typing")
        respuesta = analizador_ml.responder_pregunta(pregunta)
        await update.message.reply_text(respuesta, parse_mode='HTML')
        await update.message.reply_text(
            "💬 ¿Tienes otra pregunta?\n"
            "Escribe tu pregunta o usa /cancelar para salir."
        )
        return ANALISIS_PREGUNTA

    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        await update.message.reply_text(
            "❌ Ocurrió un error al procesar tu pregunta.\n"
            "Por favor intenta nuevamente."
        )
        return ANALISIS_PREGUNTA


# ============================================
# COMANDO /prediccion - PREDICCIONES ML
# ============================================

@requiere_autorizacion
async def prediccion_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Muestra predicciones de ventas usando ML"""

    if analizador_ml is None:
        await update.message.reply_text("❌ El sistema de predicciones no está disponible.")
        return ConversationHandler.END

    try:
        if analizador_ml.modelo_ventas is None:
            await update.message.reply_text(
                "🤖 Entrenando modelo de predicción...\n"
                "Esto puede tardar unos segundos."
            )
            resultado = analizador_ml.entrenar_modelo_ventas()

            if 'error' in resultado:
                await update.message.reply_text(f"❌ Error al entrenar modelo: {resultado['error']}")
                return ConversationHandler.END

            await update.message.reply_text(
                "✅ <b>Modelo entrenado exitosamente</b>\n\n"
                f"📊 Precisión: {resultado['precisión']}\n"
                f"📉 Error promedio: ${resultado['error_promedio']:,.0f}\n"
                f"🔢 Datos de entrenamiento: {resultado['num_datos_entrenamiento']}\n"
                f"🧪 Datos de prueba: {resultado['num_datos_prueba']}\n",
                parse_mode='HTML'
            )

        from datetime import datetime
        hoy = datetime.now()
        siguiente_mes = hoy.month + 1 if hoy.month < 12 else 1
        siguiente_año = hoy.year if hoy.month < 12 else hoy.year + 1

        await update.message.reply_text("🔮 Generando predicción...")
        prediccion = analizador_ml.predecir_ventas_mes(siguiente_año, siguiente_mes)
        respuesta = analizador_ml._formatear_prediccion(prediccion)
        await update.message.reply_text(respuesta, parse_mode='HTML')
        await update.message.reply_text(
            "💡 ¿Quieres predecir otro mes?\n"
            "Usa /prediccion nuevamente o /analisis para más opciones."
        )

    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        await update.message.reply_text(
            "❌ Error al generar predicción.\n"
            "Verifica que haya suficientes datos históricos."
        )

    return ConversationHandler.END


# ============================================
# COMANDO /anomalias - DETECCIÓN DE ANOMALÍAS
# ============================================

@requiere_autorizacion
async def anomalias_comando(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Detecta transacciones anómalas o sospechosas"""

    if analizador_ml is None:
        await update.message.reply_text("❌ El detector de anomalías no está disponible.")
        return

    try:
        await update.message.reply_text(
            "🔍 Analizando transacciones...\n"
            "Buscando valores atípicos y anomalías."
        )
        df_anomalias = analizador_ml.detectar_anomalias()
        respuesta = analizador_ml._formatear_anomalias(df_anomalias)
        await update.message.reply_text(respuesta, parse_mode='HTML')

        if len(df_anomalias) > 0:
            await update.message.reply_text(
                "💡 <b>Recomendación:</b>\n"
                "Revisa estas transacciones para asegurarte de que son correctas.\n"
                "Usa /buscar [número_factura] para editar si es necesario.",
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Error en detección de anomalías: {e}")
        await update.message.reply_text("❌ Error al detectar anomalías. Intenta nuevamente.")


# ============================================
# COMANDO /tendencias - ANÁLISIS DE TENDENCIAS
# ============================================

@requiere_autorizacion
async def tendencias_comando(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra análisis de tendencias mensuales"""

    if analizador_ml is None:
        await update.message.reply_text("❌ El análisis de tendencias no está disponible.")
        return

    try:
        await update.message.reply_text("📈 Analizando tendencias financieras...")

        df_tendencia = analizador_ml.analizar_tendencia_mensual()
        respuesta_tendencia = analizador_ml._formatear_tendencia_mensual(df_tendencia)
        await update.message.reply_text(respuesta_tendencia, parse_mode='HTML')

        df_cat_ingresos = analizador_ml.analizar_por_categoria('Ingreso')
        respuesta_cat = analizador_ml._formatear_analisis_categoria(df_cat_ingresos, 'Top Ingresos')
        await update.message.reply_text(respuesta_cat, parse_mode='HTML')

    except Exception as e:
        logger.error(f"Error en análisis de tendencias: {e}")
        await update.message.reply_text("❌ Error al analizar tendencias. Intenta nuevamente.")


# ============================================
# COMANDO /insights - INSIGHTS INTELIGENTES
# ============================================

@requiere_autorizacion
async def insights_comando(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Genera insights y recomendaciones inteligentes"""

    if analizador_ml is None:
        await update.message.reply_text("❌ El generador de insights no está disponible.")
        return

    try:
        await update.message.reply_text(
            "🧠 Generando insights inteligentes...\n"
            "Analizando patrones en tus datos."
        )

        resumen = analizador_ml.obtener_resumen_general()
        insights = []

        if resumen['margen_utilidad'] < 10:
            insights.append(
                f"⚠️ <b>Margen bajo:</b> Tu margen de utilidad es de "
                f"{resumen['margen_utilidad']:.1f}%. Considera reducir gastos o aumentar precios."
            )
        elif resumen['margen_utilidad'] > 30:
            insights.append(
                f"✅ <b>Excelente margen:</b> Tienes un margen saludable de "
                f"{resumen['margen_utilidad']:.1f}%. ¡Sigue así!"
            )

        if resumen['ticket_promedio_venta'] > 0:
            insights.append(
                f"💰 Tu ticket promedio de venta es ${resumen['ticket_promedio_venta']:,.0f}. "
                "Considera estrategias de upselling para aumentarlo."
            )

        dias_operacion = (resumen['fecha_fin'] - resumen['fecha_inicio']).days
        trans_por_dia = resumen['num_transacciones'] / max(dias_operacion, 1)
        if trans_por_dia < 2:
            insights.append(
                f"📊 Registras {trans_por_dia:.1f} transacciones por día. "
                "Aumentar la frecuencia puede mejorar el flujo de caja."
            )

        df_gastos = analizador_ml.analizar_por_categoria('Gasto')
        if len(df_gastos) > 0:
            porcentaje = (abs(df_gastos.iloc[0]['Total']) / resumen['total_gastos']) * 100
            insights.append(
                f"🔍 Tu mayor gasto es en '{df_gastos.index[0]}' "
                f"({porcentaje:.1f}% del total). Analiza si puedes optimizar esta área."
            )

        mensaje = "🧠 <b>INSIGHTS Y RECOMENDACIONES</b>\n"
        mensaje += "━━━━━━━━━━━━━━━━━━━━\n\n"
        mensaje += "\n\n".join(insights) if insights else (
            "✅ Tus finanzas están en buen estado general.\n\n"
            "Continúa monitoreando regularmente y usa /analisis para preguntas específicas."
        )

        await update.message.reply_text(mensaje, parse_mode='HTML')
        await update.message.reply_text(
            "💡 <b>Tip:</b> Usa /prediccion para ver proyecciones futuras.",
            parse_mode='HTML'
        )

    except Exception as e:
        logger.error(f"Error generando insights: {e}")
        await update.message.reply_text("❌ Error al generar insights. Intenta nuevamente.")


# ============================================
# CONFIGURACIÓN DE HANDLERS
# ============================================

def obtener_handlers_ml():
    """Retorna los handlers para las funcionalidades ML para agregar en main()"""

    conv_analisis = ConversationHandler(
        entry_points=[CommandHandler("analisis", analisis_inicio)],
        states={
            ANALISIS_PREGUNTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, analisis_pregunta)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    return {
        'conv_analisis': conv_analisis,
        'cmd_prediccion': CommandHandler("prediccion", prediccion_inicio),
        'cmd_anomalias': CommandHandler("anomalias", anomalias_comando),
        'cmd_tendencias': CommandHandler("tendencias", tendencias_comando),
        'cmd_insights': CommandHandler("insights", insights_comando),
    }
