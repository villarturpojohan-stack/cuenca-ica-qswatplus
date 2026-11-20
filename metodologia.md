# Notas de reconstrucción

| Fuente | Qué aporta |
| --- | --- |
| Guía Cuenca Ica QSWAT+ | Fragmentos de Earth Engine, código de cuenca 1374, SRTM, escala de 30 m y CRS EPSG:32718. Identifica el DEM recortado como entrada final a QSWAT+. |
| primertrabajo.docx | Contexto del ejercicio y notas de Ica y Cañete. Para Ica registra el error del canal 267, la relectura de mapas y la corrección del ráster de suelo. |
| Captura de `HruLanduseSoilSlopeRepSwat.txt` | Parámetros visibles del reporte y resultados finales. |
| Código «Descarga_DEM» | Referencia de clase con carpeta Rímac y exportación a 90 m. La captura muestra tres imports y el cuerpo hace referencia a `watersheds`, que no aparece con ese nombre entre ellos. |
| Código «operativo» | Ejercicio de Cañete con código 13754, exportación SRTM a 30 m y ejemplos de recorte. Incluye OpenLandMap como capa exploratoria de textura. |

El script usa filterBounds para encontrar cuencas que intersectan el departamento elegido y clip para enmascarar el DEM por la cuenca completa. La cuadrícula del GeoTIFF es rectangular y contiene píxeles enmascarados fuera del polígono. La exportación se configura a 30 m. La zona UTM sur se sugiere a partir del centroide y puede ajustarse en el panel. Los menús son una ampliación actual para reutilizar el flujo. El asset predeterminado procede del script de Cañete y requiere acceso desde la cuenta del usuario. La reconstrucción cubre la descarga del DEM. Los insumos de suelo y cobertura usados históricamente en QSWAT+ procedían del conjunto South America según la guía.
## Cómo leer el 25 %

La guía menciona «Percent of landscape unit». La captura del reporte final indica «Using percentage of subbasin as threshold» y «Multiple HRUs Area option», con umbral del 25 %. Para citar la corrida final se toma como referencia la captura. La configuración exacta de la interfaz queda pendiente de verificar en el proyecto QSWAT+.

| Código de cobertura | Antes de crear HRUs | Después de crear HRUs |
| --- | ---: | ---: |
| BSVG | 67,62 % | 69,64 % |
| TUWO | 20,44 % | 19,18 % |
| SHRB | 11,78 % | 11,18 % |
| URMD | 0,16 % | Sin valor reportado |

La cifra intermedia de 3 249 HRUs aparece en las notas, pero la evidencia disponible no confirma cómo se relaciona con las 561 finales. Para reproducir la corrida completa faltan, entre otros archivos, el proyecto QGIS/QSWAT+, los rásters originales y el reporte de texto.
