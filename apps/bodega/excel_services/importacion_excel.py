"""
Service Layer para importacion de datos desde Excel.

Contiene la logica de negocio para importar mantenedores desde archivos Excel.
Sigue Clean Architecture: separacion de responsabilidades.
"""
from typing import List, Dict, Any, Tuple
from openpyxl import load_workbook
from django.core.exceptions import ValidationError
from django.db import transaction


class ImportacionExcelService:
    """
    Service para importacion de datos desde Excel.
    
    Proporciona metodos genericos para:
    - Generar plantillas Excel
    - Validar archivos Excel
    - Importar datos desde Excel
    """
    
    @staticmethod
    def validar_archivo_excel(archivo) -> Tuple[bool, str]:
        """
        Valida que el archivo sea un Excel valido.
        
        Args:
            archivo: Archivo subido
            
        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not archivo:
            return False, "No se proporciono archivo"
        
        if not archivo.name.endswith(('.xlsx', '.xls')):
            return False, "El archivo debe ser un Excel (.xlsx o .xls)"
        
        try:
            wb = load_workbook(archivo, read_only=True)
            wb.close()
            return True, ""
        except Exception as e:
            return False, f"Error al leer el archivo: {str(e)}"
    
    @staticmethod
    def leer_datos_desde_excel(archivo, columnas_esperadas: List[str], fila_inicio: int = 2) -> List[Dict[str, Any]]:
        """
        Lee datos desde un archivo Excel.
        
        Args:
            archivo: Archivo Excel subido
            columnas_esperadas: Lista de nombres de columnas esperadas
            fila_inicio: Fila donde comienzan los datos (default: 2, asumiendo fila 1 es encabezado)
            
        Returns:
            Lista de diccionarios con los datos leidos
        """
        wb = load_workbook(archivo, read_only=True)
        ws = wb.active
        
        datos = []
        
        # Leer encabezados de la primera fila
        encabezados = []
        for cell in ws[1]:
            encabezados.append(cell.value if cell.value else "")
        
        # Validar que las columnas esperadas esten presentes
        columnas_faltantes = [col for col in columnas_esperadas if col not in encabezados]
        if columnas_faltantes:
            wb.close()
            raise ValidationError(f"Columnas faltantes en el archivo: {', '.join(columnas_faltantes)}")
        
        # Leer datos desde la fila de inicio
        for row in ws.iter_rows(min_row=fila_inicio, values_only=False):
            # Saltar filas vacias
            if all(cell.value is None or str(cell.value).strip() == "" for cell in row):
                continue
            
            # Crear diccionario con los datos de la fila
            fila_data = {}
            for idx, header in enumerate(encabezados):
                if idx < len(row):
                    valor = row[idx].value
                    # Convertir None a string vacio
                    fila_data[header] = str(valor).strip() if valor is not None else ""
            
            datos.append(fila_data)
        
        wb.close()
        return datos
    
    @staticmethod
    def importar_marcas(archivo, usuario) -> Tuple[int, int, List[str]]:
        """
        Importa marcas desde un archivo Excel.
        
        Args:
            archivo: Archivo Excel con las marcas
            usuario: Usuario que realiza la importacion
            
        Returns:
            Tuple[int, int, List[str]]: (creadas, actualizadas, errores)
        """
        from apps.bodega.models import Marca
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Descripcion', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):  # Empezar desde fila 2 (despues del encabezado)
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    marca, created = Marca.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
    
    @staticmethod
    def generar_plantilla_marcas() -> bytes:
        """Genera plantilla de marcas con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.bodega.models import Marca
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Marcas"
        
        encabezados = ['Codigo', 'Nombre', 'Descripcion', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        marcas_existentes = Marca.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, marca in enumerate(marcas_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=marca.codigo)
            ws.cell(row=row_idx, column=2, value=marca.nombre)
            ws.cell(row=row_idx, column=3, value=marca.descripcion)
            ws.cell(row=row_idx, column=4, value='SI' if marca.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def generar_plantilla_operaciones() -> bytes:
        """Genera plantilla de operaciones con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.bodega.models import Operacion
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Operaciones"
        
        encabezados = ['Codigo', 'Nombre', 'Tipo', 'Descripcion', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        operaciones_existentes = Operacion.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, operacion in enumerate(operaciones_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=operacion.codigo)
            ws.cell(row=row_idx, column=2, value=operacion.nombre)
            ws.cell(row=row_idx, column=3, value=operacion.tipo)
            ws.cell(row=row_idx, column=4, value=operacion.descripcion)
            ws.cell(row=row_idx, column=5, value='SI' if operacion.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 40
        ws.column_dimensions['E'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def importar_operaciones(archivo, usuario) -> Tuple[int, int, List[str]]:
        """Importa operaciones desde Excel."""
        from apps.bodega.models import Operacion
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Tipo', 'Descripcion', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    tipo = fila.get('Tipo', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    operacion, created = Operacion.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'tipo': tipo,
                            'descripcion': descripcion,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
    
    @staticmethod
    def generar_plantilla_tipos_movimiento() -> bytes:
        """Genera plantilla de tipos de movimiento con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.bodega.models import TipoMovimiento
        
        wb = Workbook()
        ws = wb.active
        ws.title = "TiposMovimiento"
        
        encabezados = ['Codigo', 'Nombre', 'Descripcion', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        tipos_existentes = TipoMovimiento.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, tipo in enumerate(tipos_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=tipo.codigo)
            ws.cell(row=row_idx, column=2, value=tipo.nombre)
            ws.cell(row=row_idx, column=3, value=tipo.descripcion)
            ws.cell(row=row_idx, column=4, value='SI' if tipo.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def importar_tipos_movimiento(archivo, usuario) -> Tuple[int, int, List[str]]:
        """Importa tipos de movimiento desde Excel."""
        from apps.bodega.models import TipoMovimiento
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Descripcion', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    tipo, created = TipoMovimiento.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
    
    # ==================== METODOS PARA SOLICITUDES ====================
    
    @staticmethod
    def generar_plantilla_tipos_solicitud() -> bytes:
        """Genera plantilla de tipos de solicitud con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.solicitudes.models import TipoSolicitud
        
        wb = Workbook()
        ws = wb.active
        ws.title = "TiposSolicitud"
        
        encabezados = ['Codigo', 'Nombre', 'Descripcion', 'RequiereAprobacion', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        tipos_existentes = TipoSolicitud.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, tipo in enumerate(tipos_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=tipo.codigo)
            ws.cell(row=row_idx, column=2, value=tipo.nombre)
            ws.cell(row=row_idx, column=3, value=tipo.descripcion or '')
            ws.cell(row=row_idx, column=4, value='SI' if tipo.requiere_aprobacion else 'NO')
            ws.cell(row=row_idx, column=5, value='SI' if tipo.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def importar_tipos_solicitud(archivo, usuario) -> Tuple[int, int, List[str]]:
        """Importa tipos de solicitud desde Excel."""
        from apps.solicitudes.models import TipoSolicitud
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Descripcion', 'RequiereAprobacion', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    requiere_aprobacion_str = fila.get('RequiereAprobacion', 'SI').strip().upper()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    requiere_aprobacion = requiere_aprobacion_str in ['SI', 'S', 'TRUE', '1']
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    tipo, created = TipoSolicitud.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'requiere_aprobacion': requiere_aprobacion,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
    
    @staticmethod
    def generar_plantilla_estados_solicitud() -> bytes:
        """Genera plantilla de estados de solicitud con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.solicitudes.models import EstadoSolicitud
        
        wb = Workbook()
        ws = wb.active
        ws.title = "EstadosSolicitud"
        
        encabezados = ['Codigo', 'Nombre', 'Descripcion', 'Color', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        estados_existentes = EstadoSolicitud.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, estado in enumerate(estados_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=estado.codigo)
            ws.cell(row=row_idx, column=2, value=estado.nombre)
            ws.cell(row=row_idx, column=3, value=estado.descripcion or '')
            ws.cell(row=row_idx, column=4, value=estado.color)
            ws.cell(row=row_idx, column=5, value='SI' if estado.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def importar_estados_solicitud(archivo, usuario) -> Tuple[int, int, List[str]]:
        """Importa estados de solicitud desde Excel."""
        from apps.solicitudes.models import EstadoSolicitud
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Descripcion', 'Color', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    color = fila.get('Color', '#6c757d').strip()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    estado, created = EstadoSolicitud.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'color': color,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
    
    # ==================== METODOS PARA COMPRAS ====================
    
    @staticmethod
    def generar_plantilla_estados_recepcion() -> bytes:
        """Genera plantilla de estados de recepcion con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.compras.models import EstadoRecepcion
        
        wb = Workbook()
        ws = wb.active
        ws.title = "EstadosRecepcion"
        
        encabezados = ['Codigo', 'Nombre', 'Descripcion', 'Color', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        estados_existentes = EstadoRecepcion.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, estado in enumerate(estados_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=estado.codigo)
            ws.cell(row=row_idx, column=2, value=estado.nombre)
            ws.cell(row=row_idx, column=3, value=estado.descripcion or '')
            ws.cell(row=row_idx, column=4, value=estado.color)
            ws.cell(row=row_idx, column=5, value='SI' if estado.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def importar_estados_recepcion(archivo, usuario) -> Tuple[int, int, List[str]]:
        """Importa estados de recepcion desde Excel."""
        from apps.compras.models import EstadoRecepcion
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Descripcion', 'Color', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    color = fila.get('Color', '#6c757d').strip()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    estado, created = EstadoRecepcion.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'color': color,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
    
    @staticmethod
    def generar_plantilla_tipos_recepcion() -> bytes:
        """Genera plantilla de tipos de recepcion con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.compras.models import TipoRecepcion
        
        wb = Workbook()
        ws = wb.active
        ws.title = "TiposRecepcion"
        
        encabezados = ['Codigo', 'Nombre', 'Descripcion', 'RequiereOrden', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        tipos_existentes = TipoRecepcion.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, tipo in enumerate(tipos_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=tipo.codigo)
            ws.cell(row=row_idx, column=2, value=tipo.nombre)
            ws.cell(row=row_idx, column=3, value=tipo.descripcion or '')
            ws.cell(row=row_idx, column=4, value='SI' if tipo.requiere_orden else 'NO')
            ws.cell(row=row_idx, column=5, value='SI' if tipo.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def importar_tipos_recepcion(archivo, usuario) -> Tuple[int, int, List[str]]:
        """Importa tipos de recepcion desde Excel."""
        from apps.compras.models import TipoRecepcion
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Descripcion', 'RequiereOrden', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    requiere_orden_str = fila.get('RequiereOrden', 'NO').strip().upper()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    requiere_orden = requiere_orden_str in ['SI', 'S', 'TRUE', '1']
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    tipo, created = TipoRecepcion.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'requiere_orden': requiere_orden,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
    
    @staticmethod
    def generar_plantilla_estados_orden_compra() -> bytes:
        """Genera plantilla de estados de orden de compra con datos reales."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from io import BytesIO
        from apps.compras.models import EstadoOrdenCompra
        
        wb = Workbook()
        ws = wb.active
        ws.title = "EstadosOrdenCompra"
        
        encabezados = ['Codigo', 'Nombre', 'Descripcion', 'Color', 'Activo']
        for col_idx, encabezado in enumerate(encabezados, start=1):
            cell = ws.cell(row=1, column=col_idx, value=encabezado)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
        
        # Obtener datos existentes (hasta 10 registros)
        estados_existentes = EstadoOrdenCompra.objects.filter(eliminado=False).order_by('codigo')[:10]
        
        for row_idx, estado in enumerate(estados_existentes, start=2):
            ws.cell(row=row_idx, column=1, value=estado.codigo)
            ws.cell(row=row_idx, column=2, value=estado.nombre)
            ws.cell(row=row_idx, column=3, value=estado.descripcion or '')
            ws.cell(row=row_idx, column=4, value=estado.color)
            ws.cell(row=row_idx, column=5, value='SI' if estado.activo else 'NO')
        
        # Ajustar ancho de columnas
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 40
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 10
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        contenido = output.read()
        output.close()
        
        return contenido
    
    @staticmethod
    def importar_estados_orden_compra(archivo, usuario) -> Tuple[int, int, List[str]]:
        """Importa estados de orden de compra desde Excel."""
        from apps.compras.models import EstadoOrdenCompra
        
        columnas_esperadas = ['Codigo', 'Nombre', 'Descripcion', 'Color', 'Activo']
        datos = ImportacionExcelService.leer_datos_desde_excel(archivo, columnas_esperadas)
        
        creadas = 0
        actualizadas = 0
        errores = []
        
        with transaction.atomic():
            for idx, fila in enumerate(datos, start=2):
                try:
                    codigo = fila.get('Codigo', '').strip()
                    nombre = fila.get('Nombre', '').strip()
                    descripcion = fila.get('Descripcion', '').strip()
                    color = fila.get('Color', '#6c757d').strip()
                    activo_str = fila.get('Activo', 'SI').strip().upper()
                    
                    if not codigo or not nombre:
                        errores.append(f"Fila {idx}: Codigo y Nombre son obligatorios")
                        continue
                    
                    activo = activo_str in ['SI', 'S', 'TRUE', '1', 'ACTIVO']
                    
                    estado, created = EstadoOrdenCompra.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'nombre': nombre,
                            'descripcion': descripcion,
                            'color': color,
                            'activo': activo,
                            'eliminado': False,
                        }
                    )
                    
                    if created:
                        creadas += 1
                    else:
                        actualizadas += 1
                        
                except Exception as e:
                    errores.append(f"Fila {idx}: {str(e)}")
        
        return creadas, actualizadas, errores
