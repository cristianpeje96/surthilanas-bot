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

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Gestor de operaciones con Google Sheets"""

    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = None
        self.ventas_sheet = None
        self.gastos_sheet = None
        self._connect()

    def _connect(self) -> None:
        try:
            creds = Credentials.from_service_account_file(
                Config.GOOGLE_CREDENTIALS_FILE,
                scopes=self.scopes
            )
            self.client = gspread.authorize(creds)
            self.ventas_sheet = self.client.open_by_key(Config.VENTAS_SHEET_ID).sheet1
            self.gastos_sheet = self.client.open_by_key(Config.GASTOS_SHEET_ID).sheet1

            # Hoja de cierre diario (segunda hoja del spreadsheet de ventas)
            spreadsheet = self.client.open_by_key(Config.VENTAS_SHEET_ID)
            try:
                self.cierre_sheet = spreadsheet.worksheet('Cierre Diario')
            except gspread.WorksheetNotFound:
                self.cierre_sheet = spreadsheet.add_worksheet(
                    title='Cierre Diario', rows=1000, cols=10
                )

            self._init_headers()
            logger.info("✅ Conectado exitosamente a Google Sheets")
        except Exception as e:
            logger.error(f"❌ Error al conectar con Google Sheets: {e}")
            raise

    def _init_headers(self) -> None:
        ventas_headers = ['Fecha', 'Número Factura', 'Cliente', 'Monto',
                         'Medio de Pago', 'Observaciones', 'Timestamp']
        if not self.ventas_sheet.row_values(1):
            self.ventas_sheet.append_row(ventas_headers)

        gastos_headers = ['Fecha', 'Categoría', 'Proveedor', 'Monto',
                         'Medio de Pago', 'Observaciones', 'Timestamp']
        if not self.gastos_sheet.row_values(1):
            self.gastos_sheet.append_row(gastos_headers)

        cierre_headers = ['Fecha', 'Efectivo', 'Transferencia', 'Tarjeta Débito',
                         'Tarjeta Crédito', 'Otro', 'Total del Día', 'Observaciones', 'Timestamp']
        if not self.cierre_sheet.row_values(1):
            self.cierre_sheet.append_row(cierre_headers)

    def registrar_cierre_diario(self, cierre: Dict) -> bool:
        """
        Registra el cierre de ventas del día desglosado por medio de pago

        Args:
            cierre: Dict con keys: fecha, efectivo, transferencia, tarjeta_debito,
                    tarjeta_credito, otro, total, observaciones
        Returns:
            bool: True si se registró exitosamente
        """
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row = [
                cierre.get('fecha', ''),
                cierre.get('efectivo', 0),
                cierre.get('transferencia', 0),
                cierre.get('tarjeta_debito', 0),
                cierre.get('tarjeta_credito', 0),
                cierre.get('otro', 0),
                cierre.get('total', 0),
                cierre.get('observaciones', '-'),
                timestamp
            ]
            self.cierre_sheet.append_row(row)
            logger.info(f"✅ Cierre diario registrado: {cierre.get('fecha')} - Total: {cierre.get('total')}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al registrar cierre diario: {e}")
            return False

    def registrar_venta(self, venta: Dict) -> bool:
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

    def _fecha_en_rango(self, fecha_str: str, inicio: Optional[str], fin: Optional[str]) -> bool:
        """
        FIX BUG 3: Implementación real del filtrado por rango de fechas.
        La versión original simplemente ignoraba inicio y fin.
        """
        if not inicio and not fin:
            return True
        try:
            fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
            if inicio:
                fecha_inicio = datetime.strptime(inicio, '%d/%m/%Y')
                if fecha < fecha_inicio:
                    return False
            if fin:
                fecha_fin = datetime.strptime(fin, '%d/%m/%Y')
                if fecha > fecha_fin:
                    return False
            return True
        except (ValueError, TypeError):
            # Si la fecha no tiene formato válido, incluirla para no silenciar datos
            return True

    def obtener_ventas(self, fecha_inicio: Optional[str] = None,
                       fecha_fin: Optional[str] = None) -> List[Dict]:
        try:
            all_records = self.ventas_sheet.get_all_records()
            if not fecha_inicio and not fecha_fin:
                return all_records
            # FIX BUG 3: filtrado real por fecha
            return [r for r in all_records if self._fecha_en_rango(r.get('Fecha', ''), fecha_inicio, fecha_fin)]
        except Exception as e:
            logger.error(f"❌ Error al obtener ventas: {e}")
            return []

    def obtener_gastos(self, fecha_inicio: Optional[str] = None,
                       fecha_fin: Optional[str] = None) -> List[Dict]:
        try:
            all_records = self.gastos_sheet.get_all_records()
            if not fecha_inicio and not fecha_fin:
                return all_records
            # FIX BUG 3: filtrado real por fecha
            return [r for r in all_records if self._fecha_en_rango(r.get('Fecha', ''), fecha_inicio, fecha_fin)]
        except Exception as e:
            logger.error(f"❌ Error al obtener gastos: {e}")
            return []

    def calcular_totales(self, fecha_inicio: Optional[str] = None,
                        fecha_fin: Optional[str] = None) -> Dict:
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
                'total_ventas': 0, 'total_gastos': 0,
                'utilidad': 0, 'margen': 0,
                'num_ventas': 0, 'num_gastos': 0
            }

    def buscar_venta_por_factura(self, numero_factura: str) -> Optional[Dict]:
        try:
            all_values = self.ventas_sheet.get_all_values()
            for idx, row in enumerate(all_values[1:], start=2):
                if len(row) >= 2 and row[1] == numero_factura:
                    return {
                        'fila': idx,
                        'fecha': row[0] if len(row) > 0 else '',
                        'numero_factura': row[1] if len(row) > 1 else '',
                        'cliente': row[2] if len(row) > 2 else '',
                        'monto': row[3] if len(row) > 3 else '',
                        'medio_pago': row[4] if len(row) > 4 else '',
                        'observaciones': row[5] if len(row) > 5 else '',
                        'timestamp': row[6] if len(row) > 6 else ''
                    }
            return None
        except Exception as e:
            logger.error(f"❌ Error al buscar venta: {e}")
            return None

    def buscar_gasto_por_criterio(self, categoria: str = None,
                                   proveedor: str = None,
                                   fecha: str = None) -> List[Dict]:
        try:
            all_values = self.gastos_sheet.get_all_values()
            resultados = []
            for idx, row in enumerate(all_values[1:], start=2):
                if len(row) < 3:
                    continue
                coincide = True
                if categoria and row[1].lower() != categoria.lower():
                    coincide = False
                if proveedor and proveedor.lower() not in row[2].lower():
                    coincide = False
                if fecha and row[0] != fecha:
                    coincide = False
                if coincide:
                    resultados.append({
                        'fila': idx,
                        'fecha': row[0] if len(row) > 0 else '',
                        'categoria': row[1] if len(row) > 1 else '',
                        'proveedor': row[2] if len(row) > 2 else '',
                        'monto': row[3] if len(row) > 3 else '',
                        'medio_pago': row[4] if len(row) > 4 else '',
                        'observaciones': row[5] if len(row) > 5 else '',
                        'timestamp': row[6] if len(row) > 6 else ''
                    })
            return resultados
        except Exception as e:
            logger.error(f"❌ Error al buscar gastos: {e}")
            return []

    def obtener_ultimo_registro(self, tipo: str) -> Optional[Dict]:
        try:
            sheet = self.ventas_sheet if tipo == 'venta' else self.gastos_sheet
            all_values = sheet.get_all_values()
            if len(all_values) < 2:
                return None
            ultima_fila = len(all_values)
            row = all_values[-1]
            if tipo == 'venta':
                return {
                    'fila': ultima_fila,
                    'fecha': row[0] if len(row) > 0 else '',
                    'numero_factura': row[1] if len(row) > 1 else '',
                    'cliente': row[2] if len(row) > 2 else '',
                    'monto': row[3] if len(row) > 3 else '',
                    'medio_pago': row[4] if len(row) > 4 else '',
                    'observaciones': row[5] if len(row) > 5 else '',
                    'timestamp': row[6] if len(row) > 6 else ''
                }
            else:
                return {
                    'fila': ultima_fila,
                    'fecha': row[0] if len(row) > 0 else '',
                    'categoria': row[1] if len(row) > 1 else '',
                    'proveedor': row[2] if len(row) > 2 else '',
                    'monto': row[3] if len(row) > 3 else '',
                    'medio_pago': row[4] if len(row) > 4 else '',
                    'observaciones': row[5] if len(row) > 5 else '',
                    'timestamp': row[6] if len(row) > 6 else ''
                }
        except Exception as e:
            logger.error(f"❌ Error al obtener último registro: {e}")
            return None

    def editar_venta(self, fila: int, venta: Dict) -> bool:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row = [
                venta.get('fecha', ''),
                venta.get('numero_factura', ''),
                venta.get('cliente', '-'),
                venta.get('monto', 0),
                venta.get('medio_pago', ''),
                venta.get('observaciones', '-'),
                timestamp + ' (editado)'
            ]
            self.ventas_sheet.update(f'A{fila}:G{fila}', [row])
            logger.info(f"✅ Venta editada en fila {fila}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al editar venta: {e}")
            return False

    def editar_gasto(self, fila: int, gasto: Dict) -> bool:
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row = [
                gasto.get('fecha', ''),
                gasto.get('categoria', ''),
                gasto.get('proveedor', '-'),
                gasto.get('monto', 0),
                gasto.get('medio_pago', ''),
                gasto.get('observaciones', '-'),
                timestamp + ' (editado)'
            ]
            self.gastos_sheet.update(f'A{fila}:G{fila}', [row])
            logger.info(f"✅ Gasto editado en fila {fila}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al editar gasto: {e}")
            return False

    def eliminar_registro(self, fila: int, tipo: str) -> bool:
        try:
            sheet = self.ventas_sheet if tipo == 'venta' else self.gastos_sheet
            sheet.delete_rows(fila)
            logger.info(f"✅ {tipo.capitalize()} eliminada de fila {fila}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al eliminar {tipo}: {e}")
            return False

# Instancia global
sheets_manager = GoogleSheetsManager()