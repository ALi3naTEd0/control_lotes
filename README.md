# Control de Lotes — Los Cielos Farm ✅

**Descripción**

Aplicación de escritorio (Tkinter) para registrar y gestionar lotes de cultivo. Permite crear lotes, asignar variedades y cantidades, editar etapas/ubicaciones, exportar informes (PDF/Excel), generar gráficos (radar, pastel, barras) y sincronizar el archivo de datos (`lotes_template.csv`) con un repositorio privado de GitHub.

---

## 📌 Características principales

- Interfaz gráfica con pestañas para crear lotes, agregar variedades y editar lotes.
- Sincronización automática y manual con GitHub (descarga/subida del `lotes_template.csv`).
- Backups automáticos en la carpeta `registros/` y restauración del backup más reciente.
- Exportar listado a PDF (requiere `reportlab`) y a Excel (`openpyxl`).
- Gráficos: radar (sucursal × etapa con IDs), pastel (por etapa) y barras (por ubicación) con detalle de IDs.
- Validaciones: hasta 20 variedades por lote, semana entre 1 y 22, selección de sucursal/etapa/ubicación desde listas predefinidas.
- Soporte para empacar como ejecutable (PyInstaller) — el script contiene comprobaciones para `sys.frozen`.

---

## 🧩 Requisitos

- Python 3.10+ (probado con las versiones en `requirements.txt`)
- Dependencias (instálalas con):

```bash
pip install -r requirements.txt
```

Dependencias destacadas:
- `requests` (sincronización GitHub)
- `matplotlib`, `numpy` (gráficos)
- `reportlab` (exportar PDF, opcional)
- `openpyxl` (exportar Excel, opcional)
- `tkinter` (incluido con Python en la mayoría de distribuciones)

---

## ⚙️ Configuración

1. Edita `github_config.txt` en el mismo directorio del script y agrega:

```
usuario/repo
TOKEN_GITHUB_CON_PERMISO_repo
```

- Línea 1: `usuario/nombre-repo` (ej.: `miusuario/mirepo`)
- Línea 2: Token personal de GitHub con permiso `repo` si quieres sincronizar con un repo privado.

2. Asegúrate de que `lotes_template.csv` exista (si no, la aplicación funciona pero sin datos iniciales).

---

## 🚀 Uso

- Ejecutar localmente:

```bash
python lotes_gui.py
```

- Crear ejecutable con PyInstaller (ejemplo básico):

```bash
pyinstaller --onefile --add-data "lotes_template.csv:." lotes_gui.py
```

(ajusta opciones para incluir `registros/` y otros recursos si lo deseas)

---

## 🔧 Flujo y comportamientos importantes

- Al iniciar, la app intenta descargar `lotes_template.csv` desde GitHub (referencia). Si falla, restaura el último backup local.
- Cada cambio en los lotes guarda en `lotes_template.csv` y lanza sincronización hacia GitHub (`subir_csv_github`).
- Se crean backups timestamped en `registros/` antes de sobrescribir o al cerrar la app.
- Limites: máximo 20 variedades por lote; semana válida 1..22.
- Los desplegables de Sucursal, Etapa y Ubicación son los definidos en las constantes `BRANCH`, `STAGES` y `LOCATIONS` en el código.

---

## 📋 Funciones y módulos clave (resumen)

- `cargar_config()`: carga `github_config.txt` (usuario/repo + token)
- `descargar_csv_github()`: descarga el CSV desde GitHub (API)
- `subir_csv_github()`: sube/actualiza el CSV al repo (API)
- `leer_csv()`: lee `lotes_template.csv` y normaliza datos
- `guardar_csv(lotes)`: escribe el CSV con formato consistente
- `fix_csv_structure()`: normaliza estructura y columnas del CSV
- `crear_backup()`, `restore_latest_backup()`: gestión de backups en `registros/`
- `startup_restore()`: lógica al iniciar para restaurar datos desde GitHub o backup
- `proximo_lote_id()`: cálculo de próximo ID de lote por sucursal
- `crear_lote_gui()`: añade un lote desde la GUI
- `listar_lotes_gui()`: ventana con listado y exportación a PDF/XLSX
- `find_lote_by_selector()`: búsqueda tolerante por ID/label
- `actualizar_etapa_ubicacion()`, `actualizar_semana_lote()`: actualizar metadatos de lote
- `agregar_variedad_lote()`, `eliminar_variedad_lote()`: gestionar variedades
- `refresh_lote_selector()`, `on_lote_select()`: actualizar selectores y vista
- `filtrar_lotes()`: ventana con filtros y resultados
- `grafico_distribucion_por_sucursal()`, `grafico_distribucion_etapas()`, `grafico_distribucion_ubicaciones()`: gráficos interactivos
- `make_gui()`: constructor de la interfaz principal

---

## 🛠️ Recomendaciones y notas de mantenimiento

- Haz commits regulares y mantén backups en `registros/`.
- Asegura que el token de GitHub tenga permisos adecuados y **no** lo subas a repositorios públicos.
- Para despliegue, empaqueta con PyInstaller y prueba en el sistema destino.

---

## 📄 Licencia

Este repositorio incluye un archivo `LICENSE` con una licencia comercial (propietaria) para "Control de Lotes — Los Cielos Farm". Lee el archivo `LICENSE` para detalles sobre uso y restricciones.

---

