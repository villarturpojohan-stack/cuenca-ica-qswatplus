// Reconstrucción ampliada con selección interactiva. Google Earth Engine Code Editor.
// Ruta tomada del script "operativo" compartido por el autor.
var assetCuencas = 'projects/ee-villarturpojohan/assets/Cuencas_Peru';

var carpetaDrive = 'DEM_Cuencas_Peru';
var dem = ee.Image('USGS/SRTMGL1_003').select('elevation');
var departamentos = ee.FeatureCollection('FAO/GAUL/2015/level1')
  .filter(ee.Filter.eq('ADM0_NAME', 'Peru'));
var cuencas = ee.FeatureCollection(assetCuencas)
  .filter(ee.Filter.notNull(['CODIGO']))
  .map(function (f) { return f.set('codigo_texto', ee.String(f.get('CODIGO'))); });
var seleccion = null;
var codigoActual = null;
var revision = 0;
var estado = ui.Label('Cargando departamentos...');
var menuDepartamento = ui.Select({placeholder: 'Departamento', disabled: true});
var menuCuenca = ui.Select({placeholder: 'Cuenca', disabled: true});
var menuUTM = ui.Select({
  items: ['EPSG:32717', 'EPSG:32718', 'EPSG:32719'],
  value: 'EPSG:32718'
});
var boton = ui.Button({label: 'Preparar exportación del DEM', disabled: true});
var panel = ui.Panel({
  widgets: [
    ui.Label('Descarga de DEM por cuenca'),
    ui.Label('Departamento'), menuDepartamento,
    ui.Label('Cuenca que intersecta el departamento'), menuCuenca,
    ui.Label('Proyección UTM sur'), menuUTM,
    ui.Label('El DEM se exporta a 30 m y conserva el contorno completo de la cuenca.'),
    boton, estado
  ],
  style: {width: '330px', position: 'top-left'}
});
Map.add(panel);
Map.setCenter(-75, -10, 5);

menuDepartamento.onChange(function (nombre) {
  var solicitud = ++revision;
  seleccion = null;
  codigoActual = null;
  boton.setDisabled(true);
  menuCuenca.setDisabled(true);
  menuCuenca.setValue(null, false);
  menuCuenca.items().reset([]);
  var departamento = departamentos.filter(ee.Filter.eq('ADM1_NAME', nombre));
  Map.layers().reset([]);
  Map.addLayer(departamento, {color: '48a868'}, nombre);
  Map.centerObject(departamento, 7);
  estado.setValue('Buscando cuencas...');
  var candidatas = cuencas.filterBounds(departamento.geometry());
  var codigos = candidatas.aggregate_array('codigo_texto').distinct().sort();
  codigos.evaluate(function (lista, error) {
    if (solicitud !== revision) return;
    if (error) {
      estado.setValue('No se pudo leer la capa de cuencas. Revisa la ruta y el acceso.');
      print(error);
      return;
    }
    menuCuenca.items().reset(lista);
    menuCuenca.setDisabled(lista.length === 0);
    estado.setValue(lista.length ? 'Elige un código de cuenca.' : 'Sin cuencas disponibles.');
    print('Cuencas de ' + nombre + ' (consulta sus nombres y códigos):', candidatas);
    if (nombre === 'Ica' && lista.indexOf('1374') !== -1) {
      menuCuenca.setValue('1374');
    }
  });
});

menuCuenca.onChange(function (codigo) {
  if (!codigo) return;
  var solicitud = ++revision;
  boton.setDisabled(true);
  seleccion = cuencas.filter(ee.Filter.eq('codigo_texto', codigo));
  codigoActual = codigo;
  var geometria = seleccion.geometry();
  Map.layers().reset([]);
  Map.addLayer(dem.clip(geometria), {
    min: 0, max: 5000, palette: ['233b66', '8ebc9a', 'f5e0b9']
  }, 'DEM de la cuenca ' + codigo);
  Map.addLayer(seleccion, {color: 'e04f49'}, 'Límite de cuenca', false);
  Map.centerObject(seleccion, 8);
  estado.setValue('Calculando la zona UTM según el centro de la cuenca...');
  geometria.centroid(100).coordinates().evaluate(function (centro, error) {
    if (solicitud !== revision) return;
    if (error) {
      estado.setValue('No se pudo leer la geometría.');
      print(error);
      return;
    }
    var zona = Math.floor((centro[0] + 180) / 6) + 1;
    if (zona < 17 || zona > 19 || centro[1] >= 0) {
      estado.setValue('Revisa la geometría. Se esperaba una cuenca de Perú en UTM sur 17, 18 o 19.');
      return;
    }
    menuUTM.setValue('EPSG:327' + zona);
    estado.setValue('Cuenca ' + codigo + ' seleccionada. Revisa el mapa y la zona UTM sugerida.');
    boton.setDisabled(false);
    print('Cuenca seleccionada:', seleccion);
  });
});

boton.onClick(function () {
  if (!seleccion || !codigoActual) return;
  var geom = seleccion.geometry();
  var nombre = 'dem_cuenca_' + codigoActual.replace(/[^a-zA-Z0-9_-]/g, '_');
  Export.image.toDrive({
    image: dem.clip(geom),
    description: nombre,
    fileNamePrefix: nombre,
    folder: carpetaDrive,
    region: geom,
    scale: 30,
    crs: menuUTM.getValue(),
    maxPixels: 1e9,
    fileFormat: 'GeoTIFF'
  });
  estado.setValue('Tarea preparada. Abre Tasks y pulsa Run para enviarla a Drive.');
});

departamentos.aggregate_array('ADM1_NAME').distinct().sort().evaluate(function (lista, error) {
  if (error || !lista || !lista.length) {
    estado.setValue('No se pudieron cargar los departamentos de GAUL 2015.');
    print(error);
    return;
  }
  menuDepartamento.items().reset(lista);
  menuDepartamento.setDisabled(false);
  estado.setValue('Elige un departamento.');
  if (lista.indexOf('Ica') !== -1) menuDepartamento.setValue('Ica');
});
