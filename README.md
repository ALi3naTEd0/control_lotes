# Control de Lotes — Los Cielos Farm

**Descripción breve**

Aplicación GUI (Tkinter) para el registro y gestión de lotes de cultivo por sucursal. Permite crear y editar lotes, asignar variedades y cantidades, generar resúmenes y gráficos, exportar informes (PDF/Excel/CSV) y sincronizar el archivo principal (`lotes_template.csv`) con un repositorio de GitHub (vía API).

---

## ✅ Características principales

- Interfaz gráfica con pestañas: `Crear lote`, `Agregar variedades`, `Editar lote` y vistas para listados y gráficos. 🔧
- Guardado local en `lotes_template.csv` y sincronización con un repositorio de GitHub (API REST). 🌐
- Backups automáticos en `registros/` antes de sobrescribir datos críticos. 🗂️
- Editor y filtros para ver y modificar lotes; exportación a PDF (reportlab) y Excel (openpyxl). ✏️📄
- Generación de resúmenes y gráficos (radar por sucursal/etapa, pastel por etapa, barras por ubicación) con `matplotlib`. 📊
- Validaciones integradas: máximo 20 variedades por lote, semana válida 1..22, ramas/etapas/ubicaciones controladas por listas predefinidas. ✅
- Soporte para empaquetado con PyInstaller (detección `sys.frozen`). 🚀

---

## 📦 Requisitos (dependencias)

Recomendado: Python 3.9+ (probado con 3.10/3.11)

Paquetes (ver `requirements.txt`):

- `tkinter` (incluido en la mayoría de instalaciones de Python con GUI)
- `requests` (sincronización GitHub)
- `matplotlib`, `numpy` (gráficos)
- `reportlab` (exportar PDF, opcional)
- `openpyxl` (exportar Excel, opcional)
- `pyinstaller` (empaquetado, opcional)
- `pillow`

Instalación rápida:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuración (GitHub)

El proyecto utiliza un archivo `github_config.txt` en la misma carpeta que `lotes_gui.py` con dos líneas:

1. `usuario/repo` (ejemplo: `ALi3naTEd0/entradas_salidas`)
2. `GITHUB_TOKEN` (token personal con permiso `repo` para leer/escribir archivos via API)

Si `github_config.txt` no existe, la aplicación lo crea con un ejemplo y pedirá que lo edites.

> Nota de seguridad: el token se guarda en texto plano en `github_config.txt`. Para entornos de producción, considere usar un gestor de secretos o variables de entorno.

---

## 🗂️ Formato de `lotes_template.csv`

El archivo CSV esperado contiene las siguientes columnas (orden y nombres):

```
ID,Branch,LoteNum,Stage,Location,Semana,DateCreated,Notes,Variedad_1,Cantidad_1,...,Variedad_20,Cantidad_20
```

- `ID`: identificador calculado (ej. `L1-FSM`)
- `Branch`: sucursal (valores limitados por `BRANCH` en el código)
- `LoteNum`: número entero de lote
- `Stage`: etapa (ej. `FLORACIÓN`)
- `Location`: ubicación física
- `Semana`: semana (1..22)
- `DateCreated`: fecha `YYYY-MM-DD`
- `Notes`: notas libres
- `Variedad_i` / `Cantidad_i`: pares para hasta 20 variedades por lote

La aplicación realiza migraciones/normalizaciones automáticas si detecta estructuras antiguas del CSV.

---

## 🔁 Sincronización con GitHub

- `descargar_csv_github()`: descarga `lotes_template.csv` desde el repo (API) y lo escribe localmente.
- `subir_csv_github()`: sube el archivo local al repo (usa `sha` cuando esté disponible para evitar sobrescrituras accidentales).
- La aplicación crea un backup local antes de restaurar o sobrescribir archivos importantes.

> Nota: No hay un "merge" avanzado automático; la app intenta restaurar desde GitHub en el arranque y al subir reemplaza el archivo en el repo (con manejo de `sha`). Si necesitas un comportamiento de merge que preserve remotos y agregue solo entradas locales únicas, puedo implementarlo.

---

## 🖥️ Uso

1. Edita `github_config.txt` con tu `usuario/repo` y `TOKEN` (si deseas sincronizar con GitHub).
2. Ejecuta la app:

```bash
python lotes_gui.py
```

3. Pestañas principales:
- `Crear lote`: formulario para crear nuevos lotes.
- `Agregar variedades`: seleccionar lote y añadir/eliminar variedades con cantidades.
- `Editar lote`: cambiar etapa, ubicación o semana de un lote existente.
- `Listados`/`Filtrar`: ver listados completos o filtrados, y exportar a PDF/XLSX/CSV.

Funciones importantes:
- `Listar todos` / `Filtrar`: muestran reportes que pueden exportarse.
- `↻ Reconectar` / `↑ Sincronizar`: botones en la barra de estado para forzar descarga o subir al repo.
- Backups automáticos en `registros/` y restauración del último backup si GitHub no está disponible.

---

## 🧰 Empaquetado (ejecutable)

Ejemplo con PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "lotes_template.csv:." lotes_gui.py
```

Ajusta `--add-data` para incluir carpetas como `registros/` o `assets/` si es necesario.

---

## ⚠️ Advertencias y notas

- Es una aplicación GUI: no está diseñada para ejecutarse en entornos headless sin servidor X/Wayland.
- El token de GitHub se guarda en texto plano; si la seguridad es crítica, usa un gestor de secretos o variables de entorno.
- La exportación a PDF/XLSX requiere librerías opcionales (`reportlab`, `openpyxl`).
- La app crea backups locales automáticamente antes de operaciones que sobrescriben datos.

---

## 🧪 Pruebas y depuración

- Mensajes de error y logs se muestran en consola (útil al empaquetar).
- Si la sincronización falla, la app sigue funcionando en modo local y la barra de estado muestra el estado de conexión.

---

## 📝 Mantenibilidad / Extensiones sugeridas

- Reemplazar almacenamiento de token por variables de entorno o integración con un secret manager.
- Implementar un mecanismo de merge (conservando remoto y agregando solo registros locales únicos) si es necesario.
- Añadir tests automatizados para funciones de import/merge/export.
- Añadir internacionalización si se requiere otro idioma.

---

## 📄 LICENSE

Este repositorio incluye una licencia comercial en `LICENSE`. Titular: Los Cielos Farm (2026). Revisa `LICENSE` para los términos.

---


