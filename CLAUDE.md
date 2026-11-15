# CLAUDE.md: Obligatorio de Herramientas de Software para Big Data (ORT, 2026)

Este archivo le da contexto a Claude para trabajar en el obligatorio del grupo. Lo mantienen los dos integrantes (Juan Manuel y Federico). Si algo de acá deja de ser cierto, se actualiza en el repo para que los dos Claude trabajen con la misma información.

## 1. Qué es el proyecto

Obligatorio grupal de la materia Herramientas de Software para Big Data, Licenciatura en Sistemas, Universidad ORT Uruguay, segundo semestre de 2026.

- **Entrega:** 07/12/2026, hasta las 21:00, por Gestión. Un único archivo zip o rar, de 40 MB como máximo, con el informe en PDF, los notebooks, los dashboards de Superset y la evidencia.
- **Defensa:** presencial y eliminatoria. Los dos integrantes tienen que poder explicar y justificar cada decisión.
- **Documentos de referencia:** el enunciado del obligatorio y la guía de AWS Academy, ambos de la cátedra. El enunciado define qué hay que hacer; la guía define cómo se prepara el entorno.

### Dataset y preguntas (aprobados por el docente)

Datasets de Steam de la UCSD (laboratorio de Julian McAuley), descargados de su sitio web. No es Kaggle.

| Archivo | Registros |
|---|---|
| steam_games | 32.135 juegos (catálogo) |
| australian_users_items | 88.310 usuarios, 5.153.209 pares usuario-juego |
| australian_user_reviews | 25.799 usuarios, 59.305 reseñas |
| bundle_data | 615 bundles, 3.525 juegos incluidos |

Preguntas analíticas:
1. ¿Qué géneros acumulan más horas jugadas, en total y por jugador? → Jupyter (pandas)
2. ¿Los juegos gratuitos se juegan más que los pagos? (también por rangos de precio) → Jupyter (pandas)
3. ¿Qué géneros tienen el mayor porcentaje de reseñas positivas? → Jupyter (pandas)
4. ¿Qué porcentaje de los juegos que poseen los usuarios nunca fue jugado, y en qué géneros pasa más? → resultados en `/anl`, tabla Hive y Superset
5. ¿Cuáles son los 10 desarrolladores con más horas jugadas y más jugadores? → resultados en `/anl`, tabla Hive y Superset

## 2. Dónde está cada cosa

- **Repositorio:** https://github.com/50NY/obligatorio-bigdata-steam (público, rama `main`)
  - `data/`: los 4 `.json.gz` ya convertidos a JSON válido. NiFi los descarga desde acá.
  - `scripts/convertir_a_json.py`: convierte los archivos originales (diccionarios de Python, no JSON) a JSON Lines y verifica registro por registro.
  - `notebooks/`: copia de los notebooks de Jupyter. La versión "viva" está en la VM; esta es la copia de respaldo.
- **Informe:** Google Doc "Obligatorio – Herramientas de Software para Big Data", en la carpeta compartida de Drive "Obligatorio".
- **Capturas:** carpeta "Capturas" dentro de "Obligatorio" en Drive. Se nombran con número y descripción: `NN_herramienta_que_muestra.png` (por ejemplo `12_hdfs_lnd_steam.png`). Hoy van hasta la 27.
- **Entorno:** máquina virtual en AWS Academy, en la cuenta de Federico (ver sección 3).

## 3. Entorno técnico

- **VM:** EC2 `ttbd-vm`, Red Hat Enterprise Linux 9, tipo **t3.large** (la guía dice t3a.large; la diferencia se menciona en el informe), disco de 30 GiB, región us-east-1, IP elástica 52.54.210.154.
- **Acceso web:** el archivo hosts de cada computadora apunta estos dominios a la IP elástica: `hdfs`, `yarn`, `hue`, `nifi`, `superset` y `jupyter` (todos `.bigdata.ort.edu.uy`). NiFi se abre en `http://nifi.bigdata.ort.edu.uy/nifi/` (la ruta `/nifi/` es obligatoria). Las credenciales de cada servicio están en la guía de la cátedra; **no se escriben en este archivo ni en el repo, porque el repo es público.**
- **Acceso por SSH:** desde AWS CloudShell, con `ssh -i ~/labsuser.pem ec2-user@52.54.210.154`. La clave `.pem` nunca se sube al repo ni se comparte.
- **Contenedores:** el paquete `lakehouse-course` levanta 13 contenedores Docker: nginx, NiFi, namenode, datanode, resourcemanager, nodemanager, Spark (con JupyterLab), hive-metastore, hive-metastore-db, hive-server, Hue, hue-db y Superset. No se instalan herramientas por separado: se usa lo que trae el entorno.
- **Spark:** 3.5.0. La sesión se crea como en los prácticos: `SparkSession.builder.appName("...").getOrCreate()`. El sistema de archivos por defecto es `hdfs://namenode:8020`, así que alcanza con rutas como `/lnd/steam`.

### Uso del lab de AWS Academy

- Al empezar: **Start Lab** y esperar el punto verde. Si la instancia aparece detenida, se inicia desde EC2 (Estado de la instancia → Iniciar).
- Al terminar: **End Lab**. Apagar no borra nada.
- **Nunca tocar Reset**: borra todo el entorno.
- El crédito es limitado (US$ 50 por cuenta; al 14/11 se habían usado US$ 18). No dejar el lab prendido sin uso.

### Problemas conocidos y cómo se resolvieron

- **Disco lleno (14/11):** NiFi daba `No space left on device` y HDFS entraba en modo seguro (`SafeModeException`). La causa: 2,8 GB de logs de Hive acumulados en `/tmp/root` del contenedor `lakehouse-hive-metastore`. Se borraron los logs viejos, se vació el actual y se desactivó el modo seguro con `docker exec namenode hdfs dfsadmin -safemode leave`.
- **Causa de fondo:** el contenedor `lakehouse-hive-metastore-db` tenía la política de reinicio `no`, mientras que los otros 12 tienen `always`. No arrancaba al prender la VM, y el metastore quedaba reintentando y llenando el log de errores. Se corrigió con `docker update --restart always lakehouse-hive-metastore-db`. **Pendiente:** confirmar en la próxima sesión que Hive arranca solo.
- Si Hive no responde: verificar con `docker ps -a --filter name=lakehouse-hive` que los tres contenedores estén en `Up`. Si la base está detenida: `docker start lakehouse-hive-metastore-db` y después `docker restart lakehouse-hive-metastore lakehouse-hive-server`.
- Para revisar el espacio: `df -h /`. Después de la limpieza quedaron unos 2,8 GB libres. Si no alcanza para Spark, la alternativa es ampliar el volumen EBS, pero hay que acordarlo antes.

## 4. Reglas del obligatorio que hay que respetar

- **Prohibido subir datos a HDFS por comando.** Toda la ingesta pasa por NiFi.
- Las zonas de HDFS tienen que ser **exactamente las de clase**, con criterios escritos.
- La ingesta en NiFi usa buenas prácticas: **Process Groups y Funnels**.
- La exploración y la limpieza se hacen **solo con Spark**, en notebooks de Jupyter.
- Las 5 preguntas se responden **desde tablas Hive**, con Spark SQL o PySpark, nunca leyendo los archivos originales.
- El informe tiene que explicar: el dominio de los datos, **qué significa cada columna de cada tabla y qué tipo de dato debe tener** (diccionario de datos), las preguntas y sus respuestas, la arquitectura del Data Lake, las tecnologías usadas y cómo contribuye cada una al análisis.
- **Parte 2:** arquitectura alternativa con otras tecnologías (Spark es la única que se puede repetir). Lleva diagrama obligatorio. Si se usan servicios de una nube, no se mezclan con los de otra.
- Nota: el enunciado habla de una VM de Azure, pero la cátedra dio AWS Academy. En el informe se aclara que se usó el entorno de AWS Academy de la guía.

## 5. Organización del Data Lake

| Zona | Ruta | Contenido | Escribe |
|---|---|---|---|
| Landing | `/lnd/steam` | Los 4 `.json.gz` tal como llegan | NiFi |
| Refinada | `/rfn/steam/refinado` | Datos limpios en Parquet | Spark |
| Refinada (modelo) | `/rfn/steam/modelo` | Tablas del modelo estrella; las tablas Hive apuntan acá | Spark |
| Analítica | `/anl/steam/pregunta_4`, `/anl/steam/pregunta_5` | Resultados para Superset | Spark |

- Los nombres de zona (`/lnd`, `/rfn`, `/anl`) se confirmaron con el material de la cátedra. **No se usa `/ref`**: fue un error de nombre en el práctico 4. Tampoco se usa `/data`, que es del primer práctico de NiFi.
- No hay zona propia para el modelo: va dentro de `/rfn`, siguiendo el ejemplo del práctico de Hive.
- En cada notebook, las rutas se definen una sola vez al inicio:
  ```python
  LANDING   = "/lnd/steam"
  REFINADO  = "/rfn/steam/refinado"
  MODELO    = "/rfn/steam/modelo"
  ANALITICA = "/anl/steam"
  ```

## 6. Estado del trabajo (al 14/11/2026)

### Hecho
- Conversión de los 4 archivos a JSON válido, verificada registro por registro (sección 4 del informe).
- **Ingesta con NiFi:** Process Group `obligatorio_steam_ingesta` con 4 InvokeHTTP ("Descargar …", Run Schedule de 1 día, ejecutados con Run Once), un Funnel, un UpdateAttribute "Renombrar archivo" (`filename = ${invokehttp.request.url:substringAfterLast('/')}`) y un PutHDFS "Guardar en landing" (Directory `/lnd/steam`, Conflict Resolution `replace`, Hadoop Configuration Resources `/opt/nifi/hadoop-conf/core-site.xml,/opt/nifi/hadoop-conf/hdfs-site.xml`). Los 4 archivos están en `/lnd/steam` y coinciden byte por byte con GitHub. **Los flujos de los prácticos que comparten el lienzo de NiFi no se tocan.**
- **Exploración con Spark** del catálogo, las bibliotecas y las reseñas, en el notebook `steam_exploracion_limpieza.ipynb`.
- Informe: secciones 1 a 4, 6, 7, 8 (exploración) y 12 escritas.

### Decisiones de limpieza ya tomadas (se aplican en el refinamiento)
- **Catálogo (`steam_games`):**
  - Se descartan las 2 filas con `id` nulo. Una está vacía; la otra es Batman: Arkham City GOTY, cuyo id 200260 (sacado de la URL) ya existe en otra fila.
  - El `id` 612880 (Wolfenstein II) es un duplicado exacto: queda una sola fila. Resultado: 32.132 juegos.
  - `discount_price` (99,3 % nulos) y `metascore` (91,7 %) no se usan.
  - El nombre del juego se toma de `app_name`, que está completo, y no de `title`.
  - Los juegos con `developer` (10,3 % nulos) o `genres` (10,2 % nulos) vacíos quedan fuera de los análisis por desarrollador o por género.
- **Regla del precio:**
  - Si es un número, se mantiene.
  - Si el texto contiene "free" (sin distinguir mayúsculas), el precio es 0 y el juego se marca como gratuito.
  - Si dice "Starting at $X", se toma X.
  - El resto ("Third-party", "Play Now", "Install Now", etc.) queda como desconocido.
  - "Free to Play" también aparece como género dentro de `genres`; hay que tenerlo en cuenta en las preguntas por género.
- **Bibliotecas (`users_items`):**
  - Son 88.310 filas pero 87.626 `user_id` distintos. Las 657 copias exactas se eliminan.
  - En los 27 casos con datos distintos (solo cambian los minutos jugados), se conserva la fila con más minutos totales y, si empatan, la de más minutos en las últimas dos semanas.
  - Los 16.806 usuarios con la biblioteca vacía se mantienen en la tabla de usuarios, pero no generan filas usuario-juego.
  - `items_count` es consistente con la lista en todos los casos.
- **Reseñas (`reviews`):**
  - Las 874 reseñas repetidas son copias exactas y se eliminan. Quedan 58.431.
  - Las 10.119 fechas sin año (Steam no muestra el año en las reseñas del año en curso) quedan como desconocidas: no se inventa un año.
  - `recommend` no tiene nulos.
  - 5.317 reseñas son de juegos que no están en el catálogo: se conservan, pero no se pueden clasificar por género.

### Pendiente (en este orden)
1. Comprobar que Hive arranca solo después del cambio de política de reinicio.
2. Explorar `bundle_data`: precios como texto con `$` y `%`.
3. Refinamiento: aplicar las reglas, desarmar las listas con `explode` y guardar en Parquet en `/rfn/steam/refinado`.
4. Diccionario de datos: qué significa cada columna y qué tipo de dato debe tener. Lo pide la letra.
5. Modelado: estrella, con `fact_user_game`, `fact_review` y las dimensiones `dim_game`, `dim_user`, `dim_date` y `dim_genre` (puente juego-género). Hay que justificar la elección y hacer el diagrama.
6. Tablas Hive sobre `/rfn/steam/modelo`.
7. Preguntas 1 a 3 con gráficos en Jupyter. Para la cantidad de visualizaciones, la letra es ambigua: hacer dos por pregunta para ir a lo seguro.
8. Preguntas 4 y 5: guardar en `/anl/steam`, crear tablas Hive y armar los dashboards en Superset.
9. Sección 5, Arquitectura implementada: la infraestructura, los 13 contenedores, el flujo de los datos y cómo contribuye cada herramienta. El diagrama es recomendable.
10. Parte 2, informe final (portada, declaración de autoría, índice, sección de IA) y la exportación.

## 7. Cómo se trabaja con los notebooks

- Se nombran con el prefijo `steam_`: `steam_exploracion_limpieza.ipynb`, después `steam_modelo.ipynb` y `steam_preguntas.ipynb`.
- Cada sección lleva un título en Markdown (`##`) con una línea que explica qué se hace, y termina con una celda de Markdown **"Hallazgos y decisiones"**. El notebook se entrega y el docente lo lee.
- El texto va en celdas de tipo **Markdown**, nunca adentro de celdas de código.
- Al terminar cada sesión: guardar con Ctrl + S, **File → Download**, reemplazar la copia en `notebooks/` y hacer commit y push.

## 8. Formato del informe (estilo Documento 302 de ORT)

- A4, márgenes de 2,5 cm (70,87 pt), Arial 12, justificado, interlineado 1,5, 12 pt de espacio después de cada párrafo.
- Capítulos en Título 1 (16 pt), cada uno empezando en página nueva. Subtítulos en Título 2 (13 pt), numerados a mano ("7.1.", "7.2.").
- **Tablas:** encabezado gris en negrita, bordes de 0,75 pt, texto de 10 pt y ancho completo de la página. Leyenda debajo, centrada, de 10 pt: "**Tabla N.** Descripción".
- **Imágenes:** centradas, con leyenda debajo: "**Ilustración N.** Descripción". La numeración sigue el orden del documento: si se agrega una en el medio, se renumeran las siguientes y sus referencias en el texto. Hoy las ilustraciones van hasta la 18 y las tablas hasta la 7.
- **Código:** Courier New 9,5 con fondo gris claro.
- Lo que falta escribir se marca como `[PENDIENTE]` en cursiva. **Nunca se inventan resultados ni números**: todo sale de lo que efectivamente se ejecutó.
- Los números de página se agregan a mano en Google Docs: abajo a la derecha, sin la primera página.
- Al final hay que pasarlo a Word con la plantilla de ORT, para cargar las propiedades del PDF (tema y palabras clave), que Google Docs no permite.
- Faltan la portada (docente y grupo), la declaración de autoría y el índice.

### Estilo de redacción
- Español rioplatense, académico pero natural, en primera persona del plural ("decidimos", "comprobamos").
- Explicar lo que efectivamente se hizo y por qué, sin frases genéricas que podrían ir en cualquier proyecto.
- Los problemas que aparecieron se documentan en la sección 12 (Problemas encontrados y aprendizajes): síntoma, diagnóstico, solución y verificación.

### Capturas
- Sacarlas cuando el resultado es definitivo, sin pestañas, marcadores ni datos personales visibles.
- Los números (conteos, nulos) van mejor como tablas en el informe que como capturas. Las capturas se reservan para lo que se entiende mejor viéndolo.
- Para insertar una imagen de Drive en el Doc desde una herramienta automática, hay que hacerla pública un momento. Después se vuelve a dejar privada **de a una**, porque el cambio en grupo no se guarda en Drive.

## 9. Uso de IA (condiciones de la cátedra)

- El uso de IA está autorizado, pero hay que **declararlo en el informe**: qué herramienta se usó y en qué partes.
- Todo lo que genere la IA se revisa y se verifica. Los resultados salen de ejecuciones reales.
- La IA no reemplaza el aprendizaje: la defensa es presencial y eliminatoria, y puede haber defensa individual si hay dudas sobre la autoría. Por eso, en cada paso Claude explica qué hace cada cosa y por qué, en lenguaje simple, y el integrante navega las herramientas por sí mismo.

## 10. Cómo trabajar con Claude en este proyecto

- Guiar paso a paso, de a una etapa, con explicación de qué hace cada paso, qué resultado se espera y cómo verificarlo. No avanzar sin comprobar que el paso anterior funcionó.
- Indicar siempre **dónde** se ejecuta cada comando: la computadora, CloudShell, la VM o JupyterLab.
- Antes de cambiar algo en el entorno, diagnosticar con comandos que solo leen. No borrar nada sin identificarlo con certeza y sin explicarlo.
- No inventar puertos, rutas, nombres de contenedores ni configuraciones: copiarlos de lo que ya funciona (los prácticos, la guía) o verificarlos.
- Explicaciones en español simple, sin esquemas innecesarios. Cuando se pide un mensaje o un texto, darlo completo y de una vez.
- Mantener la coherencia con las decisiones de este archivo. Si hay que cambiar una, se acuerda entre los dos integrantes y se actualiza acá.
- Antes de trabajar, `git pull`; al terminar, commit y push, para no pisarse los cambios.
