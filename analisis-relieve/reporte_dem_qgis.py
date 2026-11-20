# =====================================================================
# GENERADOR AUTOMÁTICO DE REPORTE (curvas de nivel + estadísticas + Word)
# Para correr en: QGIS > Complementos > Consola de Python
# =====================================================================

import os
import processing
import numpy as np
from osgeo import gdal
from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ---------------------------------------------------------------
# 1. CONFIGURACIÓN - AJUSTA SOLO ESTA PARTE
# ---------------------------------------------------------------
# Selecciona un DEM previamente recortado y proyectado en metros.
# La elevación debe estar expresada en metros.
from datetime import datetime
from qgis.PyQt.QtWidgets import QFileDialog
from osgeo import osr

dem_input, _ = QFileDialog.getOpenFileName(
    iface.mainWindow(), "Seleccionar DEM preparado", "", "GeoTIFF (*.tif *.tiff)"
)
if not dem_input:
    raise RuntimeError("Selección de DEM cancelada.")

carpeta_base = QFileDialog.getExistingDirectory(
    iface.mainWindow(), "Seleccionar carpeta para los resultados"
)
if not carpeta_base:
    raise RuntimeError("Selección de carpeta cancelada.")

ds_validacion = gdal.Open(dem_input)
if ds_validacion is None:
    raise RuntimeError("No se pudo abrir el DEM.")
crs = osr.SpatialReference()
crs.ImportFromWkt(ds_validacion.GetProjection())
if not crs.IsProjected() or not np.isclose(crs.GetLinearUnits(), 1.0):
    raise ValueError("Reproyecta el DEM a un CRS proyectado en metros antes de ejecutar.")
gt_validacion = ds_validacion.GetGeoTransform()
if gt_validacion[2] != 0 or gt_validacion[4] != 0:
    raise ValueError("El script requiere una cuadrícula sin rotación.")
ds_validacion = None

# Cada ejecución guarda sus resultados en una subcarpeta nueva.
carpeta_salida = os.path.join(
    carpeta_base, "reporte_dem_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
)
os.makedirs(carpeta_salida, exist_ok=False)
curvas_output = os.path.join(carpeta_salida, "curvas_nivel.shp")
word_output   = os.path.join(carpeta_salida, "Reporte_DEM.docx")
imagen_mapa   = os.path.join(carpeta_salida, "vista_mapa.png")

intervalo_curvas = 40  # metros entre curvas (sube a 50-100 si es el raster departamental)
factor_maestra = 5     # cada 5ta curva es "Maestra" -> cada (intervalo_curvas x 5) metros

# ---------------------------------------------------------------
# 2. GENERAR CURVAS DE NIVEL (equivalente a arcpy.ddd.Contour)
# ---------------------------------------------------------------
print("1/6. Generando curvas de nivel...")
processing.run("gdal:contour", {
    'INPUT': dem_input,
    'BAND': 1,
    'INTERVAL': intervalo_curvas,
    'FIELD_NAME': 'ELEV',
    'CREATE_3D': True,
    'IGNORE_NODATA': False,
    'NODATA': None,
    'OFFSET': 0,
    'EXTRA': '',
    'OUTPUT': curvas_output
})

# ---------------------------------------------------------------
# 2b. CLASIFICAR CURVAS MAESTRAS / INTERMEDIAS
# ---------------------------------------------------------------
print("2/6. Clasificando curvas maestras e intermedias...")
from qgis.core import edit, QgsField
from qgis.PyQt.QtCore import QVariant

intervalo_maestra = intervalo_curvas * factor_maestra

vlayer_curvas = QgsVectorLayer(curvas_output, "curvas_nivel", "ogr")
vlayer_curvas.dataProvider().addAttributes([QgsField("TIPO_CURVA", QVariant.String, len=15)])
vlayer_curvas.updateFields()

n_maestras = 0
n_intermedias = 0
with edit(vlayer_curvas):
    for feat in vlayer_curvas.getFeatures():
        cota = feat["ELEV"]
        if round(cota) % intervalo_maestra == 0:
            tipo = "Maestra"
            n_maestras += 1
        else:
            tipo = "Intermedia"
            n_intermedias += 1
        feat["TIPO_CURVA"] = tipo
        vlayer_curvas.updateFeature(feat)

print(f"Curvas clasificadas: {n_maestras} maestras, {n_intermedias} intermedias")

# ---------------------------------------------------------------
# 3. CALCULAR PENDIENTE (equivalente a arcpy.sa.Slope)
# ---------------------------------------------------------------
print("3/6. Calculando mapa de pendientes...")
slope_output = os.path.join(carpeta_salida, "slope.tif")
processing.run("gdal:slope", {
    'INPUT': dem_input,
    'BAND': 1,
    'SCALE': 1,
    'AS_PERCENT': False,
    'COMPUTE_EDGES': False,
    'ZEVENBERGEN': False,
    'OUTPUT': slope_output
})
# ---------------------------------------------------------------
# 4. ESTADÍSTICAS (con GDAL + numpy, igual que la parte de arcpy)
# ---------------------------------------------------------------
print("4/6. Extrayendo estadísticas y calculando área...")
 
ds = gdal.Open(dem_input)
band = ds.GetRasterBand(1)
arr = band.ReadAsArray().astype(float)
nodata = band.GetNoDataValue()
if nodata is not None:
    arr = np.where(arr == nodata, np.nan, arr)
 
arr[band.GetMaskBand().ReadAsArray() == 0] = np.nan
arr[~np.isfinite(arr)] = np.nan
if not np.any(np.isfinite(arr)):
    raise ValueError("El DEM carece de píxeles válidos.")
gt = ds.GetGeoTransform()
pixel_w = abs(gt[1])
pixel_h = abs(gt[5])
 
pixeles_validos = np.count_nonzero(~np.isnan(arr))
area_m2 = pixeles_validos * pixel_w * pixel_h
area_ha = area_m2 / 10000
area_km2 = area_m2 / 1_000_000
 
raster_min = float(np.nanmin(arr))
raster_max = float(np.nanmax(arr))
 
# Percentiles del DEM. Su cálculo conserva los valores extremos originales.
raster_p1 = float(np.nanpercentile(arr, 1))
raster_p99 = float(np.nanpercentile(arr, 99))
 
ds_slope = gdal.Open(slope_output)
slope_arr = ds_slope.GetRasterBand(1).ReadAsArray().astype(float)
slope_nodata = ds_slope.GetRasterBand(1).GetNoDataValue()
if slope_nodata is not None:
    slope_arr = np.where(slope_arr == slope_nodata, np.nan, slope_arr)
slope_arr[ds_slope.GetRasterBand(1).GetMaskBand().ReadAsArray() == 0] = np.nan
slope_arr[~np.isfinite(slope_arr)] = np.nan
if not np.any(np.isfinite(slope_arr)):
    raise ValueError("El ráster de pendiente carece de píxeles válidos.")
slope_mean = float(np.nanmean(slope_arr))
slope_max = float(np.nanmax(slope_arr))
 
# ---------------------------------------------------------------
# 5. IMAGEN DEL MAPA (usando lienzo activo de QGIS)
# ---------------------------------------------------------------
print("5/6. Exportando imagen del mapa...")
# Ya tienes el DEM cargado manualmente en QGIS, solo agregamos las curvas clasificadas
from qgis.core import QgsLineSymbol, QgsSingleSymbolRenderer
 
# Estilo explícito: rojo bien visible, para que no se pierda contra el DEM oscuro
symbol_curvas = QgsLineSymbol.createSimple({'color': 'red', 'width': '0.4'})
vlayer_curvas.setRenderer(QgsSingleSymbolRenderer(symbol_curvas))
vlayer_curvas.triggerRepaint()
 
QgsProject.instance().addMapLayer(vlayer_curvas)
 
canvas = iface.mapCanvas()
canvas.refresh()
canvas.waitWhileRendering()  # espera a que QGIS termine de dibujar antes de la foto
canvas.saveAsImage(imagen_mapa)
 
# ---------------------------------------------------------------
# 6. ARMAR EL REPORTE EN WORD (misma estructura que el video)
# ---------------------------------------------------------------
print("6/6. Generando reporte Word...")
doc = Document()
 
doc.add_heading("Reporte de Análisis Geográfico y MDE", level=0)
doc.add_paragraph(
    "Informe automático con estadísticas de elevación, pendiente, "
    "extensión territorial y modelo de curvas de nivel."
)
 
# --- Parámetros ---
doc.add_heading("1. Parámetros del Procesamiento", level=1)
doc.add_paragraph(f"Intervalo de curvas de nivel: {intervalo_curvas} metros")
doc.add_paragraph(f"Resolución espacial del DEM: {pixel_w:.2f} m x {pixel_h:.2f} m por píxel")
 
# --- Curvas maestras / intermedias ---
doc.add_heading("2. Clasificación de Curvas de Nivel", level=1)
doc.add_paragraph(
    f"Las curvas se generaron cada {intervalo_curvas} m. Cada {factor_maestra}ta curva "
    f"(cada {intervalo_maestra} m) se clasifica como Maestra; el resto como Intermedia."
)
t0 = doc.add_table(rows=1, cols=2)
t0.style = "Light Grid Accent 1"
hdr = t0.rows[0].cells
hdr[0].text, hdr[1].text = "Tipo de Curva", "Cantidad"
for etiqueta, valor in [
    ("Curvas Maestras", str(n_maestras)),
    ("Curvas Intermedias", str(n_intermedias))
]:
    row = t0.add_row().cells
    row[0].text, row[1].text = etiqueta, valor
 
# --- Área ---
doc.add_heading("3. Extensión y Área de Estudio", level=1)
t1 = doc.add_table(rows=1, cols=2)
t1.style = "Light Grid Accent 1"
hdr = t1.rows[0].cells
hdr[0].text, hdr[1].text = "Unidad de Medida", "Valor"
for etiqueta, valor in [
    ("Área en metros cuadrados (m²)", f"{area_m2:,.2f}"),
    ("Área en hectáreas (ha)", f"{area_ha:,.2f}"),
    ("Área en kilómetros cuadrados (km²)", f"{area_km2:.2f}")
]:
    row = t1.add_row().cells
    row[0].text, row[1].text = etiqueta, valor
 
# --- Altitud ---
doc.add_heading("4. Estadísticas de Altitud", level=1)
t2 = doc.add_table(rows=1, cols=2)
t2.style = "Light Grid Accent 1"
hdr = t2.rows[0].cells
hdr[0].text, hdr[1].text = "Métrica", "Valor (m.s.n.m.)"
for etiqueta, valor in [
    ("Altitud Mínima (valor absoluto)", f"{raster_min:.2f}"),
    ("Altitud Máxima (valor absoluto)", f"{raster_max:.2f}"),
    ("Elevación en el percentil 1", f"{raster_p1:.2f}"),
    ("Elevación en el percentil 99", f"{raster_p99:.2f}")
]:
    row = t2.add_row().cells
    row[0].text, row[1].text = etiqueta, valor
 
# --- Pendiente ---
doc.add_heading("5. Estadísticas de Pendiente", level=1)
t3 = doc.add_table(rows=1, cols=2)
t3.style = "Light Grid Accent 1"
hdr = t3.rows[0].cells
hdr[0].text, hdr[1].text = "Métrica", "Valor (grados)"
for etiqueta, valor in [
    ("Pendiente Media", f"{slope_mean:.2f}"),
    ("Pendiente Máxima", f"{slope_max:.2f}")
]:
    row = t3.add_row().cells
    row[0].text, row[1].text = etiqueta, valor
 
doc.add_paragraph()
 
# --- Imagen ---
if os.path.exists(imagen_mapa):
    doc.add_heading("6. Visualización del Relieve y Curvas de Nivel", level=1)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.add_run().add_picture(imagen_mapa, width=Inches(6.0))
 
    p_cap = doc.add_paragraph(
        f"Figura 1: Modelo del relieve con superposición de curvas de nivel cada {intervalo_curvas} m "
        f"(maestras cada {intervalo_maestra} m)."
    )
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.runs[0].font.italic = True
    p_cap.runs[0].font.size = Pt(9.5)
 
doc.add_paragraph()
 
# --- Conclusión ---
p_destacado = doc.add_paragraph()
run_destacado = p_destacado.add_run(
    f"Conclusión: Los píxeles válidos del DEM cubren un área de {area_km2:.2f} km² ({area_ha:,.2f} ha), "
    f"con un rango altitudinal entre los percentiles 1 y 99 entre {raster_p1:.2f} y {raster_p99:.2f} m.s.n.m. "
    f"(valores absolutos extremos: {raster_min:.2f} a {raster_max:.2f} m), "
    f"una pendiente media de {slope_mean:.2f}°, y un total de {n_maestras} curvas maestras "
    f"y {n_intermedias} curvas intermedias generadas cada {intervalo_curvas} m."
)
run_destacado.bold = True
 
doc.save(word_output)
print(f"\n¡PROCESO FINALIZADO CON ÉXITO!")
print(f"Reporte guardado en:\n{word_output}")