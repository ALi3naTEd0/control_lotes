# Control de Lotes — Los Cielos Farm

**Descripción breve**

Aplicación multiplataforma (Flet) para el registro y gestión de lotes de cultivo por sucursal. Soporta Desktop, Web y Android con la misma base de código. Permite crear y editar lotes, asignar variedades y cantidades, generar resúmenes y gráficos simplificados, exportar informes (CSV/Excel/PDF) y sincronizar el archivo principal (`lotes_template.csv`) con un repositorio de GitHub (API).

---

## ✅ Características principales

- Interfaz con pestañas: **Crear lote**, **Lotes (variedades)**, **Editar lote**, **Gráficos**, **Listado** y **Config**. 🔧
- Multiplataforma: Desktop / Android / Web usando Flet. En Android la configuración se guarda en `SharedPreferences` y en desktop en `lotes_config.json`.
- Persistencia y sincronización con GitHub: descarga/subida del archivo `lotes_template.csv` usando la API de GitHub y respaldos automáticos en `registros/`.
- Exportación a CSV, Excel (openpyxl) y PDF (fpdf2). ✏️📄
- Validaciones: máximo 20 variedades por lote, semana válida 1..22, y validaciones obligatorias para `Usuario`, `Repo` y `Token` antes de sincronizar.
- Soporte para tener el mismo `LoteNum` en una sucursal dividido en varias `Location` (ej. `L6-SMB` en `CUARTO 1` y `CUARTO 2`).
- Mensajes de estado claros en la barra: informa si falta token/repo/usuario o si está **Conectado a GitHub**.

---

## 📦 Requisitos (dependencias)

- Python 3.10+ (probado con 3.14)
- Recomendado usar un virtualenv

Paquetes principales (ver `requirements.txt`):

- `flet` (UI multiplataforma)
- `requests` (sincronización GitHub)
- `openpyxl` (exportar Excel, opcional)
- `fpdf2` (exportar PDF, opcional)

Instalación rápida:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ Configuración (GitHub y usuario)

- Archivo desktop: `lotes_config.json` ubicado junto al código. Contiene las claves:

```json
{
  "github_repo": "usuario/repo",
  "github_token": "ghp_xxx...",
  "current_user": "Tu Nombre"
}
```

- En Android la configuración se almacena en `SharedPreferences` bajo la clave `lotes_config`.
- **Importante**: el campo `current_user` es obligatorio para que el commit incluya el nombre en el mensaje y para permitir sincronizar. Si falta `token` o `repo`, la barra de estado mostrará mensajes claros como **Sin token configurado** o **Repo no configurado**.

> Seguridad: El token se guarda en texto plano en los archivos locales; para producción considere usar un gestor de secretos.

---

## 🗂️ Formato de `lotes_template.csv`

Estructura esperada (columnas relevantes):

```
ID,Branch,LoteNum,Stage,Location,Semana,DateCreated,ÚltimaActualización,Notes,Variedad_1,Cantidad_1,...,Variedad_20,Cantidad_20
```

La aplicación incluye funciones para normalizar/backfillear CSVs antiguos y crea backups en `registros/`.

---

## 🔁 Comportamiento de sincronización y commits

- `descargar_csv_github()` y `subir_csv_github()` manejan la lectura/escritura a GitHub vía API.
- El mensaje de commit sigue el formato: `Actualización YYYY-MM-DD HH:MM <Usuario>`.
- Antes de subir, la app valida que `repo`, `token` y `usuario` estén configurados; si falta algún dato la subida se cancela y se muestra un error en la barra y/o snackbar.

---

## 🖥️ Ejecutar la app

- Desktop/Web/Android (ejecutable principal):

```bash
python lotes_flet.py
```

- Nota: `ft.app(main)` se usa para ejecutar la app; en versiones recientes de Flet se recomienda `ft.run(main)` pero la invocación del script es compatible.

---

## 🔧 Comportamiento y notas de uso

- Crear lote: se permite tener mismo `LoteNum` por sucursal en diferentes `Location` (split). La creación bloquea duplicados exactos (misma sucursal + mismo número + misma ubicación).
- Variedades: pestaña para agregar/eliminar variedades por lote; la UI carga la lista de variedades al abrir la pestaña.
- Estado de conexión: muestra mensajes específicos si falta `Token`, `Repo` o `Usuario`. `Reconectar` y `Sincronizar` prueban la conexión y la subida.
- Limpiar configuración: borra `lotes_config.json` en desktop y `SharedPreferences` en Android, y limpia la memoria y la UI.

---

## 🧪 Depuración

- Los errores y mensajes importantes se muestran en consola (útil al ejecutar o empacar).
- Se han añadido comprobaciones para evitar errores de UI al actualizar controles (especialmente en Android y Web).

---

## 📝 Sugerencias de mantenimiento

- Mover el token a una solución segura (secret manager o variables de entorno) si la seguridad es crítica.
- Implementar tests automatizados para las funciones de import/merge/export y sincronización.
- Mejorar el proceso de merge entre cambios remotos y locales si se necesita conciliación más avanzada.

---

## 📄 LICENSE

Este repositorio incluye una licencia en `LICENSE`. Titular: Los Cielos Farm (2026). Revisa `LICENSE` para los términos.

---

