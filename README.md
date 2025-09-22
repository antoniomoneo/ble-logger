# BLE Logger – Contador de visitantes con Raspberry Pi

Este proyecto implementa un **contador de visitantes basado en Bluetooth Low Energy (BLE)** utilizando una Raspberry Pi.  
Está diseñado para museos, exposiciones o instalaciones en las que resulta útil medir la **afluencia de público y el tiempo de permanencia**, garantizando siempre la **protección de la privacidad**.

---

## 🔍 Finalidad
El sistema escucha las **señales de publicidad BLE** que emiten de forma estándar los teléfonos móviles y otros dispositivos cercanos.  
No se conecta a los dispositivos ni accede a datos personales.  
La información capturada se limita a:
- **Identificador anónimo** (hash de la dirección MAC BLE con una “sal” secreta opcional).  
- **Intensidad de señal (RSSI)** como aproximación de cercanía.  
- **Tiempos de detección** (inicio, fin, duración de la visita).

---

## 📂 Datos generados

El programa crea ficheros CSV en la carpeta `data/`:

### 1. `seen-YYYY-MM-DD.csv`
Detecciones en tiempo real (limitadas a **1 registro cada 5 segundos por dispositivo**).
- `id` → identificador anónimo (hash irreversible).  
- `utc` → fecha y hora en UTC.  
- `rssi` → intensidad de la señal en dBm.  
- `mac` → solo si no se utiliza “sal” (normalmente se excluye por privacidad).  

### 2. `sessions-YYYY-MM-DD.csv`
Resumen de cada **sesión de visita** (una sesión termina tras 120 s sin recibir señal).
- `id` → identificador anónimo.  
- `start_utc` → inicio de la visita.  
- `end_utc` → fin de la visita.  
- `duration_s` → duración en segundos.  
- `mean_rssi` → intensidad media de la señal durante la visita.  
- `mac` → solo si no se utiliza “sal”.  

---

## 🔒 Privacidad y protección de datos

- **No se capturan datos personales identificables** (ni nombres, ni contenidos de los dispositivos).  
- La dirección MAC se convierte en un código anónimo mediante **hash SHA-256 con sal**.  
- El resultado es irreversible, lo que garantiza que los dispositivos no puedan reidentificarse.  
- Los datos se utilizan **únicamente con fines estadísticos**: contar visitantes y medir tiempos de permanencia.

---

## 💾 Optimización de almacenamiento

- Se aplica un **filtro de frecuencia (throttle)**: máximo un registro cada 5 s por dispositivo.  
- Los ficheros diarios `seen.csv` se pueden comprimir automáticamente con `gzip`.  
- Se pueden borrar ficheros antiguos (ej. de más de 30 días), conservando los resúmenes de sesiones que son mucho más ligeros.  
- Con una tarjeta de 128 GB el sistema puede almacenar **años de actividad** sin problemas.

---

## 📱 Recolección de datos

La Raspberry Pi no necesita conexión permanente a Internet.  
Los datos pueden recogerse de forma periódica:  
- Conectando con un portátil o móvil y descargando los ficheros.  
- Ejecutando un script (`push_data.sh`) que empaqueta los datos y los envía a un **repositorio privado de GitHub**.

---

## 📊 Usos previstos

- Contabilizar el número de visitantes por día u hora.  
- Estimar el tiempo medio de permanencia.  
- Comparar la afluencia durante eventos o actividades especiales.  
- Facilitar informes y evaluaciones de proyectos culturales o científicos.

---

## ✅ Resumen

El BLE Logger ofrece **analítica de visitantes anónima y respetuosa con la privacidad**.  
Equilibra **utilidad de datos** (afluencia y tiempos de permanencia) con **protección de la privacidad** (anonimización irreversible, recogida mínima de datos, gestión eficiente de almacenamiento).
