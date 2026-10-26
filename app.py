import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Dashboard planta", layout="wide")

ARCHIVO = "dataset_planta_bigdata.csv"
VARS_OP = ["temperatura", "vibracion", "presion"]
VARS_NUM = ["temperatura", "vibracion", "presion", "produccion", "defectos", "falla"]


@st.cache_data
def cargar_datos(ruta: str) -> pd.DataFrame:
    df = pd.read_csv(ruta)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.drop_duplicates().dropna(subset=["timestamp"])
    df["fecha"] = df["timestamp"].dt.date
    df["hora"] = df["timestamp"].dt.hour
    return df


df = cargar_datos(ARCHIVO)

st.title("Dashboard de desempeño de planta productiva")
st.caption(
    "Las unidades físicas de temperatura, vibración, presión y producción no están "
    "documentadas en la fuente; los valores se reportan sin unidad asignada."
)

# ---------------- Filtros ----------------
st.sidebar.header("Filtros")
op_lineas = sorted(df["linea"].unique())
op_turnos = sorted(df["turno"].unique())
lineas = st.sidebar.multiselect("Línea", op_lineas, default=op_lineas)
turnos = st.sidebar.multiselect("Turno", op_turnos, default=op_turnos)

fmin, fmax = df["fecha"].min(), df["fecha"].max()
rango = st.sidebar.date_input("Rango de fechas", (fmin, fmax), min_value=fmin, max_value=fmax)
if isinstance(rango, (list, tuple)) and len(rango) == 2:
    f_ini, f_fin = rango
else:
    f_ini, f_fin = fmin, fmax

d = df[
    df["linea"].isin(lineas)
    & df["turno"].isin(turnos)
    & (df["fecha"] >= f_ini)
    & (df["fecha"] <= f_fin)
]

if d.empty:
    st.warning("No hay registros para la combinación de filtros seleccionada.")
    st.stop()

# ---------------- KPI ----------------
prod_total = d["produccion"].sum()
def_total = d["defectos"].sum()
fallas = int(d["falla"].sum())
tasa_def = 100 * def_total / prod_total if prod_total else float("nan")
tasa_falla = 100 * fallas / len(d)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Registros", f"{len(d):,}")
c2.metric("Producción total", f"{prod_total:,.0f}")
c3.metric("Tasa de defectos", f"{tasa_def:.2f} %")
c4.metric("Eventos de falla", f"{fallas:,}")
c5.metric("Registros con falla", f"{tasa_falla:.2f} %")

# ---------------- Pestañas ----------------
t_prod, t_cal, t_fal, t_cond, t_datos = st.tabs(
    ["Producción", "Calidad", "Fallas", "Condiciones operativas", "Datos"]
)

with t_prod:
    col1, col2 = st.columns(2)
    por_linea = d.groupby("linea", as_index=False)["produccion"].mean()
    col1.plotly_chart(
        px.bar(por_linea, x="linea", y="produccion", title="Producción media por registro y línea"),
        width="stretch",
    )
    por_turno = d.groupby(["turno", "linea"], as_index=False)["produccion"].mean()
    col2.plotly_chart(
        px.bar(por_turno, x="turno", y="produccion", color="linea", barmode="group",
               title="Producción media por turno"),
        width="stretch",
    )
    diario = d.groupby(["fecha", "linea"], as_index=False)["produccion"].sum()
    st.plotly_chart(
        px.line(diario, x="fecha", y="produccion", color="linea", title="Producción diaria por línea"),
        width="stretch",
    )

with t_cal:
    cal = d.groupby("linea", as_index=False)[["produccion", "defectos"]].sum()
    cal["tasa_defectos_%"] = 100 * cal["defectos"] / cal["produccion"]
    col1, col2 = st.columns(2)
    col1.plotly_chart(
        px.bar(cal, x="linea", y="defectos", title="Defectos totales por línea"),
        width="stretch",
    )
    col2.plotly_chart(
        px.bar(cal, x="linea", y="tasa_defectos_%", title="Tasa de defectos (%) por línea"),
        width="stretch",
    )
    st.plotly_chart(
        px.box(d, x="linea", y="defectos", color="turno", title="Distribución de defectos por línea y turno"),
        width="stretch",
    )

with t_fal:
    fal = d.groupby("linea", as_index=False).agg(fallas=("falla", "sum"), registros=("falla", "size"))
    fal["tasa_falla_%"] = 100 * fal["fallas"] / fal["registros"]
    col1, col2 = st.columns(2)
    col1.plotly_chart(
        px.bar(fal, x="linea", y="fallas", title="Eventos de falla por línea"),
        width="stretch",
    )
    col2.plotly_chart(
        px.bar(fal, x="linea", y="tasa_falla_%", title="Registros con falla (%) por línea"),
        width="stretch",
    )
    var = st.selectbox("Variable operativa", VARS_OP, key="var_falla")
    st.plotly_chart(
        px.box(d, x=d["falla"].astype(str), y=var, color="linea",
               labels={"x": "falla (0 = no, 1 = sí)"},
               title=f"{var} en registros con y sin falla"),
        width="stretch",
    )

with t_cond:
    var = st.selectbox("Variable operativa", VARS_OP, key="var_cond")
    serie = d.groupby(["fecha", "linea"], as_index=False)[var].mean()
    st.plotly_chart(
        px.line(serie, x="fecha", y=var, color="linea", title=f"Promedio diario de {var}"),
        width="stretch",
    )
    col1, col2 = st.columns(2)
    col1.plotly_chart(
        px.histogram(d, x=var, color="linea", barmode="overlay", opacity=0.6,
                     title=f"Distribución de {var}"),
        width="stretch",
    )
    corr = d[VARS_NUM].corr()
    col2.plotly_chart(
        px.imshow(corr, text_auto=".2f", zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
                  title="Correlación de Pearson (variables numéricas)"),
        width="stretch",
    )
    st.caption("La correlación de Pearson solo mide asociación lineal y no implica causalidad.")

with t_datos:
    st.dataframe(d, width="stretch")
    st.download_button(
        "Descargar datos filtrados (CSV)",
        d.to_csv(index=False).encode("utf-8"),
        file_name="datos_filtrados.csv",
        mime="text/csv",
    )
