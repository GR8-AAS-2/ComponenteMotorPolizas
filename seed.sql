-- =============================================================================
-- SCRIPT DE CARGA INICIAL (SEED) PARA MOTOR DE PÓLIZAS
-- Compatible con PostgreSQL (Supabase, Neon, AWS RDS, Local)
-- Contiene la definición de tabla y 50 pólizas de prueba completas.
-- =============================================================================

-- 1. Crear tabla si no existe
CREATE TABLE IF NOT EXISTS polizas (
    id SERIAL PRIMARY KEY,
    numero_poliza VARCHAR(50) NOT NULL UNIQUE,
    titular VARCHAR(150) NOT NULL,
    tipo_documento VARCHAR(10) NOT NULL DEFAULT 'CC',
    documento_identidad VARCHAR(30) NOT NULL,
    email_titular VARCHAR(120),
    telefono_titular VARCHAR(25),
    direccion VARCHAR(200),
    ciudad VARCHAR(80),
    ramo VARCHAR(60) NOT NULL,
    tipo_cobertura VARCHAR(100) NOT NULL,
    monto_asegurado NUMERIC(14, 2) NOT NULL,
    prima_mensual NUMERIC(10, 2) NOT NULL,
    deducible NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    fecha_inicio_vigencia DATE NOT NULL,
    fecha_fin_vigencia DATE NOT NULL,
    frecuencia_pago VARCHAR(20) NOT NULL DEFAULT 'MENSUAL',
    metodo_pago VARCHAR(30) NOT NULL DEFAULT 'DEBITO_AUTOMATICO',
    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA',
    agente_codigo VARCHAR(20),
    agente_nombre VARCHAR(120),
    beneficiarios TEXT,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices de búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_polizas_numero ON polizas (numero_poliza);
CREATE INDEX IF NOT EXISTS idx_polizas_documento ON polizas (documento_identidad);
CREATE INDEX IF NOT EXISTS idx_polizas_ramo ON polizas (ramo);
CREATE INDEX IF NOT EXISTS idx_polizas_estado ON polizas (estado);

-- 2. Inserción de 50 Pólizas de Prueba (ON CONFLICT DO NOTHING para idempotencia)
INSERT INTO polizas (
    numero_poliza, titular, tipo_documento, documento_identidad, email_titular, 
    telefono_titular, direccion, ciudad, ramo, tipo_cobertura, 
    monto_asegurado, prima_mensual, deducible, fecha_inicio_vigencia, fecha_fin_vigencia, 
    frecuencia_pago, metodo_pago, estado, agente_codigo, agente_nombre, beneficiarios
) VALUES
('POL-2026-AUT-001', 'Carlos Andres Gomez Diaz', 'CC', '1017123456', 'carlos.gomez@email.com', '+57 3104567890', 'Calle 45 # 23-10', 'Bogotá', 'Autos', 'Todo Riesgo Premium Plus', 65000000.00, 245000.00, 1000000.00, '2026-01-01', '2027-01-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-AUT-002', 'Maria Fernanda Morales', 'CC', '1020345678', 'maria.morales@email.com', '+57 3119876543', 'Cra 7 # 112-40 Apt 502', 'Bogotá', 'Autos', 'Responsabilidad Civil y Pérdida Total', 45000000.00, 180000.00, 1500000.00, '2026-01-15', '2027-01-15', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Titular'),
('POL-2026-VID-003', 'Jorge Eduardo Ramirez Soto', 'CC', '79845123', 'jorge.ramirez@email.com', '+57 3201239876', 'Av. Las Palmas # 15-20', 'Medellín', 'Vida', 'Vida Entera con Ahorro', 250000000.00, 380000.00, 0.00, '2026-02-01', '2036-02-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Esposa (50%), Hijos (50%)'),
('POL-2026-HOG-004', 'Ana Lucia Hernandez Paz', 'CC', '52896321', 'ana.hernandez@email.com', '+57 3156781234', 'Calle 85 # 14-30', 'Bogotá', 'Hogar', 'Hogar Integral y Terremoto', 320000000.00, 195000.00, 2000000.00, '2026-01-10', '2027-01-10', 'ANUAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Titular'),
('POL-2026-SAL-005', 'Roberto Carlos Silva Prada', 'CC', '80123456', 'roberto.silva@email.com', '+57 3004561122', 'Cra 53 # 74-21', 'Barranquilla', 'Salud', 'Salud Global Familiar VIP', 500000000.00, 890000.00, 500000.00, '2026-01-05', '2027-01-05', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Cónyuge e Hijos'),
('POL-2026-EMP-006', 'Construcciones Andinas S.A.S', 'NIT', '900543210-1', 'contacto@construandinas.com', '+57 3123456789', 'Zona Industrial Mz 4 Lote 2', 'Cali', 'Empresarial', 'Todo Riesgo Construcción y Montaje', 1200000000.00, 3200000.00, 15000000.00, '2026-02-15', '2027-02-15', 'TRIMESTRAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Empresa Titular'),
('POL-2026-AUT-007', 'Diego Alejandro Ruiz Cano', 'CC', '1032456789', 'diego.ruiz@email.com', '+57 3187654321', 'Calle 10 Sur # 43-12', 'Medellín', 'Autos', 'Todo Riesgo Utilitarios', 80000000.00, 290000.00, 1200000.00, '2025-11-01', '2026-11-01', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-VID-008', 'Patricia Elena Munoz Cruz', 'CC', '43567890', 'patricia.munoz@email.com', '+57 3169871234', 'Cra 42 # 54-10', 'Bucaramanga', 'Vida', 'Vida Temporal 10 Años', 180000000.00, 140000.00, 0.00, '2026-03-01', '2036-03-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Hijo: Daniel Munoz (100%)'),
('POL-2026-HOG-009', 'Gustavo Adolfo Castro Villa', 'CC', '71234567', 'gustavo.castro@email.com', '+57 3145678901', 'Calle 127 # 19-45', 'Bogotá', 'Hogar', 'Incendio, Terremoto y Hurto', 210000000.00, 135000.00, 1000000.00, '2025-12-15', '2026-12-15', 'SEMESTRAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Titular'),
('POL-2026-SAL-010', 'Valeria Rios Montoya', 'CC', '1152345678', 'valeria.rios@email.com', '+57 3012345678', 'Transversal 39 # 72-10', 'Medellín', 'Salud', 'Salud Individual Preferencial', 300000000.00, 420000.00, 300000.00, '2026-01-20', '2027-01-20', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-VIA-011', 'Felipe Santos Ospina', 'CC', '1018987654', 'felipe.santos@email.com', '+57 3134567890', 'Calle 72 # 10-05', 'Bogotá', 'Viajes', 'Asistencia Internacional Europa y Asia', 60000000.00, 95000.00, 0.00, '2026-03-10', '2026-06-10', 'UNICO', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Titular'),
('POL-2026-AUT-012', 'Luisa Fernanda Arias Torres', 'CC', '1098765432', 'luisa.arias@email.com', '+57 3176543210', 'Av. Santander # 55-20', 'Manizales', 'Autos', 'Todo Riesgo Clásicos', 55000000.00, 210000.00, 1000000.00, '2025-08-01', '2026-08-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Titular'),
('POL-2026-EMP-013', 'Logistica del Caribe Ltda', 'NIT', '890123456-7', 'gerencia@logisticacaribe.com', '+57 3009876543', 'Vía 40 # 85-100', 'Barranquilla', 'Empresarial', 'Transporte de Carga y Flota Pesada', 850000000.00, 2400000.00, 5000000.00, '2026-01-01', '2027-01-01', 'MENSUAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Empresa Titular'),
('POL-2026-VID-014', 'Mauricio Cardenas Restrepo', 'CC', '98765432', 'mauricio.cardenas@email.com', '+57 3218765432', 'Calle 10 # 30-15', 'Pereira', 'Vida', 'Vida Deudores Hipotecario', 160000000.00, 98000.00, 0.00, '2026-01-01', '2046-01-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Banco Acreedor (100%)'),
('POL-2026-HOG-015', 'Sandra Milena Quintero Ortiz', 'CC', '63456789', 'sandra.quintero@email.com', '+57 3198765432', 'Carrera 27 # 36-18', 'Bucaramanga', 'Hogar', 'Hogar Esencial Propietario', 180000000.00, 110000.00, 800000.00, '2025-05-10', '2026-05-10', 'ANUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Titular'),
('POL-2026-AUT-016', 'Andres Felipe Suarez Vega', 'CC', '1015678901', 'andres.suarez@email.com', '+57 3101234567', 'Calle 134 # 9-40', 'Bogotá', 'Autos', 'Todo Riesgo Motocicletas Alta Cilindrada', 38000000.00, 165000.00, 900000.00, '2026-02-01', '2027-02-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-SAL-017', 'Camila Andrea Vargas Lopez', 'CC', '1037654321', 'camila.vargas@email.com', '+57 3154567890', 'Circular 4 # 73-20', 'Medellín', 'Salud', 'Salud Maternidad y Familia', 400000000.00, 650000.00, 400000.00, '2026-01-15', '2027-01-15', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Familia Titular'),
('POL-2026-RC-018', 'Dr. Javier Antonio Mejia Soler', 'CC', '79123456', 'javier.mejia@medicos.com', '+57 3112345678', 'Calle 93 # 16-20 Cons 401', 'Bogotá', 'Responsabilidad Civil', 'RC Profesional Médica y Quirúrgica', 600000000.00, 520000.00, 5000000.00, '2026-01-01', '2027-01-01', 'ANUAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Titular'),
('POL-2026-AUT-019', 'Esteban Jose Perez Carvajal', 'CC', '1143210987', 'esteban.perez@email.com', '+57 3023456789', 'Cra 100 # 11-45', 'Cali', 'Autos', 'Todo Riesgo Eléctricos e Híbridos', 110000000.00, 340000.00, 1800000.00, '2026-02-10', '2027-02-10', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Titular'),
('POL-2026-VID-020', 'Gloria Ines Salazar Betancur', 'CC', '32456789', 'gloria.salazar@email.com', '+57 3149876543', 'Calle 50 # 45-12', 'Medellín', 'Vida', 'Vida Senior Jubilados', 90000000.00, 175000.00, 0.00, '2025-09-01', '2026-09-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Nietos (100%)'),
('POL-2026-HOG-021', 'Sebastian Toro Arango', 'CC', '1026789012', 'sebastian.toro@email.com', '+57 3182345678', 'Km 5 Vía Rionegro', 'Rionegro', 'Hogar', 'Hogar Campestre y Finca Recreo', 550000000.00, 310000.00, 3000000.00, '2026-01-01', '2027-01-01', 'ANUAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-EMP-022', 'Textiles del Valle S.A.', 'NIT', '800234567-8', 'administracion@textilesvalle.com', '+57 3128765432', 'Cra 1 # 40-50', 'Cali', 'Empresarial', 'Incendio Pyme y Pérdida de Beneficios', 2500000000.00, 5800000.00, 25000000.00, '2026-01-01', '2027-01-01', 'TRIMESTRAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Empresa Titular'),
('POL-2026-AUT-023', 'Natalia Gomez Cardona', 'CC', '1014567890', 'natalia.gomez@email.com', '+57 3171239876', 'Calle 140 # 12-18', 'Bogotá', 'Autos', 'Pérdida Total y Hurto', 32000000.00, 125000.00, 1000000.00, '2026-01-20', '2027-01-20', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Titular'),
('POL-2026-SAL-024', 'Alvaro Hernan Osorio Gil', 'CC', '19456789', 'alvaro.osorio@email.com', '+57 3106549870', 'Cra 68 # 45-20', 'Cartagena', 'Salud', 'Salud Tercera Edad Integral', 200000000.00, 560000.00, 600000.00, '2025-10-01', '2026-10-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Titular'),
('POL-2026-VIA-025', 'Monica Marcela Pineda Rojas', 'CC', '53123456', 'monica.pineda@email.com', '+57 3163456789', 'Calle 106 # 54-30', 'Bogotá', 'Viajes', 'Estudiantes en el Exterior Anual', 120000000.00, 180000.00, 0.00, '2026-01-10', '2027-01-10', 'UNICO', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Titular'),
('POL-2026-AUT-026', 'Hector Fabio Ramirez Marin', 'CC', '75678901', 'hector.ramirez@email.com', '+57 3158765432', 'Av. Centenario # 18-04', 'Armenia', 'Autos', 'Todo Riesgo Camionetas Pick-Up', 92000000.00, 310000.00, 1500000.00, '2025-11-15', '2026-11-15', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Titular'),
('POL-2026-VID-027', 'Diana Carolina Beltran Mora', 'CC', '1023456789', 'diana.beltran@email.com', '+57 3139871234', 'Cra 15 # 82-10', 'Bogotá', 'Vida', 'Vida Mujer Protegida Cáncer', 150000000.00, 115000.00, 0.00, '2026-02-01', '2036-02-01', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Madre (100%)'),
('POL-2026-HOG-028', 'Julian David Alvarez Rios', 'CC', '1036543210', 'julian.alvarez@email.com', '+57 3014567890', 'Calle 33 # 76-12', 'Medellín', 'Hogar', 'Arrendatario Seguro Contenidos', 80000000.00, 75000.00, 500000.00, '2026-01-01', '2027-01-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-EMP-029', 'Inversiones Hoteleras del Norte', 'NIT', '901234567-2', 'contabilidad@hotelesnorte.com', '+57 3001234567', 'Cra 54 # 68-150', 'Barranquilla', 'Empresarial', 'Multirriesgo Hotelero y RC Huéspedes', 3800000000.00, 7200000.00, 30000000.00, '2026-01-01', '2027-01-01', 'SEMESTRAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Empresa Titular'),
('POL-2026-AUT-030', 'Angela Maria Ospina Gomez', 'CC', '1019876543', 'angela.ospina@email.com', '+57 3192345678', 'Calle 53 # 21-40', 'Bogotá', 'Autos', 'Todo Riesgo Familiar Económico', 36000000.00, 140000.00, 1200000.00, '2026-03-01', '2027-03-01', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Titular'),
('POL-2026-SAL-031', 'Federico Restrepo Zuluaga', 'CC', '71890123', 'federico.restrepo@email.com', '+57 3209876543', 'Cra 43A # 1Sur-50', 'Medellín', 'Salud', 'Salud Internacional Plus Deducible Alto', 800000000.00, 780000.00, 2000000.00, '2026-01-01', '2027-01-01', 'ANUAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular y Cónyuge'),
('POL-2026-RC-032', 'Ingenieros Civiles Asociados S.A.', 'NIT', '860987654-3', 'proyectos@ingenierosciviles.com', '+57 3118765432', 'Av. El Dorado # 69-70', 'Bogotá', 'Responsabilidad Civil', 'RC Extracontractual Obras Civiles', 1500000000.00, 2100000.00, 10000000.00, '2026-02-15', '2027-02-15', 'SEMESTRAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Terceros Afectados'),
('POL-2026-VID-033', 'Liliana Marcela Castano Mejia', 'CC', '43123456', 'liliana.castano@email.com', '+57 3141234567', 'Calle 48 # 70-15', 'Medellín', 'Vida', 'Vida Grupo Empresas', 80000000.00, 55000.00, 0.00, '2026-01-01', '2027-01-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Beneficiarios de Ley'),
('POL-2026-AUT-034', 'Oscar Ivan Martinez Rincon', 'CC', '1017890123', 'oscar.martinez@email.com', '+57 3186543210', 'Calle 63 # 28-10', 'Bogotá', 'Autos', 'Todo Riesgo Taxi Urbano', 50000000.00, 280000.00, 2000000.00, '2025-10-10', '2026-10-10', 'MENSUAL', 'EFECTIVO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Titular'),
('POL-2026-HOG-035', 'Claudia Patricia Guzman Ortiz', 'CC', '52789012', 'claudia.guzman@email.com', '+57 3151239876', 'Cra 58 # 137-20', 'Bogotá', 'Hogar', 'Hogar Seguro Edificio y Copropiedades', 420000000.00, 230000.00, 2000000.00, '2026-01-01', '2027-01-01', 'ANUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Titular'),
('POL-2026-AUT-036', 'Ricardo Jose Navarro Blanco', 'CC', '88123456', 'ricardo.navarro@email.com', '+57 3008765432', 'Calle 76 # 51B-30', 'Barranquilla', 'Autos', 'Todo Riesgo SUV Blindado', 190000000.00, 590000.00, 3000000.00, '2026-02-01', '2027-02-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Titular'),
('POL-2026-SAL-037', 'Manuela Echeverri Londono', 'CC', '1152987654', 'manuela.echeverri@email.com', '+57 3018765432', 'Calle 10B # 36-40', 'Medellín', 'Salud', 'Salud Odontológica y Visión VIP', 50000000.00, 110000.00, 50000.00, '2026-01-10', '2027-01-10', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-VID-038', 'Guillermo Leon Valencia Hoyos', 'CC', '70456789', 'guillermo.valencia@email.com', '+57 3216549870', 'Cra 23 # 62-10', 'Manizales', 'Vida', 'Vida Individual Renta Educativa Hijos', 200000000.00, 310000.00, 0.00, '2026-01-01', '2036-01-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-03', 'Santiago Silva', 'Hijo: Mateo Valencia (100%)'),
('POL-2026-EMP-039', 'Agropecuaria Los Llanos S.A.S', 'NIT', '830567890-4', 'finanzas@agrollanos.com', '+57 3121234567', 'Km 12 Vía Puerto López', 'Villavicencio', 'Empresarial', 'Seguro Agropecuario Maquinaria y Cosechas', 980000000.00, 1950000.00, 8000000.00, '2026-03-01', '2027-03-01', 'SEMESTRAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Empresa Titular'),
('POL-2026-AUT-040', 'Tatiana Marcela Nino Parra', 'CC', '1030987654', 'tatiana.nino@email.com', '+57 3178901234', 'Calle 161 # 18-30', 'Bogotá', 'Autos', 'Todo Riesgo Conductor Joven', 42000000.00, 195000.00, 1500000.00, '2025-12-01', '2026-12-01', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Titular'),
('POL-2026-HOG-041', 'Fernando Alfonso Diaz Granados', 'CC', '12456789', 'fernando.diaz@email.com', '+57 3028765432', 'Calle 18 # 4-20', 'Santa Marta', 'Hogar', 'Hogar Frente al Mar y Vientos Fuertes', 480000000.00, 275000.00, 3500000.00, '2026-01-15', '2027-01-15', 'ANUAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Titular'),
('POL-2026-VIA-042', 'Camilo Ernesto Herrera Barreto', 'CC', '1014123987', 'camilo.herrera@email.com', '+57 3109871234', 'Calle 80 # 11-40', 'Bogotá', 'Viajes', 'Asistencia Viajero Frecuente Multiviaje', 90000000.00, 130000.00, 0.00, '2026-01-01', '2027-01-01', 'ANUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Titular'),
('POL-2026-VID-043', 'Adriana Maria Cuervo Londono', 'CC', '32789012', 'adriana.cuervo@email.com', '+57 3161234567', 'Calle 3Sur # 43A-10', 'Medellín', 'Vida', 'Vida Incapacidad Total y Permanente', 220000000.00, 240000.00, 0.00, '2026-02-01', '2036-02-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Hija: Sofia Cuervo (100%)'),
('POL-2026-AUT-044', 'Juan Pablo Montoya Ceballos', 'CC', '1028765432', 'juan.montoya@email.com', '+57 3154561234', 'Cra 35 # 7-50', 'Medellín', 'Autos', 'Todo Riesgo Deportivo Alta Gama', 280000000.00, 750000.00, 4000000.00, '2026-01-01', '2027-01-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-RC-045', 'Clinica Odontologica Sonrisas', 'NIT', '900876543-9', 'administracion@clinicosonrisas.com', '+57 3189876543', 'Cra 15 # 98-40', 'Bogotá', 'Responsabilidad Civil', 'RC Institucional Odontología y Estética', 800000000.00, 950000.00, 5000000.00, '2026-01-01', '2027-01-01', 'SEMESTRAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Pacientes Titulares'),
('POL-2026-SAL-046', 'Santiago Restrepo Villegas', 'CC', '1035678901', 'santiago.restrepo@email.com', '+57 3016543210', 'Circular 73B # 39B-12', 'Medellín', 'Salud', 'Salud Jóvenes Profesionales', 180000000.00, 210000.00, 150000.00, '2026-02-01', '2027-02-01', 'MENSUAL', 'TARJETA_CREDITO', 'ACTIVA', 'AGT-01', 'Laura Martinez', 'Titular'),
('POL-2026-AUT-047', 'Monica Lucia Caicedo Mina', 'CC', '66987654', 'monica.caicedo@email.com', '+57 3131234567', 'Av. 6N # 24N-10', 'Cali', 'Autos', 'Todo Riesgo Utilitario Delivery', 48000000.00, 220000.00, 1100000.00, '2025-11-01', '2026-11-01', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Titular'),
('POL-2026-HOG-048', 'Rodrigo Antonio Bernal Perez', 'CC', '79654321', 'rodrigo.bernal@email.com', '+57 3114567890', 'Calle 116 # 15-30 Apt 804', 'Bogotá', 'Hogar', 'Hogar Premium Penthouse', 750000000.00, 420000.00, 3000000.00, '2026-01-01', '2027-01-01', 'ANUAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-02', 'Pedro Rodriguez', 'Titular'),
('POL-2026-VID-049', 'Karen Giselle Tapia Ruiz', 'CC', '1047890123', 'karen.tapia@email.com', '+57 3004569870', 'Cra 51B # 84-120', 'Barranquilla', 'Vida', 'Vida Protección Familiar Ahorro Plus', 300000000.00, 410000.00, 0.00, '2026-01-10', '2036-01-10', 'MENSUAL', 'DEBITO_AUTOMATICO', 'ACTIVA', 'AGT-05', 'Daniela Vega', 'Padres (50%), Hermanos (50%)'),
('POL-2026-EMP-050', 'Distribuidora Farmaceutica Nacional', 'NIT', '860123987-5', 'gerencia@distrifarma.com', '+57 3148765432', 'Calle 17 # 68D-40', 'Bogotá', 'Empresarial', 'Multirriesgo Almacenes e Inventarios', 4500000000.00, 8900000.00, 40000000.00, '2026-01-01', '2027-01-01', 'TRIMESTRAL', 'TRANSFERENCIA', 'ACTIVA', 'AGT-04', 'Marcela Duque', 'Empresa Titular')
ON CONFLICT (numero_poliza) DO UPDATE SET
    titular = EXCLUDED.titular,
    tipo_documento = EXCLUDED.tipo_documento,
    documento_identidad = EXCLUDED.documento_identidad,
    email_titular = EXCLUDED.email_titular,
    telefono_titular = EXCLUDED.telefono_titular,
    direccion = EXCLUDED.direccion,
    ciudad = EXCLUDED.ciudad,
    ramo = EXCLUDED.ramo,
    tipo_cobertura = EXCLUDED.tipo_cobertura,
    monto_asegurado = EXCLUDED.monto_asegurado,
    prima_mensual = EXCLUDED.prima_mensual,
    deducible = EXCLUDED.deducible,
    fecha_inicio_vigencia = EXCLUDED.fecha_inicio_vigencia,
    fecha_fin_vigencia = EXCLUDED.fecha_fin_vigencia,
    frecuencia_pago = EXCLUDED.frecuencia_pago,
    metodo_pago = EXCLUDED.metodo_pago,
    estado = EXCLUDED.estado,
    agente_codigo = EXCLUDED.agente_codigo,
    agente_nombre = EXCLUDED.agente_nombre,
    beneficiarios = EXCLUDED.beneficiarios,
    fecha_actualizacion = CURRENT_TIMESTAMP;
