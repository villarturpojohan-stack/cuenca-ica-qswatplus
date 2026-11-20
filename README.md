# Delimitación de la cuenca del río Ica y generación de HRUs

Proyecto de aprendizaje de Ingeniería Ambiental aplicado a la cuenca del río Ica, Perú. Usé Google Earth Engine, QGIS y QSWAT+ para preparar un modelo digital de elevación (DEM), delimitar la red de drenaje y generar unidades de respuesta hidrológica (HRUs). Cada HRU representa una combinación de uso del suelo, tipo de suelo y clase de pendiente.

| Indicador | Resultado del ejercicio |
| --- | ---: |
| Área del modelo | 726 160,23 ha |
| Subcuencas | 27 |
| Canales | 279 |
| Unidades de paisaje (LSUs) | 279 |
| HRUs finales | 561 |
| Suelo desnudo o vegetación escasa (BSVG) | 69,64 % después del filtro |

La [captura del reporte de QSWAT+](evidencia/reporte-hrus.png) respalda los resultados. Los valores entre paréntesis en ese reporte corresponden a la etapa previa a la creación de HRUs.

## Cómo trabajé

1. Preparé en Earth Engine el DEM SRTM a 30 m en UTM 18S (EPSG:32718). Según mi guía, primero exporté una zona que cubría el departamento de Ica y luego generé un DEM por cuenca a partir de la capa hidrográfica.
2. En QSWAT+ probé la delimitación con el DEM departamental. El cálculo de drenaje no se completó con los recursos disponibles, así que usé `dem_cuenca_1374.tif`, recortado al contorno hidrográfico de Ica. La guía registra un punto de salida en el tramo inferior y una tolerancia de ajuste de 300 m. Las coordenadas y los umbrales finales de drenaje están pendientes de recuperar.
3. Preparé los rásters de uso y tipo de suelo a partir del conjunto de ejemplo South America (`sa_land` y `sa_soil`) de [SWAT](https://swat.tamu.edu/data). Tras corregir parte de los vacíos del suelo, volví a leer los rásters con «Read from maps» y generé las HRUs con un filtro por área.
4. Preparé el mapa a partir de «Actual HRUs», con simbología categórica por el campo `Landuse`.

## Qué ocurrió con los datos de suelo

QSWAT+ avisó que faltaban datos de cultivo o suelo para el canal 267 de la subcuenca 27. Según la guía, al aplicar [Fill NoData de GDAL](https://gdal.org/en/stable/programs/gdal_fillnodata.html) a `soil_extension.tif` y volver a leer `soil_extension_completo.tif`, el error dejó de aparecer. Mantuve el punto de salida. La prueba de relleno en uso del suelo dejó vacíos, que quedaron registrados como una limitación.

Los píxeles rellenados son estimaciones. Quedan pendientes los parámetros del relleno y la validación de los códigos de suelo asignados. El ejercicio se realizó sin verificación de campo y documenta la preparación espacial del modelo hasta la generación de HRUs.

## Script reconstruido de Earth Engine

El [script de Ica](gee/ica_dem_srtm.js) reconstruye la preparación del DEM a partir de la guía y los materiales de clase facilitados por mi profesor y el ejercicio de Cañete que sirvió de referencia. El archivo original sigue pendiente de localizar.

1. Abre el Code Editor de Earth Engine y reemplaza todo el código anterior por el contenido de gee/ica_dem_srtm.js.
2. Pulsa Run. En el panel del mapa elige un departamento y después el código de una cuenca. La consola permite consultar los nombres y atributos de las cuencas disponibles.
3. Revisa el contorno y la proyección UTM sugerida según el centro de la cuenca. Puedes cambiar la zona entre 17S, 18S y 19S. Para Ica se propone 18S.
4. Pulsa **Preparar exportación del DEM**. En **Tasks**, pulsa **Run** para iniciar la descarga a la carpeta DEM_Cuencas_Peru de Google Drive.

La ruta de cuencas está tomada del script operativo del autor. El autor confirmó la comprobación del script en Earth Engine. Si falla, configura assetCuencas con una capa accesible que tenga el campo CODIGO. El selector busca las cuencas que intersectan el departamento y exporta su geometría completa. Los menús son una ampliación actual de la reconstrucción. La exportación aplica la máscara de cuenca registrada en la guía histórica.

Se comprobó la sintaxis JavaScript y el autor confirmó que probó el script en Earth Engine. La comparación exacta con el GeoTIFF histórico queda pendiente de documentar.
El script conserva las fuentes de la guía, [SRTM](https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003) y [FAO GAUL 2015](https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2015_level1). Si GAUL 2015 deja de estar disponible, la alternativa requiere adaptar el filtro a la capa administrativa que se use. 

[Decisiones de reconstrucción y detalles de la evidencia](metodologia.md)
