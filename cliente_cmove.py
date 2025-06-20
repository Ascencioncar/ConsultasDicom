import streamlit as st
from datetime import date
import re
from datetime import datetime
from pydicom.dataset import Dataset
from pynetdicom import AE
from pynetdicom.sop_class import StudyRootQueryRetrieveInformationModelFind
import psycopg2
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

try:
    # Conectar a PostgreSQL
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )
    cursor = conn.cursor()

    # Insertar cada fila
    for uid, patient_id, patient_name, study_date in data:
        try:
            cursor.execute("""
                INSERT INTO estudios_rx (paciente, fecha, uid, patientid)
                VALUES (%s, %s, %s, %s)
            """, (
                patient_name,
                datetime.strptime(study_date, "%Y%m%d").date() if study_date.isdigit() else None,
                uid,
                patient_id
            ))
        except Exception as e:
            st.warning(f"⚠️ Error al insertar UID {uid}: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    st.success("✅ Datos guardados en la base de datos PostgreSQL correctamente.")

except Exception as e:
    st.error(f"❌ Error al conectar a la base de datos: {e}")
