import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import sys
import base64
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import requests

ROOT = os.path.dirname(__file__)

# Global for status update callback
update_status = None


# Soporte para ejecutable PyInstaller: buscar archivo en la misma carpeta que el .exe o script
if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Archivo de configuración para credenciales de GitHub
CONFIG_FILE = os.path.join(BASE_PATH, "github_config.txt")
LOTES_CSV = os.path.join(BASE_PATH, "lotes_template.csv")

def cargar_config():
    """Carga la configuración del repo desde archivo github_config.txt"""
    if not os.path.exists(CONFIG_FILE):
        # Crear archivo de ejemplo
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write("usuario/nombre-repo\nTU_TOKEN_AQUI\n")
        print(f"ERROR: Configura tus credenciales en: {CONFIG_FILE}")
        print("Línea 1: usuario/repo (ej: ALi3naTEd0/entradas_salidas)")
        print("Línea 2: TOKEN de GitHub con permiso 'repo'")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        lineas = f.read().strip().split("\n")
    if len(lineas) < 2:
        print(f"ERROR: El archivo {CONFIG_FILE} debe tener 2 líneas:")
        print("Línea 1: usuario/repo")
        print("Línea 2: TOKEN de GitHub")
        sys.exit(1)
    repo = lineas[0].strip()
    token = lineas[1].strip()
    if "TU_TOKEN_AQUI" in token or "/" not in repo:
        print(f"ERROR: Edita el archivo {CONFIG_FILE} con tus credenciales reales")
        sys.exit(1)
    return repo, token

# Cargar configuración

GITHUB_REPO, GITHUB_TOKEN = cargar_config()
GITHUB_FILE_PATH = "lotes_template.csv"
GITHUB_BRANCH = "main"
VERSION = '1.0.0'
BRANCH = ['FSM', 'SMB', 'RP']
STAGES = ['CLONADO','VEG. TEMPRANO','VEG. TARDIO','FLORACIÓN','TRANSICIÓN','SECADO','PT']
LOCATIONS = ['PT','CUARTO 1','CUARTO 2','CUARTO 3','CUARTO 4','VEGETATIVO','ENFERMERÍA','MADRES']
# Lista de variedades (ajusta según tus datos)
VARIETIES = [
    'Ak-47',
    'Apple Fritter',
    'Banana Latte',
    'Blackberry Honey',
    'Desconocida',
    'Gran Jefa',
    'HG23 (Michael Jordan)',
    'Kandy Kush',
    'King Kush Breath',
    'Kosher Kush',
    'Mozzerella',
    'Orangel',
    'Purple Diesel',
    'ReCon',
    'Red Red Wine',
    'Runtz',
    'Sugar Cane',
    'Wedding Cake',
    'Zallah Bread',
]

def descargar_csv_github():
    """Descarga el CSV desde GitHub (repo privado)."""
    if not GITHUB_TOKEN:
        return False, 'Sin token configurado'
    
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {'ref': GITHUB_BRANCH}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            import base64
            contenido = base64.b64decode(data['content']).decode('utf-8')
            with open(LOTES_CSV, 'w', encoding='utf-8') as f:
                f.write(contenido)
            # Normalizar estructura local (asegura columna Semana y mueve fechas si fuera necesario)
            try:
                fix_csv_structure()
            except Exception:
                pass
            return True, 'Conectado' 
        elif response.status_code == 401:
            return False, f'Token inválido o sin permisos. Verifica el token en github_config.txt y que tenga permisos repo.'
        elif response.status_code == 404:
            return False, f'Repo o archivo no encontrado. Verifica el nombre del repo ({GITHUB_REPO}) y el archivo ({GITHUB_FILE_PATH}) en github_config.txt.'
        else:
            return False, f'Error HTTP {response.status_code}: {response.text[:100]}'
    except requests.exceptions.ConnectionError as ce:
        return False, f'Sin conexión a internet: {ce}'
    except requests.exceptions.Timeout as te:
        return False, f'Timeout de conexión: {te}'
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return False, f'Error inesperado: {str(e)}\n{tb[:200]}'


def subir_csv_github():
    """Sube el CSV a GitHub (repo privado)."""
    if not GITHUB_TOKEN:
        messagebox.showwarning('Aviso', 'No hay token de GitHub configurado')
        return False
    
    # Primero obtener el SHA del archivo actual
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {'ref': GITHUB_BRANCH}
    
    try:
        # Obtener SHA actual
        response = requests.get(url, headers=headers, params=params, timeout=10)
        sha = response.json().get('sha', '') if response.status_code == 200 else ''
        
        # Leer contenido local
        with open(LOTES_CSV, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import base64
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Subir archivo
        data = {
            'message': f'Actualización lotes - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            'content': encoded_content,
            'branch': GITHUB_BRANCH
        }
        if sha:
            data['sha'] = sha
        
        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code in [200, 201]:
            # Mostrar mensaje en barra de estado si update_status está disponible
            try:
                update_status(True, 'CSV sincronizado con GitHub')
            except Exception:
                pass
            return True
        else:
            try:
                update_status(False, f'Error subiendo: {response.status_code}')
            except Exception:
                messagebox.showerror('Error', f'Error subiendo: {response.status_code}')
            return False
    except Exception as e:
        messagebox.showerror('Error', f'Error de conexión: {e}')
        return False


def leer_csv():
    """Lee lotes del CSV. Retorna lista de dicts."""
    if not os.path.exists(LOTES_CSV):
        return []
    lotes = []
    try:
        with open(LOTES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            lotes = []
            for row in reader:
                # Extraer variedades/cantidades
                variedades = []
                for i in range(1, 21):
                    v_raw = row.get(f'Variedad_{i}', '')
                    c_raw = row.get(f'Cantidad_{i}', '')
                    v = v_raw.strip() if v_raw else ''
                    c = c_raw.strip() if c_raw else ''
                    if v:
                        try:
                            c = int(c)
                        except:
                            c = 0
                        variedades.append({'name': v, 'count': c})
                # Arreglar caso donde el CSV antiguo no tenía columna 'Semana' y la fecha quedó en esa columna
                sem_val = row.get('Semana', '')
                if sem_val and isinstance(sem_val, str) and sem_val.strip() and '-' in sem_val and sem_val.strip()[0].isdigit():
                    # fecha estaba en la columna 'Semana', moverla a DateCreated y dejar Semana vacía
                    row['DateCreated'] = sem_val.strip()
                    row['Semana'] = ''
                row['Variedades'] = variedades
                lotes.append(row)
    except Exception as e:
        messagebox.showerror('Error', f'No se pudo leer CSV: {e}')
    return lotes


def guardar_csv(lotes):
    """Guarda lotes en el CSV (con LoteNum almacenado)."""
    try:
        with open(LOTES_CSV, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['ID','Branch','LoteNum','Stage','Location','Semana','DateCreated','Notes']
            for i in range(1, 21):
                fieldnames.append(f'Variedad_{i}')
                fieldnames.append(f'Cantidad_{i}')
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            writer.writeheader()
            for lote in lotes:
                row = {k: lote.get(k, '') for k in fieldnames}
                # Escribir variedades/cantidades
                variedades = lote.get('Variedades', [])
                for i in range(1, 21):
                    if i <= len(variedades):
                        row[f'Variedad_{i}'] = variedades[i-1]['name']
                        row[f'Cantidad_{i}'] = variedades[i-1]['count']
                    else:
                        row[f'Variedad_{i}'] = ''
                        row[f'Cantidad_{i}'] = ''
                writer.writerow(row)
    except Exception as e:
        messagebox.showerror('Error', f'No se pudo guardar CSV: {e}')


def fix_csv_structure():
    """Normaliza la estructura del CSV local: asegura columnas correctas y mueve fechas mal colocadas."""
    # leer_csv ya arregla casos donde la fecha quedó en la columna 'Semana'
    try:
        lotes = leer_csv()
        # Reescribir usando guardar_csv con el orden correcto de columnas
        guardar_csv(lotes)
    except Exception:
        pass


def proximo_lote_id(branch):
    """Calcula el próximo LoteID para la sucursal."""
    lotes = leer_csv()
    lotes_rama = [l for l in lotes if l.get('Branch') == branch]
    n = len(lotes_rama) + 1
    return f"L{n}-{branch}"


def crear_lote_gui(branch_var, lote_num, stage_var, location_var, semana_var, notes_var, date_var):
    branch = branch_var.get()
    lote_num_sel = lote_num.get()
    stage = stage_var.get()
    location = location_var.get()
    semana = semana_var.get()
    notes = notes_var.get()
    date = date_var.get() or datetime.now().strftime('%Y-%m-%d')

    if branch not in BRANCH:
        messagebox.showerror('Error', 'Sucursal inválida')
        return
    if stage not in STAGES:
        messagebox.showerror('Error', 'Etapa inválida')
        return
    if location not in LOCATIONS:
        messagebox.showerror('Error', 'Ubicación inválida')
        return

    # Validar semana (1-22)
    try:
        semana_int = int(semana)
        if not 1 <= semana_int <= 22:
            raise ValueError
    except Exception:
        messagebox.showerror('Error', 'Semana inválida (1-22)')
        return

    lotes = leer_csv()
    lotes_rama = [l for l in lotes if l.get('Branch') == branch]
    
    # Calcular número de lote por rama
    if lote_num_sel == 'AUTO':
        n = len(lotes_rama) + 1
    else:
        try:
            n = int(lote_num_sel.lstrip('L'))
            # Validar que el número no esté ya usado en esta rama
            lotes_por_rama = {}
            for lote in lotes:
                b = lote.get('Branch')
                if b not in lotes_por_rama:
                    lotes_por_rama[b] = 0
                lotes_por_rama[b] += 1
                if b == branch and lotes_por_rama[b] == n:
                    messagebox.showerror('Error', f'El lote L{n}-{branch} ya existe')
                    return
        except Exception:
            messagebox.showerror('Error', 'Número de lote inválido')
            return

    # Crear entrada con LoteNum almacenado

    entry = {
        'ID': f"L{n}-{branch}",
        'Branch': branch,
        'LoteNum': str(n),
        'Stage': stage,
        'Location': location,
        'Semana': str(semana_int),
        'DateCreated': date,
        'Notes': notes or '',
        'Variedades': []
    }

    lotes.append(entry)
    guardar_csv(lotes)
    # Sincronizar con GitHub automáticamente
    subir_csv_github()
    lote_id = f"L{n}-{branch}"
    messagebox.showinfo('Creado', f'Lote creado: {lote_id}')
    try:
        refresh_lote_selector()
    except Exception:
        pass


def listar_lotes_gui():
    """Abre ventana con listado de todos los lotes."""
    lotes = leer_csv()
    # Ordenar lotes por branch y número de lote (alfanumérico)
    def lote_id_key(lote):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        try:
            num = int(lote_num)
        except Exception:
            num = 0
        return (branch, num)
    lotes_sorted = sorted(lotes, key=lote_id_key)
    win = tk.Toplevel()
    win.title('Listado de lotes')
    # Frame para botones de exportación
    btn_export_frame = ttk.Frame(win)
    btn_export_frame.pack(side='top', fill='x', pady=4)

    def exportar_pdf():
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from tkinter import filedialog
        except ImportError:
            messagebox.showerror('Error', 'Falta instalar reportlab: pip install reportlab')
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF files', '*.pdf')], title='Guardar como PDF')
        if not file_path:
            return
        c = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter
        y = height - 40
        c.setFont('Helvetica-Bold', 14)
        c.drawString(40, y, 'Listado de Lotes')
        y -= 30
        c.setFont('Helvetica', 9)
        for lote in lotes_sorted:
            if y < 60:
                c.showPage()
                y = height - 40
                c.setFont('Helvetica', 9)
            branch = lote.get('Branch')
            lote_num = lote.get('LoteNum')
            lote_id = f"L{lote_num}-{branch}"
            total = 0
            vars_formatted = ''
            variedades = lote.get('Variedades', [])
            if variedades:
                vars_list = [f"{v['name']} ({v['count']})" for v in variedades]
                total = sum(v['count'] for v in variedades)
                vars_formatted = '; '.join(vars_list)
            c.setFont('Helvetica-Bold', 10)
            c.drawString(40, y, f"{lote_id}")
            y -= 14
            c.setFont('Helvetica', 9)
            c.drawString(60, y, f"Sucursal: {branch}   Etapa: {lote['Stage']}   Ubicación: {lote['Location']}")
            y -= 12
            c.drawString(60, y, f"Variedades: {vars_formatted}")
            y -= 12
            c.drawString(60, y, f"Total: {total} plantas   Fecha: {lote['DateCreated']}")
            y -= 12
            if lote.get('Notes'):
                c.drawString(60, y, f"Notas: {lote.get('Notes','')}")
                y -= 12
            c.line(40, y, width-40, y)
            y -= 10
        c.save()
        messagebox.showinfo('Exportar PDF', f'Exportado a {file_path}')

    def exportar_xlsx():
        try:
            import openpyxl
            from openpyxl.styles import Font
            from tkinter import filedialog
        except ImportError:
            messagebox.showerror('Error', 'Falta instalar openpyxl: pip install openpyxl')
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx')], title='Guardar como Excel')
        if not file_path:
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Lotes'
        headers = ['ID', 'Sucursal', 'Etapa', 'Ubicación', 'Variedades', 'Total', 'Fecha', 'Notas']
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for lote in lotes_sorted:
            branch = lote.get('Branch')
            lote_num = lote.get('LoteNum')
            lote_id = f"L{lote_num}-{branch}"
            total = 0
            vars_formatted = ''
            variedades = lote.get('Variedades', [])
            if variedades:
                vars_list = [f"{v['name']} ({v['count']})" for v in variedades]
                total = sum(v['count'] for v in variedades)
                vars_formatted = '; '.join(vars_list)
            ws.append([
                lote_id,
                branch,
                lote['Stage'],
                lote['Location'],
                vars_formatted,
                total,
                lote['DateCreated'],
                lote.get('Notes','')
            ])
        wb.save(file_path)
        messagebox.showinfo('Exportar Excel', f'Exportado a {file_path}')

    btn_pdf = ttk.Button(btn_export_frame, text='Exportar a PDF', command=exportar_pdf)
    btn_pdf.pack(side='left', padx=4)
    btn_xls = ttk.Button(btn_export_frame, text='Exportar a Excel', command=exportar_xlsx)
    btn_xls.pack(side='left', padx=4)

    text = tk.Text(win, width=100, height=40)
    text.pack(fill='both', expand=True)
    if not lotes_sorted:
        text.insert('end', 'No hay lotes registrados.\n')
        return
    # Insertar encabezado
    text.insert('end', '='*100 + '\n')
    # Construir IDs desde LoteNum
    for idx, lote in enumerate(lotes_sorted):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        lote_id = f"L{lote_num}-{branch}"
        # Mostrar variedades correctamente
        total = 0
        vars_formatted = ''
        variedades = lote.get('Variedades', [])
        if variedades:
            vars_list = [f"{v['name']} ({v['count']})" for v in variedades]
            total = sum(v['count'] for v in variedades)
            vars_formatted = '; '.join(vars_list)
        # Formato mejorado con saltos de línea
        text.insert('end', f"\n【 {lote_id} 】\n")
        text.insert('end', f"  Sucursal:    {branch}\n")
        text.insert('end', f"  Etapa:       {lote['Stage']}\n")
        text.insert('end', f"  Ubicación:   {lote['Location']}\n")
        text.insert('end', f"  Variedades:  {vars_formatted}\n")
        text.insert('end', f"  Total:       {total} plantas\n")
        text.insert('end', f"  Fecha:       {lote['DateCreated']}\n")
        if lote.get('Notes'):
            text.insert('end', f"  Notas:       {lote.get('Notes','')}\n")
        text.insert('end', '-'*100 + '\n')


def find_lote_by_selector(lote_identifier):
    """Devuelve (index, lote) buscando por calc_id (L{n}-{branch}), por el campo ID o por la cadena de display 'L{n}-{branch} | Location | DateCreated'."""
    lotes = leer_csv()
    for idx, lote in enumerate(lotes):
        calc_id = f"L{lote.get('LoteNum')}-{lote.get('Branch')}"
        display = f"{calc_id} | {lote.get('Location','')} | {lote.get('DateCreated','')}"
        if lote_identifier == calc_id or lote_identifier == lote.get('ID') or lote_identifier == display:
            return idx, lote
    return None, None


def actualizar_etapa_ubicacion(lote_id, new_stage, new_location):
    """Actualiza la etapa y ubicación de un lote. lote_id puede ser display o calc_id."""
    lotes = leer_csv()
    idx, lote = find_lote_by_selector(lote_id)
    if lote is None:
        return False
    lote['Stage'] = new_stage
    lote['Location'] = new_location
    guardar_csv(lotes)
    return True


def actualizar_semana_lote(lote_id, nueva_semana):
    """Actualiza la semana de un lote (1-22). lote_id puede ser display o calc_id."""
    lotes = leer_csv()
    idx, lote = find_lote_by_selector(lote_id)
    if lote is None:
        return False
    lote['Semana'] = str(nueva_semana)
    guardar_csv(lotes)
    # Subir cambios a GitHub
    try:
        subir_csv_github()
    except Exception:
        pass
    return True





def agregar_variedad_lote(lote_id, name, qty):
    """Agrega o suma cantidad de una variedad a un lote."""
    lotes = leer_csv()
    idx, lote = find_lote_by_selector(lote_id)
    if lote is None:
        messagebox.showerror('Error', 'No se encontró el lote')
        return False
    vars_list = lote.get('Variedades', [])
    found = False
    for v in vars_list:
        if v['name'] == name:
            v['count'] += qty
            found = True
            break
    if not found:
        if len(vars_list) >= 20:
            messagebox.showerror('Error', 'No se pueden agregar más de 20 variedades por lote.')
            return False
        vars_list.append({'name': name, 'count': qty})
    lote['Variedades'] = vars_list
    guardar_csv(lotes)
    subir_csv_github()
    return True


def eliminar_variedad_lote(lote_id, idx):
    """Elimina una variedad por índice."""
    lotes = leer_csv()
    lot_idx, lote = find_lote_by_selector(lote_id)
    if lote is None:
        return False
    vars_list = lote.get('Variedades', [])
    if 0 <= idx < len(vars_list):
        del vars_list[idx]
        lote['Variedades'] = vars_list
        guardar_csv(lotes)
        subir_csv_github()
        return True
    return False


def refresh_lote_selector():
    """Actualiza el selector de lotes en Tab2."""
    lotes = leer_csv()
    # Generar IDs desde LoteNum y ordenarlos alfanuméricamente (L4 antes que L5)
    def lote_id_key(lote):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        try:
            num = int(lote_num)
        except Exception:
            num = 0
        return (branch, num)
    lotes_sorted = sorted(lotes, key=lote_id_key)
    ids = [f"L{lote.get('LoteNum')}-{lote.get('Branch')} | {lote.get('Location','')} | {lote.get('DateCreated','')}" for lote in lotes_sorted]
    lote_selector['values'] = ids
    if ids:
        lote_selector.set(ids[0])
        on_lote_select()


def on_lote_select(event=None):
    """Muestra variedades del lote seleccionado."""
    sel = lote_selector.get()
    var_listbox_tab2.delete(0, 'end')
    # Forzar recarga del CSV para obtener los datos más recientes
    lotes = leer_csv()
    idx, lote = find_lote_by_selector(sel)
    if lote is None:
        try:
            stage_label_tab2.config(text='')
            location_label_tab2.config(text='')
            semana_label_tab2.config(text='')
            total_label_tab2.config(text='TOTAL: 0')
        except Exception:
            pass
        return
    total = 0
    vars_list = []
    variedades = lote.get('Variedades', [])
    for v in variedades:
        vars_list.append(f"{v['name']} ({v['count']})")
        total += v['count']
    # Ordenar alfabéticamente y mostrar
    vars_list.sort()
    for var_pair in vars_list:
        var_listbox_tab2.insert('end', var_pair)
    # Actualizar labels de info
    stage_label_tab2.config(text=lote.get('Stage',''))
    location_label_tab2.config(text=lote.get('Location',''))
    semana_label_tab2.config(text=lote.get('Semana',''))
    total_label_tab2.config(text=f'TOTAL: {total}')


def filtrar_lotes(branch_filter, stage_filter, location_filter, lote_id_filter=None, variety_filter=None):
    """Filtra lotes y muestra en una ventana con formato mejorado."""
    lotes = leer_csv()
    filtered = []
    for lote in lotes:
        if branch_filter and lote.get('Branch') != branch_filter:
            continue
        if stage_filter and lote.get('Stage') != stage_filter:
            continue
        if location_filter and lote.get('Location') != location_filter:
            continue
        if lote_id_filter:
            branch = lote.get('Branch')
            lote_num = lote.get('LoteNum')
            calc_id = f"L{lote_num}-{branch}"
            display = f"{calc_id} | {lote.get('Location','')} | {lote.get('DateCreated','')}"
            if not (calc_id == lote_id_filter or display == lote_id_filter or lote.get('ID') == lote_id_filter):
                continue
        if variety_filter:
            variedades = lote.get('Variedades', [])
            if not any(v['name'] == variety_filter for v in variedades):
                continue
        filtered.append(lote)
    
    # Ordenar los lotes filtrados por branch y número de lote (alfanumérico)
    def lote_id_key(lote):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        try:
            num = int(lote_num)
        except Exception:
            num = 0
        return (branch, num)
    filtered_sorted = sorted(filtered, key=lote_id_key)
    win = tk.Toplevel()
    win.title('Lotes filtrados')
    text = tk.Text(win, width=100, height=40)
    text.pack(fill='both', expand=True)
    if not filtered_sorted:
        text.insert('end', 'No hay lotes que cumplan los filtros.\n')
        return
    # Insertar encabezado con filtros aplicados
    text.insert('end', '='*100 + '\n')
    text.insert('end', 'FILTROS APLICADOS:\n')
    if branch_filter:
        text.insert('end', f'  - Sucursal: {branch_filter}\n')
    if stage_filter:
        text.insert('end', f'  - Etapa: {stage_filter}\n')
    if location_filter:
        text.insert('end', f'  - Ubicación: {location_filter}\n')
    if lote_id_filter:
        text.insert('end', f'  - Lote: {lote_id_filter}\n')
    if variety_filter:
        text.insert('end', f'  - Variedad: {variety_filter}\n')
    text.insert('end', f'\nResultados: {len(filtered_sorted)} lote(s)\n')
    text.insert('end', '='*100 + '\n')
    # Construir IDs desde LoteNum con formato mejorado
    for idx, lote in enumerate(filtered_sorted):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        lote_id = f"L{lote_num}-{branch}"
        # Recalcular total de lote
        total = 0
        vars_formatted = ''
        variedades = lote.get('Variedades', [])
        if variedades:
            vars_list = [f"{v['name']} ({v['count']})" for v in variedades]
            total = sum(v['count'] for v in variedades)
            vars_formatted = '; '.join(vars_list)
        # Formato mejorado con saltos de línea
        text.insert('end', f"\n【 {lote_id} 】\n")
        text.insert('end', f"  Sucursal:    {branch}\n")
        text.insert('end', f"  Etapa:       {lote['Stage']}\n")
        text.insert('end', f"  Ubicación:   {lote['Location']}\n")
        text.insert('end', f"  Variedades:  {vars_formatted}\n")
        text.insert('end', f"  Total:       {total} plantas\n")
        text.insert('end', f"  Fecha:       {lote['DateCreated']}\n")
        if lote.get('Notes'):
            text.insert('end', f"  Notas:       {lote.get('Notes','')}\n")
        text.insert('end', '-'*100 + '\n')


def grafico_distribucion_por_sucursal():
    """Gráfico radar/polar de cantidad de lotes por sucursal y etapa con IDs."""
    lotes = leer_csv()
    
    # Contar lotes por sucursal y etapa, y guardar IDs desde LoteNum
    data = {}
    lotes_ids = {}
    
    for lote in lotes:
        branch = lote.get('Branch')
        stage = lote.get('Stage')
        lote_num = lote.get('LoteNum')
        lote_id = f"L{lote_num}-{branch}"
        
        key = (branch, stage)
        data[key] = data.get(key, 0) + 1
        if key not in lotes_ids:
            lotes_ids[key] = []
        lotes_ids[key].append(lote_id)
    
    if not data:
        messagebox.showinfo('Gráficos', 'No hay lotes para graficar.')
        return
    
    # Preparar datos para gráfico de radar
    branches = list(set(l[0] for l in data.keys()))
    stages = list(set(l[1] for l in data.keys()))
    
    fig = Figure(figsize=(10, 10), dpi=100)
    ax = fig.add_subplot(111, projection='polar')
    
    angles = np.linspace(0, 2 * np.pi, len(branches), endpoint=False).tolist()
    angles += angles[:1]  # Cerrar el polígono
    
    for stage in stages:
        values = [data.get((b, stage), 0) for b in branches]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=stage)
        ax.fill(angles, values, alpha=0.15)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(branches)
    ax.set_ylim(0, max([v for v in data.values()]) + 1)
    ax.set_title('Distribución de Lotes por Sucursal y Etapa', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    ax.grid(True)
    
    # Crear texto con detalles
    info_text = "Detalle de Lotes:\n"
    for (branch, stage), ids in lotes_ids.items():
        info_text += f"{branch} | {stage}: {', '.join(ids)}\n"
    
    win = tk.Toplevel()
    win.title('Gráfico Radar - Lotes por Sucursal y Etapa')
    win.geometry('1000x700')
    
    frame_gra = ttk.Frame(win)
    frame_gra.pack(side='left', fill='both', expand=True)
    canvas = FigureCanvasTkAgg(fig, master=frame_gra)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    
    frame_info = ttk.Frame(win, width=250)
    frame_info.pack(side='right', fill='both')
    text_info = tk.Text(frame_info, width=35, height=40, wrap='word')
    text_info.pack(fill='both', expand=True, padx=5, pady=5)
    text_info.insert('end', info_text)
    text_info.config(state='disabled')


def grafico_distribucion_etapas():
    """Gráfico de pastel (pie chart) de lotes por etapa con IDs."""
    lotes = leer_csv()
    
    # Contar por etapa y guardar IDs desde LoteNum
    por_etapa = {}
    lotes_ids_etapa = {}
    
    for lote in lotes:
        stage = lote.get('Stage')
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        lote_id = f"L{lote_num}-{branch}"
        
        por_etapa[stage] = por_etapa.get(stage, 0) + 1
        if stage not in lotes_ids_etapa:
            lotes_ids_etapa[stage] = []
        lotes_ids_etapa[stage].append(lote_id)
    
    if not por_etapa:
        messagebox.showinfo('Gráficos', 'No hay lotes para graficar.')
        return
    
    fig = Figure(figsize=(10, 8), dpi=100)
    ax = fig.add_subplot(111)
    
    labels = list(por_etapa.keys())
    sizes = list(por_etapa.values())
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                        colors=colors, startangle=90)
    ax.set_title('Distribución de Lotes por Etapa')
    
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontweight('bold')
    
    # Crear texto con detalles
    info_text = "Detalle de Lotes por Etapa:\n\n"
    for stage, ids in lotes_ids_etapa.items():
        info_text += f"{stage} ({len(ids)} lotes):\n"
        info_text += f"  {', '.join(ids)}\n\n"
    
    win = tk.Toplevel()
    win.title('Gráfico de Etapas')
    win.geometry('900x600')
    
    frame_gra = ttk.Frame(win)
    frame_gra.pack(side='left', fill='both', expand=True)
    canvas = FigureCanvasTkAgg(fig, master=frame_gra)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    
    frame_info = ttk.Frame(win, width=250)
    frame_info.pack(side='right', fill='both')
    text_info = tk.Text(frame_info, width=30, height=40, wrap='word')
    text_info.pack(fill='both', expand=True, padx=5, pady=5)
    text_info.insert('end', info_text)
    text_info.config(state='disabled')


def grafico_distribucion_ubicaciones():
    """Gráfico de barras de lotes por ubicación con IDs."""
    lotes = leer_csv()
    
    # Contar por ubicación y guardar IDs desde LoteNum
    por_ubicacion = {}
    lotes_ids_ubicacion = {}
    
    for lote in lotes:
        location = lote.get('Location')
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        lote_id = f"L{lote_num}-{branch}"
        
        por_ubicacion[location] = por_ubicacion.get(location, 0) + 1
        if location not in lotes_ids_ubicacion:
            lotes_ids_ubicacion[location] = []
        lotes_ids_ubicacion[location].append(lote_id)
    
    if not por_ubicacion:
        messagebox.showinfo('Gráficos', 'No hay lotes para graficar.')
        return
    
    fig = Figure(figsize=(12, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    locations = list(por_ubicacion.keys())
    counts = list(por_ubicacion.values())
    colors = plt.cm.Spectral(np.linspace(0, 1, len(locations)))
    
    bars = ax.bar(locations, counts, color=colors)
    ax.set_xlabel('Ubicación', fontsize=11, fontweight='bold')
    ax.set_ylabel('Cantidad de Lotes', fontsize=11, fontweight='bold')
    ax.set_title('Distribución de Lotes por Ubicación')
    ax.tick_params(axis='x', rotation=45)
    
    # Agregar valor en cada barra
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(count)}', ha='center', va='bottom', fontweight='bold')
    
    fig.tight_layout()
    
    # Crear texto con detalles
    info_text = "Detalle de Lotes por Ubicación:\n\n"
    for loc, ids in lotes_ids_ubicacion.items():
        info_text += f"{loc} ({len(ids)} lotes):\n"
        info_text += f"  {', '.join(ids)}\n\n"
    
    win = tk.Toplevel()
    win.title('Gráfico de Ubicaciones')
    win.geometry('1000x600')
    
    frame_gra = ttk.Frame(win)
    frame_gra.pack(side='left', fill='both', expand=True)
    canvas = FigureCanvasTkAgg(fig, master=frame_gra)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)
    
    frame_info = ttk.Frame(win, width=250)
    frame_info.pack(side='right', fill='both')
    text_info = tk.Text(frame_info, width=30, height=40, wrap='word')
    text_info.pack(fill='both', expand=True, padx=5, pady=5)
    text_info.insert('end', info_text)
    text_info.config(state='disabled')


def make_gui():
    root = tk.Tk()
    root.title('Control de Lotes')
    root.geometry('900x600')

    nb = ttk.Notebook(root)
    nb.pack(fill='both', expand=True)

    # Tab 1: Crear lote
    tab1 = ttk.Frame(nb, padding=12)
    nb.add(tab1, text='Crear lote')

    ttk.Label(tab1, text='Sucursal').grid(column=0, row=0, sticky='w')
    branch_var = tk.StringVar(value=BRANCH[0])
    branch_cb = ttk.Combobox(tab1, textvariable=branch_var, values=BRANCH, state='readonly')
    branch_cb.grid(column=1, row=0, sticky='ew')

    ttk.Label(tab1, text='Nº Lote').grid(column=2, row=0, sticky='w')
    lote_num = tk.StringVar(value='AUTO')
    lote_nums = ['AUTO'] + [f'L{i}' for i in range(1, 33)]
    lote_num_cb = ttk.Combobox(tab1, textvariable=lote_num, values=lote_nums, state='readonly', width=8)
    lote_num_cb.grid(column=3, row=0, sticky='w')

    ttk.Label(tab1, text='Etapa').grid(column=0, row=1, sticky='w')
    stage_var = tk.StringVar(value=STAGES[0])
    stage_cb = ttk.Combobox(tab1, textvariable=stage_var, values=STAGES, state='readonly')
    stage_cb.grid(column=1, row=1, sticky='ew')

    ttk.Label(tab1, text='Ubicación').grid(column=2, row=1, sticky='w')
    location_var = tk.StringVar(value=LOCATIONS[0])
    location_cb = ttk.Combobox(tab1, textvariable=location_var, values=LOCATIONS, state='readonly')
    location_cb.grid(column=3, row=1, sticky='ew')

    # Semana (1-22)
    ttk.Label(tab1, text='Semana').grid(column=0, row=2, sticky='w')
    semana_var = tk.StringVar(value='1')
    semana_vals = [str(i) for i in range(1, 23)]
    semana_cb = ttk.Combobox(tab1, textvariable=semana_var, values=semana_vals, state='readonly', width=6)
    semana_cb.grid(column=1, row=2, sticky='w')

    # Las variedades se gestionan desde la pestaña 'Agregar variedades'.
    # Controles relacionados con variedad eliminados de esta pestaña para evitar confusión.

    ttk.Label(tab1, text='Fecha (YYYY-MM-DD)').grid(column=0, row=4, sticky='w')
    date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
    date_entry = ttk.Entry(tab1, textvariable=date_var)
    date_entry.grid(column=1, row=4, sticky='ew')

    ttk.Label(tab1, text='Notas').grid(column=0, row=5, sticky='nw')
    notes_var = tk.StringVar()
    notes_entry = ttk.Entry(tab1, textvariable=notes_var, width=50)
    notes_entry.grid(column=1, row=5, sticky='ew')

    btn_frame = ttk.Frame(tab1)
    btn_frame.grid(column=0, row=6, columnspan=5, pady=10)

    create_btn = ttk.Button(btn_frame, text='Crear lote', command=lambda: crear_lote_gui(branch_var, lote_num, stage_var, location_var, semana_var, notes_var, date_var))
    create_btn.grid(column=0, row=0, padx=4)

    list_btn = ttk.Button(btn_frame, text='Listar todos', command=listar_lotes_gui)
    list_btn.grid(column=1, row=0, padx=4)

    # Tab 2: Agregar variedades a lotes existentes
    tab2 = ttk.Frame(nb, padding=12)
    nb.add(tab2, text='Agregar variedades')

    ttk.Label(tab2, text='Seleccionar lote').grid(column=0, row=0, sticky='w')
    global lote_selector, var_listbox_tab2, stage_label_tab2, location_label_tab2, semana_label_tab2
    lote_selector = ttk.Combobox(tab2, values=[], state='readonly', width=30)
    lote_selector.grid(column=1, row=0, sticky='w')
    lote_selector.bind('<<ComboboxSelected>>', on_lote_select)

    refresh_btn = ttk.Button(tab2, text='Refrescar lista', command=refresh_lote_selector)
    refresh_btn.grid(column=2, row=0, padx=4)

    # Frame for listbox and scrollbar
    var_listbox_frame = ttk.Frame(tab2)
    var_listbox_frame.grid(column=0, row=1, columnspan=3, sticky='ew', pady=6)

    # Header inside frame to show Etapa, Ubicación y Semana del lote seleccionado
    header_frame = ttk.Frame(var_listbox_frame)
    header_frame.pack(side='top', fill='x', padx=4, pady=(0,4))
    ttk.Label(header_frame, text='Etapa:').pack(side='left')
    stage_label_tab2 = ttk.Label(header_frame, text='', font=('TkDefaultFont', 10, 'bold'))
    stage_label_tab2.pack(side='left', padx=(4,12))
    ttk.Label(header_frame, text='Ubicación:').pack(side='left')
    location_label_tab2 = ttk.Label(header_frame, text='', font=('TkDefaultFont', 10, 'bold'))
    location_label_tab2.pack(side='left', padx=(4,12))
    ttk.Label(header_frame, text='Semana:').pack(side='left')
    semana_label_tab2 = ttk.Label(header_frame, text='', font=('TkDefaultFont', 10, 'bold'))
    semana_label_tab2.pack(side='left', padx=(4,0))

    var_listbox_tab2 = tk.Listbox(var_listbox_frame, height=16, width=80)
    var_listbox_tab2.pack(side='left', fill='both', expand=True)

    var_scrollbar_tab2 = ttk.Scrollbar(var_listbox_frame, orient='vertical', command=var_listbox_tab2.yview)
    var_scrollbar_tab2.pack(side='right', fill='y')
    var_listbox_tab2.config(yscrollcommand=var_scrollbar_tab2.set) 

    global total_label_tab2
    total_label_tab2 = ttk.Label(tab2, text='TOTAL: 0', font=('TkDefaultFont', 10, 'bold'))
    total_label_tab2.grid(column=0, row=2, columnspan=3, sticky='w', pady=(0, 6))

    ttk.Label(tab2, text='Variedad').grid(column=0, row=3, sticky='w')
    variety_tab2 = tk.StringVar(value=sorted(VARIETIES)[0])
    variety_cb2 = ttk.Combobox(tab2, textvariable=variety_tab2, values=sorted(VARIETIES))
    variety_cb2.grid(column=1, row=3, sticky='ew')

    ttk.Label(tab2, text='Cantidad').grid(column=2, row=3, sticky='w')
    qty_tab2 = tk.StringVar(value='1')
    qty_entry2 = ttk.Entry(tab2, textvariable=qty_tab2, width=8)
    qty_entry2.grid(column=3, row=3, sticky='w')
    # Agregar evento Enter para agregar variedad automáticamente
    def on_qty_enter(event):
        add_var_tab2()
    qty_entry2.bind('<Return>', on_qty_enter)

    def add_var_tab2():
        lote = lote_selector.get()
        if not lote:
            messagebox.showerror('Error', 'Selecciona un lote primero')
            return
        name = variety_tab2.get()
        try:
            q = int(qty_tab2.get())
        except ValueError:
            messagebox.showerror('Error', 'Cantidad inválida')
            return
        if agregar_variedad_lote(lote, name, q):
            # Guardar selección actual
            lote_actual = lote_selector.get()
            refresh_lote_selector()
            # Restaurar selección
            lote_selector.set(lote_actual)
            # Forzar actualización visual del listbox
            on_lote_select()
            # Verificar sincronización con GitHub
            success, msg = descargar_csv_github()
            if not success:
                messagebox.showwarning('Advertencia', f'Variedad agregada localmente, pero no se pudo sincronizar con GitHub: {msg}')
            # Pop-up eliminado, la lista se actualiza automáticamente
        else:
            messagebox.showerror('Error', 'No se pudo agregar variedad')

    def remove_sel_tab2():
        lote = lote_selector.get()
        sel = var_listbox_tab2.curselection()
        if not lote or not sel:
            messagebox.showerror('Error', 'Selecciona lote y variedad')
            return
        idx = sel[0]
        # Obtener el nombre de la variedad seleccionada
        nombre_seleccionado = var_listbox_tab2.get(idx).split(' (')[0]
        # Buscar el lote con helper
        lot_idx, lote_obj = find_lote_by_selector(lote)
        if lote_obj is None:
            messagebox.showerror('Error', 'No se pudo encontrar la variedad para eliminar')
            return
        vars_list = lote_obj.get('Variedades', [])
        for real_idx, v in enumerate(vars_list):
            if v['name'] == nombre_seleccionado:
                if eliminar_variedad_lote(lote, real_idx):
                    on_lote_select()
                    return
                else:
                    messagebox.showerror('Error', 'No se pudo eliminar variedad')
                    return
        messagebox.showerror('Error', 'No se pudo encontrar la variedad para eliminar')

    add_btn2 = ttk.Button(tab2, text='Agregar', command=add_var_tab2)
    add_btn2.grid(column=4, row=3, padx=4)
    remove_btn2 = ttk.Button(tab2, text='Eliminar', command=remove_sel_tab2)
    remove_btn2.grid(column=4, row=1, padx=4)

    # ===== Tab 3: Editar Lote =====
    tab3 = ttk.Frame(nb, padding=12)
    nb.add(tab3, text='Editar Lote')

    ttk.Label(tab3, text='Seleccionar lote').grid(column=0, row=0, sticky='w')
    edit_lote_selector = ttk.Combobox(tab3, values=[], state='readonly', width=30)
    edit_lote_selector.grid(column=1, row=0, sticky='w')
    
    def refresh_edit_lotes():
        lotes = leer_csv()
        # Ordenar alfanuméricamente igual que en refresh_lote_selector
        def lote_id_key(lote):
            branch = lote.get('Branch')
            lote_num = lote.get('LoteNum')
            try:
                num = int(lote_num)
            except Exception:
                num = 0
            return (branch, num)
        lotes_sorted = sorted(lotes, key=lote_id_key)
        ids = [f"L{lote.get('LoteNum')}-{lote.get('Branch')} | {lote.get('Location','')} | {lote.get('DateCreated','')}" for lote in lotes_sorted]
        edit_lote_selector['values'] = ids
        if ids:
            edit_lote_selector.set(ids[0])
            on_edit_lote_select()

    refresh_edit_btn = ttk.Button(tab3, text='Refrescar', command=refresh_edit_lotes)
    refresh_edit_btn.grid(column=2, row=0, padx=4)

    ttk.Label(tab3, text='Nueva Etapa').grid(column=0, row=1, sticky='w')
    edit_stage_var = tk.StringVar(value='')
    edit_stage_cb = ttk.Combobox(tab3, textvariable=edit_stage_var, values=STAGES, state='readonly')
    edit_stage_cb.grid(column=1, row=1, sticky='ew')

    ttk.Label(tab3, text='Nueva Ubicación').grid(column=0, row=2, sticky='w')
    edit_location_var = tk.StringVar(value='')
    edit_location_cb = ttk.Combobox(tab3, textvariable=edit_location_var, values=LOCATIONS, state='readonly')
    edit_location_cb.grid(column=1, row=2, sticky='ew')

    # Nueva Semana para corregir (1..22)
    ttk.Label(tab3, text='Nueva Semana').grid(column=0, row=3, sticky='w')
    edit_semana_var = tk.StringVar(value='')
    edit_semana_cb = ttk.Combobox(tab3, textvariable=edit_semana_var, values=[str(i) for i in range(1,23)], state='readonly')
    edit_semana_cb.grid(column=1, row=3, sticky='ew')

    def on_edit_lote_select(event=None):
        sel = edit_lote_selector.get()
        if not sel:
            return
        idx, lote = find_lote_by_selector(sel)
        if lote is None:
            return
        # Leave stage and location empty (we only edit Semana here)
        edit_stage_var.set('')
        edit_location_var.set('')
        edit_semana_var.set(lote.get('Semana',''))

    edit_lote_selector.bind('<<ComboboxSelected>>', on_edit_lote_select)

    def actualizar_lote_gui():
        lote = edit_lote_selector.get()
        nueva_semana = edit_semana_var.get()
        if not lote:
            messagebox.showerror('Error', 'Selecciona un lote')
            return
        # Validar semana (1-22)
        try:
            semana_int = int(nueva_semana)
            if not 1 <= semana_int <= 22:
                raise ValueError
        except Exception:
            messagebox.showerror('Error', 'Semana inválida (1-22)')
            return
        if actualizar_semana_lote(lote, str(semana_int)):
            messagebox.showinfo('OK', f'Semana del lote {lote} actualizada a {semana_int}')
            refresh_edit_lotes()
        else:
            messagebox.showerror('Error', 'No se pudo actualizar la semana del lote')

    update_btn = ttk.Button(tab3, text='Guardar cambios', command=actualizar_lote_gui)
    update_btn.grid(column=0, row=4, columnspan=2, pady=10)

    # ===== Barra de estado =====
    status_frame = ttk.Frame(root)
    status_frame.pack(side='bottom', fill='x', padx=5, pady=3)
    
    status_indicator = tk.Label(status_frame, text='●', font=('TkDefaultFont', 12))
    status_indicator.pack(side='left')
    
    status_label = ttk.Label(status_frame, text='Verificando conexión...')
    status_label.pack(side='left', padx=5)
    
    # Versión de la aplicación
    version_label = ttk.Label(status_frame, text=f'v{VERSION}', foreground='gray')
    version_label.pack(side='right', padx=8)

    sync_btn = ttk.Button(status_frame, text='↑ Sincronizar', command=lambda: sync_to_github())
    sync_btn.pack(side='right', padx=5)
    
    refresh_conn_btn = ttk.Button(status_frame, text='↻ Reconectar', command=lambda: check_connection())
    refresh_conn_btn.pack(side='right', padx=5)
    
    def update_status_local(connected, message):
        if connected:
            status_indicator.config(text='●', fg='green')
            status_label.config(text=f'Conectado - {message}')
        else:
            status_indicator.config(text='●', fg='red')
            status_label.config(text=f'Sin conexión - {message}')

    global update_status
    update_status = update_status_local
    
    def check_connection():
        status_label.config(text='Verificando...')
        root.update()
        success, msg = descargar_csv_github()
        update_status(success, msg)
        if success:
            refresh_lote_selector()
    
    def sync_to_github():
        status_label.config(text='Subiendo cambios...')
        root.update()
        if subir_csv_github():
            update_status(True, 'Sincronizado')
        else:
            update_status(False, 'Error al sincronizar')

    # Initialize
    refresh_lote_selector()
    try:
        refresh_edit_lotes()
    except Exception:
        pass
    
    # Verificar conexión al inicio
    root.after(500, check_connection)

    root.mainloop()


if __name__ == '__main__':
    make_gui()
