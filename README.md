# dashboard-planta-produccion
# Dashboard de supervisión de planta productiva

Proyecto Integrador – Digitalización de plantas productivas
Universidad EAFIT

**Aplicación publicada:** https://NOMBRE-DE-LA-APP.streamlit.app *(reemplazar por el enlace real)*

## Integrantes

| Nombre | Usuario de GitHub |
|---|---|
| Integrante 1 |   Mariana Arrubla Serna |
| Integrante 2 | Gabriela Ballesteros Ochoa  |
| Integrante 3 | Maria José Sanchez  |

## Descripción del proyecto

Dashboard interactivo desarrollado en Python con Streamlit que integra los registros de una planta con tres líneas de producción. Permite supervisar la producción, la calidad, las variables operativas (temperatura, vibración y presión) y los registros de falla, con filtros por línea, turno y rango de fechas.

## Estructura del dashboard

| Sección (pestaña) | Contenido | Requisito |
|---|---|---|
| Barra lateral | Filtros de línea, turno, rango de fechas y agregación temporal | RF-07 |
| Resumen general | 12 KPI y tabla de indicadores por línea | RF-01, RF-02 |
| Producción y calidad | Producción acumulada por línea, evolución temporal, producción por turno; defectos por línea, % de defectos y defectos por turno | RF-03, RF-05 |
| Variables operativas | Tres gráficas temporales independientes (temperatura, vibración, presión) | RF-04 |
| Análisis de fallas | Fallas por línea, evolución temporal, % de fallas por línea, relación variable operativa–falla | RF-06 |
| Datos | Tabla interactiva filtrada y botón de descarga en CSV | RF-08, RF-09 |
| Hallazgos y recomendaciones | Tres hallazgos y tres recomendaciones calculados a partir de los datos | RF-10 |

## Datos

Archivo: `dataset_planta_bigdata.csv` (suministrado por el docente).

| Variable | Tipo | Descripción |
|---|---|---|
| `timestamp` | Fecha y hora | Momento del registro |
| `linea` | Categórica | Línea de producción |
| `turno` | Categórica | Turno de trabajo (mañana, tarde, noche) |
| `operario` | Categórica | Operario responsable |
| `temperatura` | Numérica | Temperatura de operación (unidad no documentada) |
| `vibracion` | Numérica | Nivel de vibración (unidad no documentada) |
| `presion` | Numérica | Presión de operación (unidad no documentada) |
| `produccion` | Entera | Unidades producidas en el registro |
| `defectos` | Entera | Unidades defectuosas en el registro |
| `falla` | Binaria (0/1) | 1 = registro con falla, 0 = sin falla |

Preparación: conversión de `timestamp` a fecha, eliminación de registros duplicados y de fechas no válidas.

## Fórmulas de los indicadores

- **Producción total** = Σ producción
- **Producción promedio por registro** = Σ producción / número de registros
- **Defectos totales** = Σ defectos
- **% de defectos** = Σ defectos / Σ producción × 100 *(supuesto: los defectos forman parte de las unidades producidas)*
- **Registros con falla** = Σ falla
- **% de registros con falla** = Σ falla / número de registros × 100
- **Temperatura, vibración y presión promedio** = media aritmética del periodo filtrado

## Ejecución local

```bash
git clone https://github.com/marianaarrubla013-ops/dashboard-planta-produccion.git
cd dashboard-planta-produccion
pip install -r requirements.txt
streamlit run app.py
```

## Tecnologías

Python, Streamlit, Pandas, Plotly, GitHub y Streamlit Community Cloud.

## Limitaciones

- Las unidades físicas de las variables operativas y de la producción no están documentadas en la fuente.
- Las relaciones entre variables operativas y fallas son asociaciones estadísticas, no relaciones causales comprobadas.
