import streamlit as st
from datetime import date
import re
import openpyxl
from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind

# ─────────────────────────────────────────────
# Configuraciones del PACS (personaliza esto)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Interfaz de usuario
# ─────────────────────────────────────────────
st.title("Buscador de Estudios RX en PACS")

with st.form("consulta_form"):
    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Fecha inicio", value=date.today().replace(day=1))
    with col2:
        end_date = st.date_input("Fecha fin", value=date.today())

    modality = st.text_input("Modalidad", value="CR")
    ejecutar = st.form_submit_button("Buscar estudios")

if ejecutar:
    st.info("Conectando con el PACS y ejecutando la búsqueda...")

    ae = AE(ae_title=MY_AET)
    ae.add_requested_context(StudyRootQueryRetrieveInformationModelFind)

    assoc = ae.associate(PACS_IP, PACS_PORT, ae_title=PACS_AET)

    if assoc.is_established:
        ds = Dataset()
        ds.QueryRetrieveLevel = 'STUDY'
        ds.StudyDate = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
        ds.Modality = modality
        ds.StudyInstanceUID = ''
        ds.PatientID = ''
        ds.PatientName = ''

        responses = assoc.send_c_find(ds, StudyRootQueryRetrieveInformationModelFind)

        data = []
        for (status, identifier) in responses:
            if status and identifier:
                uid = getattr(identifier, 'StudyInstanceUID', '')
                patient = getattr(identifier, 'PatientID', 'Desconocido')
                study_date = getattr(identifier, 'StudyDate', '????')
                Patient_Name = str(getattr(identifier, 'PatientName', ''))
                if uid and re.search(r'[A-Za-z]', uid):
                    data.append((uid, patient, Patient_Name, study_date))

        assoc.release()

        if data:
            st.success(f" Se encontraron {len(data)} estudio(s) RX con letras en el UID.")
            st.table(data)

            # Guardar Excel
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Estudios_RX"
            ws.append(["StudyInstanceUID", "PatientID", "PatientName","StudyDate"])
            for row in data:
                ws.append(row)

            excel_path = "resultados_estudios_rx.xlsx"
            wb.save(excel_path)

            with open(excel_path, "rb") as f:
                st.download_button(" Descargar Excel", f, file_name="estudios_rx.xlsx")
        else:
            st.warning("No se encontraron estudios RX con letras en el UID.")
    else:
        st.error("No se pudo establecer conexión con el PACS.")