import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

# Intentar importar fpdf, si no está disponible, desactivar PDF
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    st.warning("⚠️ Módulo 'fpdf' no instalado. Para generar PDFs, ejecuta: pip install fpdf")

# Inicializar session_state
st.session_state.setdefault('results_ready', False)
st.session_state.setdefault('pdf_data', {})

# Datos de mortalidad - CORREGIDOS para tener la misma longitud
data = {
    'x': list(range(12, 101)),  # 12 a 100 (89 valores)
    'lx': [10000000.00, 9996040.00, 9991772, 9987175, 9982232, 9976911, 9971175, 9965002, 9958356, 9951206, 9943513, 9935230, 9926319, 9916730, 9906406, 9895301, 9883358, 9870509, 9856691, 9841827, 9825844, 9808658, 9790179, 9770314, 9748956, 9726007, 9701352, 9674867, 9646423, 9615883, 9583092, 9547903, 9510151, 9469657, 9426238, 9379692, 9329820, 9276407, 9219227, 9158039, 9092605, 9022655, 8947930, 8868159, 8783051, 8692322, 8595672, 8492808, 8383429, 8267235, 8143937, 8013243, 7874895, 7728626, 7574208, 7411439, 7240153, 7060228, 6871578, 6674199, 6468140.00, 6253527, 6030583, 5799611, 5561038, 5315385, 5063308, 4805576, 4543100, 4276911, 4008175, 3738177, 3468318, 3200088, 2935067, 2674876, 2421164, 2175571, 1939687, 1715009, 1502902, 1304559, 1120960, 952835, 800645, 664559, 544452, 439906.00, 350237],
    'dx': [3960.00, 4268, 4596, 4944, 5321, 5737, 6172, 6647, 7150, 7692, 8283, 8912, 9589, 10323, 11105, 11944, 12848, 13819, 14864, 15983, 17185, 18480, 19864, 21358, 22949, 24655, 26485, 28444, 30541, 32790, 35189, 37752, 40494, 43418, 46547, 49872, 53413, 57180, 61188, 65434, 69949, 74726, 79771, 85108, 90729, 96650, 102864, 109379, 116194, 123298, 130694, 138349, 146268, 154418, 162770, 171286, 179925, 188649, 197379, 206059, 214613, 222944, 230971, 238573, 245653, 252077, 257733, 262476, 266189, 268735, 269999, 269859, 268229, 265022, 260191, 253712, 245593, 235884, 224678, 212107, 198342, 183600, 168125, 152190, 136086, 120108, 104546, 89669, 350237]
}

# Función para calcular valores conmutados
def calcular_valores_conmutados(i):
    df = pd.DataFrame(data)
    df['Dx'] = df['lx'] * ((1 + i) ** (-df['x']))
    df['Cx'] = df['dx'] * ((1 + i) ** (-(df['x'] + 1)))
    df['Nx'] = df['Dx'][::-1].cumsum()[::-1]
    df['Mx'] = df['Cx'][::-1].cumsum()[::-1]
    return df

# Función para obtener valor conmutado
def get_valor(df, edad, columna):
    try:
        return df[df['x'] == edad][columna].values[0]
    except:
        return 0

# Cálculo de anualidades
def calc_anualidad_anticipada_vitalicia(df, edad, i):
    Dx = get_valor(df, edad, 'Dx')
    Nx = get_valor(df, edad, 'Nx')
    return Nx / Dx if Dx != 0 else 0

def calc_anualidad_anticipada_temporal(df, edad, n, i):
    Dx = get_valor(df, edad, 'Dx')
    Nx = get_valor(df, edad, 'Nx')
    Nx_n = get_valor(df, edad + n, 'Nx')
    return (Nx - Nx_n) / Dx if Dx != 0 else 0

# PNU - Prima Neta Única
def calc_PNU_vitalicia(df, edad, i):
    Dx = get_valor(df, edad, 'Dx')
    Mx = get_valor(df, edad, 'Mx')
    return Mx / Dx if Dx != 0 else 0

def calc_PNU_temporal(df, edad, n, i):
    Dx = get_valor(df, edad, 'Dx')
    Mx = get_valor(df, edad, 'Mx')
    Mx_n = get_valor(df, edad + n, 'Mx')
    return (Mx - Mx_n) / Dx if Dx != 0 else 0

def calc_PNU_dotal(df, edad, n, i):
    Dx = get_valor(df, edad, 'Dx')
    Dx_n = get_valor(df, edad + n, 'Dx')
    Mx = get_valor(df, edad, 'Mx')
    Mx_n = get_valor(df, edad + n, 'Mx')
    return ((Mx - Mx_n) / Dx + Dx_n / Dx) if Dx != 0 else 0

# Prima Comercial
def calc_prima_comercial(P, a_pago, a_seguro, alpha, gamma, beta, k):
    numerador = P * a_pago + alpha + gamma * a_seguro
    denominador = a_pago * (1 - k / a_pago - beta)
    return numerador / denominador if denominador != 0 else 0

# Valor de Rescate
def calc_valor_rescate(A_actual, P, a_restante, kB, a_pago_original):
    # proteger división por cero
    if a_pago_original == 0:
        return A_actual - P * a_restante
    return A_actual - P * a_restante - (kB * a_restante / a_pago_original)

# Seguro Saldado
def calc_seguro_saldado(V_rescate, A_nueva):
    return V_rescate / A_nueva if A_nueva != 0 else 0

# Seguro Prorrogado
def calc_seguro_prorrogado(df, V_rescate, SA, edad_actual, tipo_seguro, n_restante=None):
    edad_x = edad_actual
    Dx_actual = get_valor(df, edad_x, 'Dx')
    Mx_actual = get_valor(df, edad_x, 'Mx')
    if Dx_actual == 0:
        return 0, 0, 0
    M_buscado = Mx_actual - (V_rescate / SA) * Dx_actual
    for edad in range(edad_x + 1, 100):
        M_edad_ant = get_valor(df, edad - 1, 'Mx')
        M_edad = get_valor(df, edad, 'Mx')
        if M_buscado <= M_edad_ant and M_buscado >= M_edad:
            edad_encontrada = edad - 1
            if M_edad_ant != M_edad:
                I = ((M_edad_ant - M_buscado) / (M_edad_ant - M_edad)) * 365
            else:
                I = 0
            años = edad_encontrada - edad_x
            dias_totales = I
            meses = int(dias_totales / 30)
            dias_restantes = dias_totales - (meses * 30)
            dias = round(dias_restantes)
            if dias >= 30:
                meses += 1
                dias -= 30
            if meses >= 12:
                años += meses // 12
                meses = meses % 12
            return años, meses, dias
    return 0, 0, 0

# Configuración de Streamlit
st.set_page_config(page_title="Valores Garantizados - Seguros", layout="wide")
st.title("📊 Calculadora de Valores Garantizados")
st.markdown("### Sistema de cálculo para Seguros de Vida")

# Sidebar para parámetros generales
with st.sidebar:
    st.header("⚙️ Parámetros Generales")
    tipo_seguro = st.selectbox("Tipo de Seguro", ["Vitalicio", "Temporal", "Dotal (Mixto)"])
    suma_asegurada = st.number_input("Suma Asegurada ($)", min_value=10000.0, value=100000.0, step=10000.0, help="Mínimo $10,000")
    tasa_interes = st.number_input("Tasa de Interés (%)", min_value=0.01, max_value=10.0, value=4.0, step=0.1, help="Mayor a 0% y menor o igual a 10%")
    edad = st.number_input("Edad del Asegurado", min_value=12, max_value=99, value=40, step=1)
    tipo_recargo = st.radio("Tipo de Recargos", ["Mínimos", "Máximos"])
    t_anos = st.number_input("Año de Cálculo (t)", min_value=1, max_value=50, value=10, step=1, help="Año en el que se calculan los valores garantizados")

# Parámetros específicos según tipo de seguro
st.header("📋 Parámetros del Seguro")
col1, col2 = st.columns(2)
with col1:
    if tipo_seguro == "Vitalicio":
        plazo_seguro = 100 - edad
        st.info(f"Plazo del Seguro: Vitalicio (hasta edad 100)")
        plazo_pago = st.number_input("Plazo de Pago de Primas (años)", min_value=1, max_value=plazo_seguro, value=min(20, plazo_seguro), step=1)
    elif tipo_seguro == "Temporal":
        plazo_seguro = st.number_input("Plazo del Seguro (años)", min_value=1, max_value=100 - edad, value=20, step=1)
        plazo_pago = st.number_input("Plazo de Pago de Primas (años)", min_value=1, max_value=plazo_seguro, value=min(15, plazo_seguro), step=1)
    else:
        plazo_seguro = st.number_input("Plazo del Seguro (años)", min_value=1, max_value=100 - edad, value=20, step=1)
        plazo_pago = st.number_input("Plazo de Pago de Primas (años)", min_value=1, max_value=plazo_seguro, value=min(15, plazo_seguro), step=1)

with col2:
    st.markdown("**Recargos Aplicables:**")
    if tipo_seguro in ["Vitalicio", "Dotal (Mixto)"]:
        if tipo_recargo == "Mínimos":
            gamma = 5 / 1000
            beta = 0.05
            k = min(plazo_pago * 0.05, 1.0)
        else:
            gamma = 7 / 1000
            beta = 0.07
            k = min(plazo_pago * 0.05, 1.0)
    else:
        if tipo_recargo == "Mínimos":
            gamma = 2 / 1000
            beta = 0.05
            k = min(plazo_pago * 0.03, 0.6)
        else:
            gamma = 3 / 1000
            beta = 0.07
            k = min(plazo_pago * 0.03, 0.6)
    alpha = 0
    st.write(f"• γ (Administración): {gamma:.6f}")
    st.write(f"• β (Cobranza): {beta:.2f}")
    st.write(f"• k (Adquisición): {k:.4f}")
    st.write(f"• α (Honorarios): {alpha}")

# Botón para calcular
if st.button("🔢 CALCULAR VALORES GARANTIZADOS", type="primary", key="btn_calcular"):
    i = tasa_interes / 100
    df_conmutados = calcular_valores_conmutados(i)
    st.header("📊 RESULTADOS")
    tab1, tab2, tab3, tab4 = st.tabs(["Prima Comercial", "Valor de Rescate", "Seguro Saldado", "Seguro Prorrogado"])

    # 1. PRIMA COMERCIAL
    with tab1:
        st.subheader("💰 Prima Comercial")
        if tipo_seguro == "Vitalicio":
            PNU = calc_PNU_vitalicia(df_conmutados, edad, i)
            a_pago = calc_anualidad_anticipada_vitalicia(df_conmutados, edad, i)
            a_seguro = a_pago
            P = PNU / a_pago if a_pago != 0 else 0
        elif tipo_seguro == "Temporal":
            PNU = calc_PNU_temporal(df_conmutados, edad, plazo_seguro, i)
            a_pago = calc_anualidad_anticipada_temporal(df_conmutados, edad, plazo_pago, i)
            a_seguro = calc_anualidad_anticipada_temporal(df_conmutados, edad, plazo_seguro, i)
            Nx = get_valor(df_conmutados, edad, 'Nx')
            Nx_p = get_valor(df_conmutados, edad + plazo_pago, 'Nx')
            denominador = Nx - Nx_p
            P = PNU / (denominador / get_valor(df_conmutados, edad, 'Dx')) if denominador != 0 else 0
        else:
            PNU = calc_PNU_dotal(df_conmutados, edad, plazo_seguro, i)
            a_pago = calc_anualidad_anticipada_temporal(df_conmutados, edad, plazo_pago, i)
            a_seguro = calc_anualidad_anticipada_temporal(df_conmutados, edad, plazo_seguro, i)
            Nx = get_valor(df_conmutados, edad, 'Nx')
            Nx_p = get_valor(df_conmutados, edad + plazo_pago, 'Nx')
            denominador = Nx - Nx_p
            P = PNU / (denominador / get_valor(df_conmutados, edad, 'Dx')) if denominador != 0 else 0

        B = calc_prima_comercial(P, a_pago, a_seguro, alpha, gamma, beta, k)
        B_total = B * suma_asegurada
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("PNU por $1", f"${PNU:.10f}")
        with col2:
            st.metric("Prima Neta Nivelada", f"${P:.10f}")
        with col3:
            st.metric("Prima Comercial Anual", f"${B_total:,.2f}")
        st.success(f"**Prima Comercial: ${B_total:,.2f}** (5 puntos)")

    # 2. VALOR DE RESCATE
    with tab2:
        st.subheader("💵 Valor de Rescate")
        if t_anos >= plazo_seguro:
            st.error("El año de cálculo no puede ser mayor o igual al plazo del seguro")
            A_actual = 0
            a_restante = 0
            V_rescate = 0
            V_rescate_total = 0
        else:
            edad_actual = edad + t_anos
            if tipo_seguro == "Vitalicio":
                A_actual = calc_PNU_vitalicia(df_conmutados, edad_actual, i)
                a_restante = calc_anualidad_anticipada_temporal(df_conmutados, edad_actual, max(plazo_pago - t_anos, 0), i) if t_anos < plazo_pago else 0
            elif tipo_seguro == "Temporal":
                n_restante = plazo_seguro - t_anos
                A_actual = calc_PNU_temporal(df_conmutados, edad_actual, n_restante, i)
                a_restante = calc_anualidad_anticipada_temporal(df_conmutados, edad_actual, max(plazo_pago - t_anos, 0), i) if t_anos < plazo_pago else 0
            else:
                n_restante = plazo_seguro - t_anos
                A_actual = calc_PNU_dotal(df_conmutados, edad_actual, n_restante, i)
                a_restante = calc_anualidad_anticipada_temporal(df_conmutados, edad_actual, max(plazo_pago - t_anos, 0), i) if t_anos < plazo_pago else 0

            a_pago_original = a_pago if 'a_pago' in locals() else 0
            V_rescate = calc_valor_rescate(A_actual, P, a_restante, k * B, a_pago_original)
            V_rescate_total = V_rescate * suma_asegurada
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Edad Actual", f"{edad_actual} años")
                st.metric("A_{x+t}", f"{A_actual:.10f}")
            with col2:
                st.metric("Años transcurridos", f"{t_anos} años")
                st.metric("Anualidad restante", f"{a_restante:.6f}")
            st.success(f"**Valor de Rescate: ${V_rescate_total:,.2f}** (7.5 puntos)")

    # 3. SEGURO SALDADO
    with tab3:
        st.subheader("🛡️ Seguro Saldado")
        if t_anos >= plazo_seguro:
            st.error("El año de cálculo no puede ser mayor o igual al plazo del seguro")
            A_nueva = 0
            S_saldado = 0
            S_saldado_total = 0
            n_restante = 0
        else:
            edad_actual = edad + t_anos
            n_restante = plazo_seguro - t_anos if tipo_seguro != "Vitalicio" else (100 - edad_actual)
            if tipo_seguro == "Vitalicio":
                A_nueva = calc_PNU_vitalicia(df_conmutados, edad_actual, i)
            elif tipo_seguro == "Temporal":
                A_nueva = calc_PNU_temporal(df_conmutados, edad_actual, n_restante, i)
            else:
                A_nueva = calc_PNU_dotal(df_conmutados, edad_actual, n_restante, i)
            S_saldado = calc_seguro_saldado(V_rescate, A_nueva)
            S_saldado_total = S_saldado * suma_asegurada
            col1, col2 = st.columns(2)
            with col1:
                st.metric("PNU Nueva", f"{A_nueva:.10f}")
                st.metric("Vigencia Restante", f"{n_restante} años")
            with col2:
                st.metric("Valor Rescate Utilizado", f"${V_rescate_total:,.2f}")
                st.metric("Nueva Suma Asegurada", f"${S_saldado_total:,.2f}")
            st.success(f"**Seguro Saldado: ${S_saldado_total:,.2f}** (7.5 puntos)")
            st.info(f"El asegurado queda cubierto por ${S_saldado_total:,.2f} durante los {n_restante} años restantes")

    # 4. SEGURO PRORROGADO
    with tab4:
        st.subheader("⏰ Seguro Prorrogado")
        if t_anos >= plazo_seguro:
            st.error("El año de cálculo no puede ser mayor o igual al plazo del seguro")
            años, meses, dias = 0, 0, 0
            edad_actual = edad + t_anos
        else:
            edad_actual = edad + t_anos
            n_restante = plazo_seguro - t_anos if tipo_seguro != "Vitalicio" else None
            años, meses, dias = calc_seguro_prorrogado(df_conmutados, V_rescate, 1, edad_actual, tipo_seguro, n_restante)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Edad Actual", f"{edad_actual} años")
                st.metric("Suma Asegurada", f"${suma_asegurada:,.2f}")
            with col2:
                st.metric("Valor Rescate", f"${V_rescate_total:,.2f}")
                st.metric("Prórroga", f"{años} años, {meses} meses, {dias} días")
            if tipo_seguro == "Dotal (Mixto)":
                if años >= (n_restante or 0):
                    Dx_actual = get_valor(df_conmutados, edad_actual, 'Dx')
                    Dx_final = get_valor(df_conmutados, edad + plazo_seguro, 'Dx')
                    devolucion = V_rescate_total - (suma_asegurada * (Dx_final / Dx_actual)) if Dx_actual != 0 else 0
                    st.success(f"**Prórroga: Hasta término de vigencia ({n_restante} años)**")
                    if devolucion > 0:
                        st.info(f"**Devolución si llega con vida: ${devolucion:,.2f}** (10 puntos)")
                else:
                    st.success(f"**Prórroga: {años} años, {meses} meses, {dias} días** (10 puntos)")
            else:
                st.success(f"**Prórroga: {años} años, {meses} meses, {dias} días** (10 puntos)")
            st.info(f"📅 **Fecha de término de la prórroga:** {años} años, {meses} meses y {dias} días desde hoy")

    # Guardar resultados en session_state para poder generar PDF fuera del bloque de cálculo
    st.session_state['results_ready'] = True
    st.session_state['pdf_data'] = {
        'tipo_seguro': tipo_seguro,
        'suma_asegurada': suma_asegurada,
        'tasa_interes': tasa_interes,
        'edad': edad,
        'plazo_seguro': plazo_seguro,
        'plazo_pago': plazo_pago,
        'tipo_recargo': tipo_recargo,
        't_anos': t_anos,
        'PNU': locals().get('PNU', 0),
        'P': locals().get('P', 0),
        'B_total': locals().get('B_total', 0),
        'edad_actual': locals().get('edad_actual', 0),
        'A_actual': locals().get('A_actual', 0),
        'V_rescate_total': locals().get('V_rescate_total', 0),
        'S_saldado_total': locals().get('S_saldado_total', 0),
        'n_restante': locals().get('n_restante', 0),
        'años': locals().get('años', 0),
        'meses': locals().get('meses', 0),
        'dias': locals().get('dias', 0),
        'devolucion': locals().get('devolucion', 0)
    }

# --- Generación de PDF fuera del bloque de cálculo ---
st.header("📄 Generar Reporte PDF")
if not st.session_state.get('results_ready', False):
    st.info("Primero haz clic en '🔢 CALCULAR VALORES GARANTIZADOS' para poder generar el PDF.")
else:
    pdf_data = st.session_state.get('pdf_data', {})
    if not PDF_AVAILABLE:
        st.error("❌ Para generar PDF, instala fpdf: pip install fpdf")
        st.code("pip install fpdf", language="bash")
    else:
        if st.button("📥 Generar y Descargar Reporte en PDF", key="generar_pdf"):
            try:
                import tempfile, os
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "REPORTE DE VALORES GARANTIZADOS", 0, 1, "C")
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "C")
                pdf.ln(10)

                # Datos generales
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "DATOS GENERALES", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 6, f"Tipo de Seguro: {pdf_data.get('tipo_seguro')}", 0, 1)
                pdf.cell(0, 6, f"Suma Asegurada: ${pdf_data.get('suma_asegurada'):,.2f}", 0, 1)
                pdf.cell(0, 6, f"Tasa de Interes: {pdf_data.get('tasa_interes')}%", 0, 1)
                pdf.cell(0, 6, f"Edad del Asegurado: {pdf_data.get('edad')} anos", 0, 1)
                pdf.cell(0, 6, f"Plazo del Seguro: {pdf_data.get('plazo_seguro')} anos", 0, 1)
                pdf.cell(0, 6, f"Plazo de Pago: {pdf_data.get('plazo_pago')} anos", 0, 1)
                pdf.cell(0, 6, f"Tipo de Recargos: {pdf_data.get('tipo_recargo')}", 0, 1)
                pdf.cell(0, 6, f"Ano de Calculo: {pdf_data.get('t_anos')}", 0, 1)
                pdf.ln(5)

                # Prima Comercial
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, "PRIMA COMERCIAL (5 puntos)", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 6, f"PNU: ${pdf_data.get('PNU'):.10f}", 0, 1)
                pdf.cell(0, 6, f"Prima Neta Nivelada: ${pdf_data.get('P'):.10f}", 0, 1)
                pdf.cell(0, 6, f"Prima Comercial Anual: ${pdf_data.get('B_total'):,.2f}", 0, 1)
                pdf.ln(5)

                # Valor de Rescate
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"VALOR DE RESCATE AL ANO {pdf_data.get('t_anos')} (7.5 puntos)", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 6, f"Edad Actual: {pdf_data.get('edad_actual')} anos", 0, 1)
                pdf.cell(0, 6, f"Valor de Rescate: ${pdf_data.get('V_rescate_total'):,.2f}", 0, 1)
                pdf.ln(5)

                # Seguro Saldado
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"SEGURO SALDADO AL ANO {pdf_data.get('t_anos')} (7.5 puntos)", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 6, f"Nueva Suma Asegurada: ${pdf_data.get('S_saldado_total'):,.2f}", 0, 1)
                if pdf_data.get('tipo_seguro') != 'Vitalicio':
                    pdf.cell(0, 6, f"Vigencia Restante: {pdf_data.get('n_restante')} anos", 0, 1)
                else:
                    pdf.cell(0, 6, f"Vigencia: Vitalicia", 0, 1)
                pdf.ln(5)

                # Seguro Prorrogado
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"SEGURO PRORROGADO AL ANO {pdf_data.get('t_anos')} (10 puntos)", 0, 1)
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 6, f"Suma Asegurada Mantenida: ${pdf_data.get('suma_asegurada'):,.2f}", 0, 1)
                pdf.cell(0, 6, f"Prorroga: {pdf_data.get('años')} anos, {pdf_data.get('meses')} meses, {pdf_data.get('dias')} dias", 0, 1)

                if pdf_data.get('tipo_seguro') == "Dotal (Mixto)":
                    if pdf_data.get('años', 0) >= pdf_data.get('n_restante', 0):
                        pdf.cell(0, 6, f"Vigencia hasta termino original: {pdf_data.get('n_restante')} anos", 0, 1)
                        if pdf_data.get('devolucion', 0) > 0:
                            pdf.cell(0, 6, f"Devolucion si llega con vida: ${pdf_data.get('devolucion'):,.2f}", 0, 1)

                pdf.ln(10)

                # Resumen de puntuación
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 6, "RESUMEN DE PUNTUACION:", 0, 1)
                pdf.set_font("Arial", "", 9)
                pdf.cell(0, 5, "- Prima Comercial: 5 puntos", 0, 1)
                pdf.cell(0, 5, "- Valor de Rescate: 7.5 puntos", 0, 1)
                pdf.cell(0, 5, "- Seguro Saldado: 7.5 puntos", 0, 1)
                pdf.cell(0, 5, "- Seguro Prorrogado: 10 puntos", 0, 1)
                pdf.ln(3)
                pdf.set_font("Arial", "I", 8)
                pdf.cell(0, 5, "Total por tipo de seguro: 30 puntos", 0, 1, "C")
                pdf.cell(0, 5, "Calificacion maxima (3 tipos): 100 puntos = 30 puntos del parcial", 0, 1, "C")

                # Guardar PDF y entregar descarga
                nombre_archivo = f"valores_garantizados_{pdf_data.get('tipo_seguro','').lower().replace(' ', '_').replace('(', '').replace(')', '')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                ruta_pdf = os.path.join(tempfile.gettempdir(), nombre_archivo)
                pdf.output(ruta_pdf)
                with open(ruta_pdf, 'rb') as f:
                    pdf_bytes = f.read()
                st.download_button(label="📥 Descargar PDF", data=pdf_bytes, file_name=nombre_archivo, mime="application/pdf")
                st.success("✅ PDF generado exitosamente! Haz clic en 'Descargar PDF' arriba.")
            except Exception as e:
                st.error(f"❌ Error al generar PDF: {e}")
                st.info("Intenta instalar fpdf nuevamente: pip install fpdf")

# Footer y demás (sin cambios funcionales)
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p><strong>Sistema de Cálculo de Valores Garantizados</strong></p>
    <p>Matemáticas Actuariales - Tabla de Mortalidad Mexicana 2000-I</p>
    <p>✅ Prima Comercial (5 pts) | ✅ Valor de Rescate (7.5 pts) | ✅ Seguro Saldado (7.5 pts) | ✅ Seguro Prorrogado (10 pts) | ✅ PDF (10 pts)</p>
</div>
""", unsafe_allow_html=True)

with st.expander("📖 Instrucciones de Uso"):
    st.markdown("""
    ### Cómo usar esta calculadora:
    1. **Seleccione el tipo de seguro** en el panel lateral.
    2. **Configure los parámetros** y haga clic en 'CALCULAR'.
    3. Luego usa 'Generar y Descargar Reporte en PDF'.
    """)

if suma_asegurada < 10000:
    st.error("⚠️ La suma asegurada debe ser mínimo $10,000")
if tasa_interes <= 0 or tasa_interes > 10:
    st.error("⚠️ La tasa de interés debe ser mayor a 0% y menor o igual a 10%")

with st.expander("🔢 Información sobre Valores Conmutados"):
    st.markdown("""
    - **D_x** = l_x × (1+i)^(-x)
    - **N_x** = Σ D_y (desde y=x hasta y=100)
    - **C_x** = d_x × (1+i)^(-(x+1))
    - **M_x** = Σ C_y (desde y=x hasta y=100)
    """)
with st.expander("📊 Ver Tabla de Mortalidad (edades 12-50)"):
    df_muestra = pd.DataFrame(data)
    df_muestra = df_muestra[df_muestra['x'] <= 50]
    st.dataframe(df_muestra, use_container_width=True)