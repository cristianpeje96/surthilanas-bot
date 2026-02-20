"""
Módulo de Machine Learning para análisis financiero de SURTHILANAS
Proporciona análisis predictivo, clustering y respuestas inteligentes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# ML Libraries
try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.warning("Scikit-learn no disponible. Instala con: pip install scikit-learn")

logger = logging.getLogger(__name__)

class AnalizadorFinancieroML:
    """
    Analizador financiero con capacidades de Machine Learning
    """
    
    def __init__(self, ruta_excel: str):
        """
        Inicializa el analizador con el archivo Excel de SURTHILANAS
        
        Args:
            ruta_excel: Ruta al archivo Excel con datos financieros
        """
        self.ruta_excel = ruta_excel
        self.df_transacciones = None
        self.df_categorias = None
        self.modelo_ventas = None
        self.scaler = StandardScaler() if ML_AVAILABLE else None
        self.cargar_datos()
    
    def cargar_datos(self):
        """Carga y procesa los datos del Excel"""
        try:
            # Leer transacciones
            df_raw = pd.read_excel(
                self.ruta_excel, 
                sheet_name='Transacciones',
                skiprows=5  # Saltar filas de encabezado
            )
            
            # Limpiar nombres de columnas
            df_raw.columns = ['Categoría', 'Fecha', 'Descripción', 'Importe', 'Extra']
            
            # Filtrar datos válidos
            self.df_transacciones = df_raw[
                df_raw['Categoría'].notna() & 
                df_raw['Fecha'].notna() &
                df_raw['Importe'].notna()
            ].copy()
            
            # Convertir fecha
            self.df_transacciones['Fecha'] = pd.to_datetime(
                self.df_transacciones['Fecha'], 
                errors='coerce'
            )
            
            # Convertir importe a numérico
            self.df_transacciones['Importe'] = pd.to_numeric(
                self.df_transacciones['Importe'], 
                errors='coerce'
            )
            
            # Crear características adicionales
            self.df_transacciones['Año'] = self.df_transacciones['Fecha'].dt.year
            self.df_transacciones['Mes'] = self.df_transacciones['Fecha'].dt.month
            self.df_transacciones['Día'] = self.df_transacciones['Fecha'].dt.day
            self.df_transacciones['DiaSemana'] = self.df_transacciones['Fecha'].dt.dayofweek
            self.df_transacciones['Trimestre'] = self.df_transacciones['Fecha'].dt.quarter
            
            # Clasificar tipo de transacción
            self.df_transacciones['Tipo'] = self.df_transacciones['Importe'].apply(
                lambda x: 'Ingreso' if x > 0 else 'Gasto'
            )
            
            # Cargar categorías
            try:
                df_cat = pd.read_excel(
                    self.ruta_excel,
                    sheet_name='Categorías',
                    skiprows=4
                )
                df_cat.columns = ['Categoría', 'Tipo']
                self.df_categorias = df_cat[df_cat['Categoría'].notna()].copy()
            except:
                logger.warning("No se pudo cargar la hoja de Categorías")
            
            logger.info(f"Datos cargados: {len(self.df_transacciones)} transacciones")
            
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            raise
    
    # ============================================
    # ANÁLISIS DESCRIPTIVO
    # ============================================
    
    def obtener_resumen_general(self) -> Dict:
        """Genera un resumen general de las finanzas"""
        if self.df_transacciones is None or len(self.df_transacciones) == 0:
            return {"error": "No hay datos disponibles"}
        
        ingresos = self.df_transacciones[self.df_transacciones['Importe'] > 0]['Importe'].sum()
        gastos = abs(self.df_transacciones[self.df_transacciones['Importe'] < 0]['Importe'].sum())
        utilidad = ingresos - gastos
        
        return {
            'total_ingresos': ingresos,
            'total_gastos': gastos,
            'utilidad_neta': utilidad,
            'margen_utilidad': (utilidad / ingresos * 100) if ingresos > 0 else 0,
            'num_transacciones': len(self.df_transacciones),
            'num_ingresos': len(self.df_transacciones[self.df_transacciones['Importe'] > 0]),
            'num_gastos': len(self.df_transacciones[self.df_transacciones['Importe'] < 0]),
            'ticket_promedio_venta': self.df_transacciones[
                self.df_transacciones['Importe'] > 0
            ]['Importe'].mean() if len(self.df_transacciones[self.df_transacciones['Importe'] > 0]) > 0 else 0,
            'gasto_promedio': abs(self.df_transacciones[
                self.df_transacciones['Importe'] < 0
            ]['Importe'].mean()) if len(self.df_transacciones[self.df_transacciones['Importe'] < 0]) > 0 else 0,
            'fecha_inicio': self.df_transacciones['Fecha'].min(),
            'fecha_fin': self.df_transacciones['Fecha'].max()
        }
    
    def analizar_por_categoria(self, tipo: str = None) -> pd.DataFrame:
        """
        Analiza las transacciones por categoría
        
        Args:
            tipo: 'Ingreso' o 'Gasto' para filtrar, None para todos
        """
        df = self.df_transacciones.copy()
        
        if tipo:
            df = df[df['Tipo'] == tipo]
        
        analisis = df.groupby('Categoría').agg({
            'Importe': ['sum', 'mean', 'count'],
            'Fecha': ['min', 'max']
        }).round(2)
        
        analisis.columns = ['Total', 'Promedio', 'Cantidad', 'Primera_Fecha', 'Última_Fecha']
        analisis = analisis.sort_values('Total', ascending=False)
        
        return analisis
    
    def analizar_tendencia_mensual(self) -> pd.DataFrame:
        """Analiza la tendencia de ingresos y gastos por mes"""
        df = self.df_transacciones.copy()
        
        # Agrupar por año y mes
        df['AñoMes'] = df['Fecha'].dt.to_period('M')
        
        tendencia = df.groupby(['AñoMes', 'Tipo'])['Importe'].sum().unstack(fill_value=0)
        tendencia['Utilidad'] = tendencia.get('Ingreso', 0) + tendencia.get('Gasto', 0)
        
        return tendencia
    
    def detectar_anomalias(self, umbral_std: float = 2.5) -> pd.DataFrame:
        """
        Detecta transacciones anómalas (valores atípicos)
        
        Args:
            umbral_std: Número de desviaciones estándar para considerar anomalía
        """
        df = self.df_transacciones.copy()
        
        # Calcular estadísticas por tipo
        anomalias = []
        
        for tipo in ['Ingreso', 'Gasto']:
            df_tipo = df[df['Tipo'] == tipo]
            if len(df_tipo) == 0:
                continue
                
            valores = df_tipo['Importe'].abs()
            media = valores.mean()
            std = valores.std()
            
            # Identificar valores fuera del umbral
            df_anomalo = df_tipo[
                (valores > media + umbral_std * std) | 
                (valores < media - umbral_std * std)
            ].copy()
            
            df_anomalo['Desviación_Std'] = ((valores - media) / std).abs()
            anomalias.append(df_anomalo)
        
        if anomalias:
            resultado = pd.concat(anomalias)
            return resultado.sort_values('Desviación_Std', ascending=False)
        
        return pd.DataFrame()
    
    # ============================================
    # PREDICCIONES CON MACHINE LEARNING
    # ============================================
    
    def entrenar_modelo_ventas(self) -> Dict:
        """
        Entrena un modelo de ML para predecir ventas futuras
        
        Returns:
            Diccionario con métricas del modelo
        """
        if not ML_AVAILABLE:
            return {"error": "Scikit-learn no está instalado"}
        
        try:
            # Filtrar solo ventas/ingresos
            df_ventas = self.df_transacciones[
                self.df_transacciones['Importe'] > 0
            ].copy()
            
            if len(df_ventas) < 20:
                return {"error": "No hay suficientes datos para entrenar (mínimo 20 ventas)"}
            
            # Preparar características
            features = ['Año', 'Mes', 'Día', 'DiaSemana', 'Trimestre']
            X = df_ventas[features]
            y = df_ventas['Importe']
            
            # Dividir datos
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Entrenar modelo
            self.modelo_ventas = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=4,
                random_state=42
            )
            
            self.modelo_ventas.fit(X_train, y_train)
            
            # Evaluar
            y_pred = self.modelo_ventas.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Importancia de características
            importancia = dict(zip(
                features,
                self.modelo_ventas.feature_importances_
            ))
            
            return {
                'mae': mae,
                'r2': r2,
                'precisión': f"{r2 * 100:.1f}%",
                'error_promedio': mae,
                'importancia_features': importancia,
                'num_datos_entrenamiento': len(X_train),
                'num_datos_prueba': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error al entrenar modelo: {e}")
            return {"error": str(e)}
    
    def predecir_ventas_mes(self, año: int, mes: int) -> Dict:
        """
        Predice las ventas para un mes específico
        
        Args:
            año: Año a predecir
            mes: Mes a predecir (1-12)
        """
        if not ML_AVAILABLE or self.modelo_ventas is None:
            # Si no hay modelo, usar promedio histórico
            return self._predecir_con_promedio(año, mes)
        
        try:
            # Crear features para todos los días del mes
            import calendar
            dias_mes = calendar.monthrange(año, mes)[1]
            
            predicciones = []
            for dia in range(1, dias_mes + 1):
                fecha = datetime(año, mes, dia)
                trimestre = (mes - 1) // 3 + 1
                dia_semana = fecha.weekday()
                
                features = pd.DataFrame([{
                    'Año': año,
                    'Mes': mes,
                    'Día': dia,
                    'DiaSemana': dia_semana,
                    'Trimestre': trimestre
                }])
                
                pred = self.modelo_ventas.predict(features)[0]
                predicciones.append(pred)
            
            venta_total_predicha = sum(predicciones)
            venta_promedio_dia = np.mean(predicciones)
            
            # Comparar con histórico
            historico_mes = self.df_transacciones[
                (self.df_transacciones['Mes'] == mes) &
                (self.df_transacciones['Importe'] > 0)
            ]['Importe'].sum()
            
            return {
                'año': año,
                'mes': mes,
                'venta_total_predicha': venta_total_predicha,
                'venta_promedio_dia': venta_promedio_dia,
                'dias_mes': dias_mes,
                'historico_mismo_mes': historico_mes,
                'diferencia_vs_historico': venta_total_predicha - historico_mes,
                'variacion_porcentual': ((venta_total_predicha - historico_mes) / historico_mes * 100) if historico_mes > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return {"error": str(e)}
    
    def _predecir_con_promedio(self, año: int, mes: int) -> Dict:
        """Predicción simple basada en promedios históricos"""
        # Calcular promedio del mismo mes en años anteriores
        df_mes = self.df_transacciones[
            (self.df_transacciones['Mes'] == mes) &
            (self.df_transacciones['Importe'] > 0)
        ]
        
        if len(df_mes) == 0:
            # Usar promedio general
            promedio = self.df_transacciones[
                self.df_transacciones['Importe'] > 0
            ]['Importe'].mean()
        else:
            promedio = df_mes['Importe'].mean()
        
        import calendar
        dias_mes = calendar.monthrange(año, mes)[1]
        venta_predicha = promedio * dias_mes
        
        return {
            'año': año,
            'mes': mes,
            'venta_total_predicha': venta_predicha,
            'venta_promedio_dia': promedio,
            'dias_mes': dias_mes,
            'metodo': 'promedio_histórico',
            'nota': 'Predicción basada en promedio histórico (modelo ML no disponible)'
        }
    
    # ============================================
    # CLUSTERING Y SEGMENTACIÓN
    # ============================================
    
    def segmentar_transacciones(self, n_clusters: int = 3) -> Dict:
        """
        Segmenta las transacciones en clusters usando K-Means
        
        Args:
            n_clusters: Número de segmentos a crear
        """
        if not ML_AVAILABLE:
            return {"error": "Scikit-learn no está instalado"}
        
        try:
            df = self.df_transacciones.copy()
            
            # Preparar datos para clustering
            features = df[['Importe', 'Mes', 'DiaSemana']].copy()
            features['Importe_Abs'] = features['Importe'].abs()
            
            # Escalar datos
            X_scaled = self.scaler.fit_transform(features[['Importe_Abs', 'Mes', 'DiaSemana']])
            
            # Aplicar K-Means
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df['Cluster'] = kmeans.fit_predict(X_scaled)
            
            # Analizar cada cluster
            clusters_info = []
            for i in range(n_clusters):
                cluster_data = df[df['Cluster'] == i]
                
                info = {
                    'cluster_id': i,
                    'num_transacciones': len(cluster_data),
                    'importe_promedio': cluster_data['Importe'].mean(),
                    'importe_total': cluster_data['Importe'].sum(),
                    'categorias_principales': cluster_data['Categoría'].value_counts().head(3).to_dict(),
                    'tipo_predominante': cluster_data['Tipo'].mode()[0] if len(cluster_data) > 0 else 'N/A'
                }
                clusters_info.append(info)
            
            return {
                'num_clusters': n_clusters,
                'clusters': clusters_info,
                'datos_con_clusters': df
            }
            
        except Exception as e:
            logger.error(f"Error en clustering: {e}")
            return {"error": str(e)}
    
    # ============================================
    # RESPUESTAS A PREGUNTAS EN LENGUAJE NATURAL
    # ============================================
    
    def responder_pregunta(self, pregunta: str) -> str:
        """
        Responde preguntas sobre los datos financieros
        
        Args:
            pregunta: Pregunta en lenguaje natural
        """
        pregunta = pregunta.lower()
        
        # Resumen general
        if any(word in pregunta for word in ['resumen', 'general', 'total', 'estado']):
            resumen = self.obtener_resumen_general()
            return self._formatear_resumen_general(resumen)
        
        # Categorías
        if 'categoría' in pregunta or 'categorias' in pregunta:
            if 'gasto' in pregunta:
                df = self.analizar_por_categoria('Gasto')
                return self._formatear_analisis_categoria(df, 'Gastos')
            elif 'ingreso' in pregunta or 'venta' in pregunta:
                df = self.analizar_por_categoria('Ingreso')
                return self._formatear_analisis_categoria(df, 'Ingresos')
            else:
                df = self.analizar_por_categoria()
                return self._formatear_analisis_categoria(df, 'Todas las categorías')
        
        # Tendencias
        if 'tendencia' in pregunta or 'mensual' in pregunta or 'evolución' in pregunta:
            df = self.analizar_tendencia_mensual()
            return self._formatear_tendencia_mensual(df)
        
        # Anomalías
        if 'anomal' in pregunta or 'atípic' in pregunta or 'extrañ' in pregunta:
            df = self.detectar_anomalias()
            return self._formatear_anomalias(df)
        
        # Predicciones
        if 'predict' in pregunta or 'previsi' in pregunta or 'futuro' in pregunta or 'próximo' in pregunta:
            # Predecir próximo mes
            hoy = datetime.now()
            siguiente_mes = hoy.month + 1 if hoy.month < 12 else 1
            siguiente_año = hoy.year if hoy.month < 12 else hoy.year + 1
            
            pred = self.predecir_ventas_mes(siguiente_año, siguiente_mes)
            return self._formatear_prediccion(pred)
        
        # Respuesta por defecto
        return (
            "🤔 No entendí completamente tu pregunta. Puedo ayudarte con:\n\n"
            "📊 Resumen general y estado financiero\n"
            "📈 Análisis por categorías (ingresos/gastos)\n"
            "📉 Tendencias mensuales y evolución\n"
            "🔍 Detección de transacciones anómalas\n"
            "🔮 Predicciones de ventas futuras\n\n"
            "Intenta preguntar algo como:\n"
            "• ¿Cuál es el resumen general?\n"
            "• ¿Cuáles son mis principales gastos?\n"
            "• ¿Cómo ha sido la tendencia mensual?\n"
            "• ¿Hay transacciones anómalas?\n"
            "• ¿Cuánto venderé el próximo mes?"
        )
    
    # ============================================
    # MÉTODOS DE FORMATEO
    # ============================================
    
    def _formatear_resumen_general(self, resumen: Dict) -> str:
        """Formatea el resumen general para mostrar al usuario"""
        if 'error' in resumen:
            return f"❌ {resumen['error']}"
        
        texto = "📊 <b>RESUMEN FINANCIERO GENERAL</b>\n"
        texto += "━━━━━━━━━━━━━━━━━━━━\n\n"
        texto += f"💰 <b>Ingresos Totales:</b> ${resumen['total_ingresos']:,.0f}\n"
        texto += f"💸 <b>Gastos Totales:</b> ${resumen['total_gastos']:,.0f}\n"
        texto += f"📈 <b>Utilidad Neta:</b> ${resumen['utilidad_neta']:,.0f}\n"
        texto += f"📊 <b>Margen:</b> {resumen['margen_utilidad']:.1f}%\n\n"
        texto += f"🔢 <b>Transacciones:</b> {resumen['num_transacciones']}\n"
        texto += f"   • Ingresos: {resumen['num_ingresos']}\n"
        texto += f"   • Gastos: {resumen['num_gastos']}\n\n"
        texto += f"🎯 <b>Ticket Promedio Venta:</b> ${resumen['ticket_promedio_venta']:,.0f}\n"
        texto += f"💳 <b>Gasto Promedio:</b> ${resumen['gasto_promedio']:,.0f}\n\n"
        texto += f"📅 Período: {resumen['fecha_inicio'].strftime('%d/%m/%Y')} - {resumen['fecha_fin'].strftime('%d/%m/%Y')}"
        
        return texto
    
    def _formatear_analisis_categoria(self, df: pd.DataFrame, titulo: str) -> str:
        """Formatea el análisis por categorías"""
        if len(df) == 0:
            return "❌ No hay datos disponibles para este análisis"
        
        texto = f"📂 <b>ANÁLISIS POR CATEGORÍAS - {titulo.upper()}</b>\n"
        texto += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        top_5 = df.head(5)
        for idx, (cat, row) in enumerate(top_5.iterrows(), 1):
            texto += f"{idx}. <b>{cat}</b>\n"
            texto += f"   💰 Total: ${abs(row['Total']):,.0f}\n"
            texto += f"   📊 Promedio: ${abs(row['Promedio']):,.0f}\n"
            texto += f"   🔢 Cantidad: {int(row['Cantidad'])}\n\n"
        
        return texto
    
    def _formatear_tendencia_mensual(self, df: pd.DataFrame) -> str:
        """Formatea el análisis de tendencia mensual"""
        if len(df) == 0:
            return "❌ No hay datos suficientes para análisis de tendencia"
        
        texto = "📈 <b>TENDENCIA MENSUAL</b>\n"
        texto += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for periodo, row in df.tail(6).iterrows():
            ingreso = row.get('Ingreso', 0)
            gasto = abs(row.get('Gasto', 0))
            utilidad = row.get('Utilidad', 0)
            
            texto += f"📅 <b>{periodo}</b>\n"
            texto += f"   💰 Ingresos: ${ingreso:,.0f}\n"
            texto += f"   💸 Gastos: ${gasto:,.0f}\n"
            texto += f"   {'✅' if utilidad >= 0 else '⚠️'} Utilidad: ${utilidad:,.0f}\n\n"
        
        return texto
    
    def _formatear_anomalias(self, df: pd.DataFrame) -> str:
        """Formatea el reporte de anomalías"""
        if len(df) == 0:
            return "✅ No se detectaron transacciones anómalas"
        
        texto = "🔍 <b>TRANSACCIONES ANÓMALAS DETECTADAS</b>\n"
        texto += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for idx, row in df.head(5).iterrows():
            texto += f"⚠️ <b>{row['Fecha'].strftime('%d/%m/%Y')}</b>\n"
            texto += f"   Categoría: {row['Categoría']}\n"
            texto += f"   Importe: ${abs(row['Importe']):,.0f}\n"
            texto += f"   Descripción: {row['Descripción']}\n"
            texto += f"   Desviación: {row['Desviación_Std']:.1f} σ\n\n"
        
        return texto
    
    def _formatear_prediccion(self, pred: Dict) -> str:
        """Formatea la predicción de ventas"""
        if 'error' in pred:
            return f"❌ {pred['error']}"
        
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        
        mes_nombre = meses[pred['mes'] - 1]
        
        texto = f"🔮 <b>PREDICCIÓN DE VENTAS - {mes_nombre.upper()} {pred['año']}</b>\n"
        texto += "━━━━━━━━━━━━━━━━━━━━\n\n"
        texto += f"💰 <b>Venta Total Estimada:</b> ${pred['venta_total_predicha']:,.0f}\n"
        texto += f"📊 <b>Venta Promedio/Día:</b> ${pred['venta_promedio_dia']:,.0f}\n"
        texto += f"📅 <b>Días del mes:</b> {pred['dias_mes']}\n\n"
        
        if 'historico_mismo_mes' in pred and pred['historico_mismo_mes'] > 0:
            texto += f"📈 <b>Histórico mismo mes:</b> ${pred['historico_mismo_mes']:,.0f}\n"
            
            if pred.get('diferencia_vs_historico', 0) >= 0:
                texto += f"✅ Incremento esperado: ${pred['diferencia_vs_historico']:,.0f} "
                texto += f"({pred['variacion_porcentual']:.1f}%)"
            else:
                texto += f"⚠️ Disminución esperada: ${abs(pred['diferencia_vs_historico']):,.0f} "
                texto += f"({abs(pred['variacion_porcentual']):.1f}%)"
        
        if pred.get('metodo') == 'promedio_histórico':
            texto += f"\n\n💡 {pred['nota']}"
        
        return texto
