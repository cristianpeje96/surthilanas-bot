"""
Módulo de integración con Google Sheets
Maneja todas las operaciones de lectura/escritura en Google Drive
"""

import gspread
from google.oauth2.service_account import Credentials
from typing import List, Dict, Optional
from datetime import datetime
import logging
from config import Config

# Configurar logging
logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Gestor de operaciones con Google Sheets"""
    
    def __init__(self):
        """Inicializa la conexión con Google Sheets"""
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = None
        self.ventas_sheet = None
        self.gastos_sheet = None
        self._connect()
    
    def _connect(self) -> None:
        """Establece conexión con Google Sheets"""
        try:
            creds = Credentials.from_service_account_file(
                Config.GOOGLE_CREDENTIALS_FILE,
                scopes=self.scopes
            )
            self.client = gspread.authorize(creds)
            
            # Abrir hojas de cálculo
            self.ventas_sheet = self.client.open_by_key(Config.VENTAS_SHEET_ID).sheet1
            self.gastos_sheet = self.client.open_by_key(Config.GASTOS_SHEET_ID).sheet1
            
            # Inicializar encabezados si están vacíos
            self._init_headers()
            
            logger.info("✅ Conectado exitosamente a Google Sheets")
        except Exception as e:
            logger.error(f"❌ Error al conectar con Google Sheets: {e}")
            raise
    
    def _init_headers(self) -> None:
        """Inicializa los encabezados de las hojas si están vacías"""
        # Encabezados para ventas
        ventas_headers = ['Fecha', 'Número Factura', 'Cliente', 'Monto', 
                         'Medio de Pago', 'Observaciones', 'Timestamp']
        if not self.ventas_sheet.row_values(1):
            self.ventas_sheet.append_row(ventas_headers)
            logger.info("Encabezados de ventas inicializados")
        
        # Encabezados para gastos
        gastos_headers = ['Fecha', 'Categoría', 'Proveedor', 'Monto', 
                         'Medio de Pago', 'Observaciones', 'Timestamp']
        if not self.gastos_sheet.row_values(1):
            self.gastos_sheet.append_row(gastos_headers)
            logger.info("Encabezados de gastos inicializados")
    
    def registrar_venta(self, venta: Dict) -> bool:
        """
        Registra una nueva venta en Google Sheets
        
        Args:
            venta: Dict con keys: fecha, numero_factura, cliente, monto, 
                   medio_pago, observaciones
        
        Returns:
            bool: True si se registró exitosamente
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row = [
                venta.get('fecha', ''),
                venta.get('numero_factura', ''),
                venta.get('cliente', '-'),
                venta.get('monto', 0),
                venta.get('medio_pago', ''),
                venta.get('observaciones', '-'),
                timestamp
            ]
            
            self.ventas_sheet.append_row(row)
            logger.info(f"✅ Venta registrada: {venta.get('numero_factura')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al registrar venta: {e}")
            return False
    
    def registrar_gasto(self, gasto: Dict) -> bool:
        """
        Registra un nuevo gasto en Google Sheets
        
        Args:
            gasto: Dict con keys: fecha, categoria, proveedor, monto, 
                   medio_pago, observaciones
        
        Returns:
            bool: True si se registró exitosamente
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row = [
                gasto.get('fecha', ''),
                gasto.get('categoria', ''),
                gasto.get('proveedor', '-'),
                gasto.get('monto', 0),
                gasto.get('medio_pago', ''),
                gasto.get('observaciones', '-'),
                timestamp
            ]
            
            self.gastos_sheet.append_row(row)
            logger.info(f"✅ Gasto registrado: {gasto.get('categoria')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al registrar gasto: {e}")
            return False
    
    def obtener_ventas(self, fecha_inicio: Optional[str] = None, 
                       fecha_fin: Optional[str] = None) -> List[Dict]:
        """
        Obtiene ventas del período especificado
        
        Args:
            fecha_inicio: Fecha en formato DD/MM/AAAA (opcional)
            fecha_fin: Fecha en formato DD/MM/AAAA (opcional)
        
        Returns:
            List[Dict]: Lista de ventas
        """
        try:
            all_records = self.ventas_sheet.get_all_records()
            
            if not fecha_inicio and not fecha_fin:
                return all_records
            
            # Filtrar por fechas si se especifican
            filtered = []
            for record in all_records:
                fecha_venta = record.get('Fecha', '')
                # Aquí se puede agregar lógica de filtrado por rango de fechas
                filtered.append(record)
            
            return filtered
        except Exception as e:
            logger.error(f"❌ Error al obtener ventas: {e}")
            return []
    
    def obtener_gastos(self, fecha_inicio: Optional[str] = None, 
                       fecha_fin: Optional[str] = None) -> List[Dict]:
        """
        Obtiene gastos del período especificado
        
        Args:
            fecha_inicio: Fecha en formato DD/MM/AAAA (opcional)
            fecha_fin: Fecha en formato DD/MM/AAAA (opcional)
        
        Returns:
            List[Dict]: Lista de gastos
        """
        try:
            all_records = self.gastos_sheet.get_all_records()
            
            if not fecha_inicio and not fecha_fin:
                return all_records
            
            return all_records
        except Exception as e:
            logger.error(f"❌ Error al obtener gastos: {e}")
            return []
    
    def calcular_totales(self, fecha_inicio: Optional[str] = None, 
                        fecha_fin: Optional[str] = None) -> Dict:
        """
        Calcula totales de ventas y gastos
        
        Returns:
            Dict con total_ventas, total_gastos, utilidad
        """
        try:
            ventas = self.obtener_ventas(fecha_inicio, fecha_fin)
            gastos = self.obtener_gastos(fecha_inicio, fecha_fin)
            
            total_ventas = sum(float(v.get('Monto', 0)) for v in ventas)
            total_gastos = sum(float(g.get('Monto', 0)) for g in gastos)
            utilidad = total_ventas - total_gastos
            
            return {
                'total_ventas': total_ventas,
                'total_gastos': total_gastos,
                'utilidad': utilidad,
                'margen': (utilidad / total_ventas * 100) if total_ventas > 0 else 0,
                'num_ventas': len(ventas),
                'num_gastos': len(gastos)
            }
        except Exception as e:
            logger.error(f"❌ Error al calcular totales: {e}")
            return {
                'total_ventas': 0,
                'total_gastos': 0,
                'utilidad': 0,
                'margen': 0,
                'num_ventas': 0,
                'num_gastos': 0
            }

# Instancia global del gestor
sheets_manager = GoogleSheetsManager()
