CREATE TABLE rxmalos (
    id SERIAL PRIMARY KEY,
    paciente VARCHAR(255),
    fecha DATE,
    fechaconsulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uid VARCHAR(128),
    patientid VARCHAR(64)
);

select * from rxmalos;
