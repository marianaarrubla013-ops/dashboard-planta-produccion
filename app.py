"""
Dashboard de supervisión de planta productiva
Proyecto Integrador – Digitalización de plantas productivas

Requisitos cubiertos (ver README.md):
RF-01 Estructura y navegación      -> título, descripción y pestañas
RF-02 KPI (mínimo 6)               -> pestaña "Resumen general"
RF-03 Visualización de producción  -> pestaña "Producción y calidad"
RF-04 Variables operativas         -> pestaña "Variables operativas"
RF-05 Análisis de calidad          -> pestaña "Producción y calidad"
RF-06 Análisis de fallas           -> pestaña "Análisis de fallas"
RF-07 Filtros interactivos         -> barra lateral
RF-08 Tabla de datos               -> pestaña "Datos"
RF-09 Descarga de información      -> pestaña "Datos"
RF-10 Hallazgos y recomendaciones  -> pestaña "Hallazgos y recomendaciones"
"""

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------------------
# Configuración general
# --------------------------------------------------------------------------
st.set_page_config(page_title="Dashboard de planta productiva", page_icon="🏭", layout="wide")

ARCHIVO = "dataset_planta_bigdata.csv"
VARS_OP = {"temperatura": "Temperatura", "vibracion": "Vibración", "presion": "Presión"}
ORDEN_TURNOS = ["Mañana", "Manana", "Tarde", "Noche"]
FRECUENCIAS = {"Hora": "h", "Día": "D", "Semana": "W"}


# --------------------------------------------------------------------------
# Carga y preparación de datos (Pandas)
# --------------------------------------------------------------------------
@st.cache_data
def cargar_datos(ruta: str) -> pd.DataFrame:
    df = pd.read_csv(ruta)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).drop_duplicates()
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["fecha"] = df["timestamp"].dt.date
    return df


def ordenar_turnos(turnos):
    """Ordena los turnos como Mañana -> Tarde -> Noche cuando los nombres coinciden."""
    conocidos = [t for t in ORDEN_TURNOS if t in turnos]
    otros = sorted(t for t in turnos if t not in ORDEN_TURNOS)
    return conocidos + otros


def pct(a, b):
    return 100 * a / b if b else float("nan")


def fmt(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


df = cargar_datos(ARCHIVO)
COLUMNAS_ORIGINALES = [c for c in df.columns if c != "fecha"]
TURNOS = ordenar_turnos(df["turno"].unique().tolist())
LINEAS = sorted(df["linea"].unique().tolist())

# --------------------------------------------------------------------------
# RF-01 Título y propósito
# --------------------------------------------------------------------------
st.title("🏭 Dashboard de supervisión de planta productiva")
st.markdown(
    "Este dashboard integra los registros de producción, calidad, variables operativas y fallas "
    "de las líneas de la planta. Su propósito es apoyar la supervisión diaria mediante indicadores "
    "clave, visualizaciones interactivas y filtros por línea, turno y periodo."
)
st.caption(
    "Fuente: archivo `dataset_planta_bigdata.csv` suministrado por el docente. "
    "Las unidades físicas de temperatura, vibración, presión y producción no están documentadas "
    "en la fuente, por lo que los valores se presentan sin unidad."
)

# --------------------------------------------------------------------------
# RF-07 Filtros interactivos (barra lateral)
# --------------------------------------------------------------------------
st.sidebar.header("Filtros")

lineas_sel = st.sidebar.multiselect(
    "Línea de producción", LINEAS, default=LINEAS,
    help="Seleccione una, varias o todas las líneas.",
)
turnos_sel = st.sidebar.multiselect(
    "Turno", TURNOS, default=TURNOS,
    help="Seleccione uno o varios turnos.",
)
fmin, fmax = df["fecha"].min(), df["fecha"].max()
rango = st.sidebar.date_input(
    "Rango de fechas", value=(fmin, fmax), min_value=fmin, max_value=fmax,
    help="Seleccione la fecha inicial y la fecha final del periodo.",
)
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    f_ini, f_fin = rango
elif isinstance(rango, (list, tuple)) and len(rango) == 1:
    f_ini = f_fin = rango[0]
else:
    f_ini = f_fin = rango

st.sidebar.divider()
agregacion = st.sidebar.radio(
    "Agregación temporal de las gráficas", list(FRECUENCIAS), index=1,
    help="Agrupa los registros por hora, día o semana para mejorar la legibilidad.",
)
FREQ = FRECUENCIAS[agregacion]

d = df[
    df["linea"].isin(lineas_sel)
    & df["turno"].isin(turnos_sel)
    & (df["fecha"] >= f_ini)
    & (df["fecha"] <= f_fin)
].copy()

st.sidebar.caption(f"Registros seleccionados: **{fmt(len(d))}** de {fmt(len(df))}")

if d.empty:
    st.warning("No hay registros para la combinación de filtros seleccionada. Ajuste los filtros.")
    st.stop()


def serie_temporal(data, columna, agg):
    """Agrega una columna por periodo y línea según la frecuencia elegida."""
    return (
        data.set_index("timestamp")
        .groupby("linea")[columna]
        .resample(FREQ)
        .agg(agg)
        .reset_index()
    )


# --------------------------------------------------------------------------
# RF-01 Navegación por pestañas
# --------------------------------------------------------------------------
tab_res, tab_pc, tab_var, tab_fal, tab_datos, tab_hall = st.tabs([
    "📊 Resumen general",
    "🏗️ Producción y calidad",
    "🌡️ Variables operativas",
    "⚠️ Análisis de fallas",
    "📋 Datos",
    "💡 Hallazgos y recomendaciones",
])

# ==========================================================================
# 1. RESUMEN GENERAL – RF-02 KPI
# ==========================================================================
with tab_res:
    st.header("Resumen general de la planta")
    st.caption("Los indicadores se recalculan automáticamente con los filtros de la barra lateral.")

    prod_total = d["produccion"].sum()
    def_total = d["defectos"].sum()
    n_reg = len(d)
    n_falla = int(d["falla"].sum())

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Producción total", fmt(prod_total))
    k2.metric("Producción promedio por registro", fmt(d["produccion"].mean(), 1))
    k3.metric("Defectos totales", fmt(def_total))
    k4.metric("Porcentaje de defectos", f"{fmt(pct(def_total, prod_total), 2)} %",
              help="Defectos totales / producción total × 100. Se interpreta como defectos por "
                   "cada 100 unidades producidas.")

    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Registros con falla", fmt(n_falla))
    k6.metric("Porcentaje de registros con falla", f"{fmt(pct(n_falla, n_reg), 2)} %",
              help="Registros con falla = 1 / total de registros × 100")
    k7.metric("Temperatura promedio", fmt(d["temperatura"].mean(), 2))
    k8.metric("Vibración promedio", fmt(d["vibracion"].mean(), 2))

    k9, k10, k11, k12 = st.columns(4)
    k9.metric("Presión promedio", fmt(d["presion"].mean(), 2))
    k10.metric("Total de registros", fmt(n_reg))
    k11.metric("Líneas seleccionadas", len(lineas_sel))
    k12.metric("Días analizados", d["fecha"].nunique())

    st.subheader("Indicadores por línea")
    resumen = d.groupby("linea").agg(
        Registros=("falla", "size"),
        Produccion_total=("produccion", "sum"),
        Defectos=("defectos", "sum"),
        Registros_con_falla=("falla", "sum"),
        Temperatura_prom=("temperatura", "mean"),
        Vibracion_prom=("vibracion", "mean"),
        Presion_prom=("presion", "mean"),
    )
    resumen["% defectos"] = 100 * resumen["Defectos"] / resumen["Produccion_total"]
    resumen["% registros con falla"] = 100 * resumen["Registros_con_falla"] / resumen["Registros"]
    st.dataframe(resumen.round(2), width="stretch")

# ==========================================================================
# 2. PRODUCCIÓN Y CALIDAD – RF-03 y RF-05
# ==========================================================================
with tab_pc:
    st.header("Análisis de producción y calidad")

    # ---- RF-03 Producción ----
    st.subheader("Producción")
    c1, c2 = st.columns(2)

    prod_linea = d.groupby("linea", as_index=False)["produccion"].sum()
    fig = px.bar(prod_linea, x="linea", y="produccion", color="linea", text_auto=",.0f",
                 title="Producción acumulada por línea",
                 labels={"linea": "Línea", "produccion": "Producción acumulada"})
    fig.update_layout(showlegend=False)
    c1.plotly_chart(fig, width="stretch")

    prod_turno = d.groupby("turno", as_index=False)["produccion"].sum()
    fig = px.bar(prod_turno, x="turno", y="produccion", color="turno", text_auto=",.0f",
                 category_orders={"turno": TURNOS},
                 title="Producción acumulada por turno",
                 labels={"turno": "Turno", "produccion": "Producción acumulada"})
    fig.update_layout(showlegend=False)
    c2.plotly_chart(fig, width="stretch")

    prod_t = serie_temporal(d, "produccion", "sum")
    fig = px.line(prod_t, x="timestamp", y="produccion", color="linea", markers=(FREQ != "h"),
                  title=f"Evolución de la producción (agregación: {agregacion.lower()})",
                  labels={"timestamp": "Periodo", "produccion": "Producción", "linea": "Línea"})
    st.plotly_chart(fig, width="stretch")

    prod_tl = d.groupby(["turno", "linea"], as_index=False)["produccion"].sum()
    fig = px.bar(prod_tl, x="turno", y="produccion", color="linea", barmode="group",
                 category_orders={"turno": TURNOS},
                 title="Producción por turno y línea",
                 labels={"turno": "Turno", "produccion": "Producción acumulada", "linea": "Línea"})
    st.plotly_chart(fig, width="stretch")

    st.divider()

    # ---- RF-05 Calidad ----
    st.subheader("Calidad")
    cal = d.groupby("linea", as_index=False)[["produccion", "defectos"]].sum()
    cal["pct_defectos"] = 100 * cal["defectos"] / cal["produccion"]

    c1, c2 = st.columns(2)
    fig = px.bar(cal, x="linea", y="defectos", color="linea", text_auto=",.0f",
                 title="Cantidad de defectos por línea",
                 labels={"linea": "Línea", "defectos": "Defectos"})
    fig.update_layout(showlegend=False)
    c1.plotly_chart(fig, width="stretch")

    fig = px.bar(cal, x="linea", y="pct_defectos", color="linea", text_auto=".2f",
                 title="Porcentaje de defectos por línea",
                 labels={"linea": "Línea", "pct_defectos": "% defectos"})
    fig.update_layout(showlegend=False)
    c2.plotly_chart(fig, width="stretch")

    cal_t = d.groupby("turno", as_index=False)[["produccion", "defectos"]].sum()
    cal_t["pct_defectos"] = 100 * cal_t["defectos"] / cal_t["produccion"]
    c1, c2 = st.columns(2)
    fig = px.bar(cal_t, x="turno", y="defectos", color="turno", text_auto=",.0f",
                 category_orders={"turno": TURNOS},
                 title="Defectos registrados por turno",
                 labels={"turno": "Turno", "defectos": "Defectos"})
    fig.update_layout(showlegend=False)
    c1.plotly_chart(fig, width="stretch")

    fig = px.bar(cal_t, x="turno", y="pct_defectos", color="turno", text_auto=".2f",
                 category_orders={"turno": TURNOS},
                 title="Porcentaje de defectos por turno",
                 labels={"turno": "Turno", "pct_defectos": "% defectos"})
    fig.update_layout(showlegend=False)
    c2.plotly_chart(fig, width="stretch")

    n_anom = int((df["defectos"] > df["produccion"]).sum())
    st.caption(
        "Porcentaje de defectos = defectos / producción × 100, interpretado como defectos por cada "
        f"100 unidades producidas. En el conjunto original, {fmt(n_anom)} registros "
        f"({fmt(pct(n_anom, len(df)), 2)} %) tienen más defectos que unidades producidas, por lo que "
        "el indicador es una tasa y no una proporción estricta de piezas defectuosas. Estos registros "
        "se conservan porque forman parte de los datos originales."
    )

# ==========================================================================
# 3. VARIABLES OPERATIVAS – RF-04
# ==========================================================================
with tab_var:
    st.header("Monitoreo de variables operativas")
    st.caption(f"Promedio por {agregacion.lower()} y línea. La agregación se cambia en la barra lateral.")

    for col, nombre in VARS_OP.items():
        serie = serie_temporal(d, col, "mean")
        fig = px.line(serie, x="timestamp", y=col, color="linea", markers=(FREQ != "h"),
                      title=f"{nombre} promedio a lo largo del tiempo",
                      labels={"timestamp": "Periodo", col: nombre, "linea": "Línea"})
        st.plotly_chart(fig, width="stretch")

    st.subheader("Estadísticas descriptivas del periodo seleccionado")
    desc = d.groupby("linea")[list(VARS_OP)].agg(["mean", "std", "min", "max"]).round(2)
    st.dataframe(desc, width="stretch")

# ==========================================================================
# 4. ANÁLISIS DE FALLAS – RF-06
# ==========================================================================
with tab_fal:
    st.header("Análisis de fallas")

    fal = d.groupby("linea", as_index=False).agg(fallas=("falla", "sum"), registros=("falla", "size"))
    fal["pct_falla"] = 100 * fal["fallas"] / fal["registros"]

    c1, c2 = st.columns(2)
    fig = px.bar(fal, x="linea", y="fallas", color="linea", text_auto=",.0f",
                 title="Cantidad de registros con falla por línea",
                 labels={"linea": "Línea", "fallas": "Registros con falla"})
    fig.update_layout(showlegend=False)
    c1.plotly_chart(fig, width="stretch")

    fig = px.bar(fal, x="linea", y="pct_falla", color="linea", text_auto=".2f",
                 title="Porcentaje de registros con falla por línea",
                 labels={"linea": "Línea", "pct_falla": "% registros con falla"})
    fig.update_layout(showlegend=False)
    c2.plotly_chart(fig, width="stretch")

    fal_t = serie_temporal(d, "falla", "sum")
    fig = px.line(fal_t, x="timestamp", y="falla", color="linea", markers=(FREQ != "h"),
                  title=f"Evolución de los registros con falla (agregación: {agregacion.lower()})",
                  labels={"timestamp": "Periodo", "falla": "Registros con falla", "linea": "Línea"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Relación entre variables operativas y fallas")
    var = st.selectbox("Variable operativa", list(VARS_OP), format_func=VARS_OP.get)
    nombre = VARS_OP[var]

    c1, c2 = st.columns(2)
    d_box = d.assign(estado=d["falla"].map({0: "Sin falla", 1: "Con falla"}))
    fig = px.box(d_box, x="estado", y=var, color="estado",
                 category_orders={"estado": ["Sin falla", "Con falla"]},
                 title=f"Distribución de {nombre.lower()} en registros con y sin falla",
                 labels={"estado": "", var: nombre})
    fig.update_layout(showlegend=False)
    c1.plotly_chart(fig, width="stretch")

    # Porcentaje de fallas por rangos (quintiles) de la variable seleccionada
    try:
        d_bins = d.assign(rango=pd.qcut(d[var], q=5, duplicates="drop"))
        tasa = d_bins.groupby("rango", observed=True)["falla"].mean().mul(100).reset_index()
        tasa["rango"] = tasa["rango"].astype(str)
        fig = px.bar(tasa, x="rango", y="falla", text_auto=".2f",
                     title=f"% de registros con falla por rango de {nombre.lower()} (quintiles)",
                     labels={"rango": f"Rango de {nombre.lower()}", "falla": "% registros con falla"})
        c2.plotly_chart(fig, width="stretch")
    except ValueError:
        c2.info("No hay suficientes valores distintos para construir rangos con este filtro.")

    medianas = d.groupby("falla")[var].median()
    if {0, 1}.issubset(medianas.index):
        st.caption(
            f"Mediana de {nombre.lower()}: {fmt(medianas[0], 2)} sin falla vs. "
            f"{fmt(medianas[1], 2)} con falla. Una asociación no implica causalidad."
        )

# ==========================================================================
# RF-08 Tabla de datos y RF-09 Descarga
# ==========================================================================
with tab_datos:
    st.header("Tabla de datos")
    st.caption("Registros del archivo CSV correspondientes a los filtros aplicados. "
               "La tabla permite ordenar por columna, buscar y ampliar.")
    tabla = d[COLUMNAS_ORIGINALES]
    st.dataframe(tabla, width="stretch", hide_index=True, height=450)
    st.write(f"Registros mostrados: **{fmt(len(tabla))}**")

    st.subheader("Descarga de información")
    st.download_button(
        label="⬇️ Descargar datos filtrados (CSV)",
        data=tabla.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"datos_filtrados_{f_ini}_{f_fin}.csv",
        mime="text/csv",
        type="primary",
    )

# ==========================================================================
# RF-10 Hallazgos y recomendaciones (calculados sobre el conjunto completo)
# ==========================================================================
with tab_hall:
    st.header("Hallazgos y recomendaciones")
    st.caption("Calculados sobre el conjunto de datos completo, para que no cambien con los filtros.")

    g_lin = df.groupby("linea").agg(prod=("produccion", "sum"), defe=("defectos", "sum"),
                                    fallas=("falla", "sum"), reg=("falla", "size"))
    g_lin["pct_def"] = 100 * g_lin["defe"] / g_lin["prod"]
    g_lin["pct_falla"] = 100 * g_lin["fallas"] / g_lin["reg"]

    g_tur = df.groupby("turno").agg(prod=("produccion", "sum"), defe=("defectos", "sum"))
    g_tur["pct_def"] = 100 * g_tur["defe"] / g_tur["prod"]

    l_max, l_min = g_lin["prod"].idxmax(), g_lin["prod"].idxmin()
    dif_prod = pct(g_lin.loc[l_max, "prod"] - g_lin.loc[l_min, "prod"], g_lin.loc[l_min, "prod"])
    t_max_def, t_min_def = g_tur["pct_def"].idxmax(), g_tur["pct_def"].idxmin()
    l_max_def = g_lin["pct_def"].idxmax()
    l_max_fal = g_lin["pct_falla"].idxmax()

    # Variable operativa con mayor diferencia relativa de medianas entre registros con y sin falla
    dif_var = {}
    for col in VARS_OP:
        m = df.groupby("falla")[col].median()
        if {0, 1}.issubset(m.index) and m[0] != 0:
            dif_var[col] = 100 * (m[1] - m[0]) / abs(m[0])
    v_key = max(dif_var, key=lambda k: abs(dif_var[k])) if dif_var else "vibracion"
    v_nom = VARS_OP[v_key]
    med = df.groupby("falla")[v_key].median()
    corr_def = df[[v_key, "defectos"]].corr().iloc[0, 1]
    umbral = df.loc[df["falla"] == 0, v_key].quantile(0.90)
    pct_sobre = pct(((df["falla"] == 1) & (df[v_key] > umbral)).sum(), (df["falla"] == 1).sum())

    st.subheader("Hallazgos")
    st.markdown(
        f"**1. Producción.** La línea **{l_max}** acumula la mayor producción "
        f"({fmt(g_lin.loc[l_max, 'prod'])}), un {fmt(dif_prod, 1)} % más que la línea **{l_min}** "
        f"({fmt(g_lin.loc[l_min, 'prod'])})."
    )
    st.markdown(
        f"**2. Calidad.** La línea **{l_max_def}** presenta el mayor porcentaje de defectos "
        f"({fmt(g_lin.loc[l_max_def, 'pct_def'], 2)} %). Por turno, **{t_max_def}** registra "
        f"{fmt(g_tur.loc[t_max_def, 'pct_def'], 2)} % de defectos frente a "
        f"{fmt(g_tur.loc[t_min_def, 'pct_def'], 2)} % en **{t_min_def}**."
    )
    st.markdown(
        f"**3. Fallas y condiciones operativas.** La línea **{l_max_fal}** tiene el mayor porcentaje "
        f"de registros con falla ({fmt(g_lin.loc[l_max_fal, 'pct_falla'], 2)} %). Entre las variables "
        f"operativas, **{v_nom.lower()}** muestra la mayor diferencia: mediana de {fmt(med[1], 2)} en "
        f"registros con falla frente a {fmt(med[0], 2)} sin falla ({fmt(dif_var.get(v_key, 0), 1)} %). "
        f"Su correlación con los defectos es r = {fmt(corr_def, 2)}."
    )

    st.subheader("Recomendaciones")
    st.markdown(
        f"**1. Alerta temprana por {v_nom.lower()}.** Definir un umbral de alerta en "
        f"{fmt(umbral, 2)} (percentil 90 de los registros sin falla). El "
        f"{fmt(pct_sobre, 1)} % de los registros con falla supera ese valor. Priorizar inspección "
        f"y mantenimiento preventivo en la línea **{l_max_fal}**."
    )
    st.markdown(
        f"**2. Control de calidad en el turno {t_max_def} y la línea {l_max_def}.** Revisar "
        f"procedimientos, ajustes de arranque y frecuencia de inspección en ese turno, y comparar "
        f"sus prácticas con el turno **{t_min_def}**, que tiene el menor porcentaje de defectos."
    )
    st.markdown(
        f"**3. Seguimiento periódico con el dashboard.** Revisar semanalmente los KPI de producción, "
        f"% de defectos y % de registros con falla por línea, e investigar las causas de la menor "
        f"producción de la línea **{l_min}** (paradas, velocidad o disponibilidad)."
    )
    st.caption("Limitaciones: las unidades físicas no están documentadas y las relaciones observadas "
               "son asociaciones estadísticas, no relaciones causales comprobadas.")
