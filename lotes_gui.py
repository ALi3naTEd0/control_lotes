import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import requests

ROOT = os.path.dirname(__file__)

# Global for status update callback
update_status = None
LOTES_CSV = os.path.join(ROOT, 'lotes_template.csv')
GITHUB_CONFIG = os.path.join(ROOT, 'github_config.txt')

# Leer configuración de GitHub
GITHUB_TOKEN = ''
GITHUB_REPO = ''
GITHUB_FILE_PATH = 'lotes_template.csv'
GITHUB_BRANCH = 'main'

if os.path.exists(GITHUB_CONFIG):
    try:
        with open(GITHUB_CONFIG, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            if len(lines) >= 4:
                GITHUB_TOKEN = lines[0]
                GITHUB_REPO = lines[1]
                GITHUB_FILE_PATH = lines[2]
                GITHUB_BRANCH = lines[3]
    except Exception:
        pass

BRANCHES = ['FSM', 'SMB', 'RP']
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
STAGES = ['CLONADO','VEG. TEMPRANO','VEG. TARDIO','FLORACIÓN','TRANSICIÓN','SECADO','PT']
LOCATIONS = ['PT','CUARTO 1','CUARTO 2','CUARTO 3','CUARTO 4','VEGETATIVO','ENFERMERÍA','MADRES']


def descargar_csv_github():
    """Descarga el CSV desde GitHub (repo privado)."""
    if not GITHUB_TOKEN:
        return False, 'Sin token configurado'
    
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    params = {'ref': GITHUB_BRANCH}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            with open(LOTES_CSV, 'w', encoding='utf-8') as f:
                f.write(response.text)
            return True, 'Conectado'
        elif response.status_code == 401:
            return False, 'Token inválido'
        elif response.status_code == 404:
            return False, 'Repo/archivo no encontrado'
        else:
            return False, f'Error {response.status_code}'
    except requests.exceptions.ConnectionError:
        return False, 'Sin conexión a internet'
    except requests.exceptions.Timeout:
        return False, 'Timeout de conexión'
    except Exception as e:
        return False, f'Error: {str(e)[:20]}'


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
                for i in range(1, 11):
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
                row['Variedades'] = variedades
                lotes.append(row)
    except Exception as e:
        messagebox.showerror('Error', f'No se pudo leer CSV: {e}')
    return lotes


def guardar_csv(lotes):
    """Guarda lotes en el CSV (con LoteNum almacenado)."""
    try:
        with open(LOTES_CSV, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['ID','Branch','LoteNum','Stage','Location','DateCreated','Notes']
            for i in range(1, 11):
                fieldnames.append(f'Variedad_{i}')
                fieldnames.append(f'Cantidad_{i}')
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            writer.writeheader()
            for lote in lotes:
                row = {k: lote.get(k, '') for k in fieldnames}
                # Escribir variedades/cantidades
                variedades = lote.get('Variedades', [])
                for i in range(1, 11):
                    if i <= len(variedades):
                        row[f'Variedad_{i}'] = variedades[i-1]['name']
                        row[f'Cantidad_{i}'] = variedades[i-1]['count']
                    else:
                        row[f'Variedad_{i}'] = ''
                        row[f'Cantidad_{i}'] = ''
                writer.writerow(row)
    except Exception as e:
        messagebox.showerror('Error', f'No se pudo guardar CSV: {e}')


def proximo_lote_id(branch):
    """Calcula el próximo LoteID para la sucursal."""
    lotes = leer_csv()
    lotes_rama = [l for l in lotes if l.get('Branch') == branch]
    n = len(lotes_rama) + 1
    return f"L{n}-{branch}"


def crear_lote_gui(branch_var, lote_num, stage_var, location_var, notes_var, date_var):
    branch = branch_var.get()
    lote_num_sel = lote_num.get()
    stage = stage_var.get()
    location = location_var.get()
    notes = notes_var.get()
    date = date_var.get() or datetime.now().strftime('%Y-%m-%d')

    if branch not in BRANCHES:
        messagebox.showerror('Error', 'Sucursal inválida')
        return
    if stage not in STAGES:
        messagebox.showerror('Error', 'Etapa inválida')
        return
    if location not in LOCATIONS:
        messagebox.showerror('Error', 'Ubicación inválida')
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
        # Recalcular total de lote
        total = 0
        vars_formatted = ''
        vars_str = lote.get('Varieties', '').strip()
        if vars_str:
            vars_list = []
            for var_pair in vars_str.split(';'):
                var_pair = var_pair.strip()
                if var_pair:
                    # Parse "Name(count)" y formatear con espacio
                    if '(' in var_pair and ')' in var_pair:
                        v_name = var_pair[:var_pair.rfind('(')].strip()
                        try:
                            qty = int(var_pair[var_pair.rfind('(')+1:var_pair.rfind(')')])
                            total += qty
                            vars_list.append(f"{v_name} ({qty})")
                        except:
                            vars_list.append(var_pair)
                    else:
                        vars_list.append(var_pair)
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


def actualizar_etapa_ubicacion(lote_id, new_stage, new_location):
    """Actualiza la etapa y ubicación de un lote."""
    lotes = leer_csv()
    for lote in lotes:
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        calc_id = f"L{lote_num}-{branch}"
        if calc_id == lote_id:
            lote['Stage'] = new_stage
            lote['Location'] = new_location
            guardar_csv(lotes)
            return True
    return False


def agregar_variedad_lote(lote_id, name, qty):
    """Agrega o suma cantidad de una variedad a un lote."""
    lotes = leer_csv()
    for idx, lote in enumerate(lotes):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        calc_id = f"L{lote_num}-{branch}"
        if calc_id == lote_id:
            vars_list = lote.get('Variedades', [])
            found = False
            for v in vars_list:
                if v['name'] == name:
                    v['count'] += qty
                    found = True
                    break
            if not found:
                vars_list.append({'name': name, 'count': qty})
            lote['Variedades'] = vars_list
            guardar_csv(lotes)
            subir_csv_github()
            return True
    return False


def eliminar_variedad_lote(lote_id, idx):
    """Elimina una variedad por índice."""
    lotes = leer_csv()
    for lot_idx, lote in enumerate(lotes):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        calc_id = f"L{lote_num}-{branch}"
        if calc_id == lote_id:
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
    ids = [f"L{lote.get('LoteNum')}-{lote.get('Branch')}" for lote in lotes_sorted]
    lote_selector['values'] = ids
    if ids:
        lote_selector.set(ids[0])
        on_lote_select()


def on_lote_select(event=None):
    """Muestra variedades del lote seleccionado."""
    sel = lote_selector.get()
    var_listbox_tab2.delete(0, 'end')
    lotes = leer_csv()
    for idx, lote in enumerate(lotes):
        branch = lote.get('Branch')
        lote_num = lote.get('LoteNum')
        calc_id = f"L{lote_num}-{branch}"
        if calc_id == sel:
            vars_str = lote.get('Varieties', '').strip()
            total = 0
            vars_list = []
            if vars_str:
                for var_pair in vars_str.split(';'):
                    var_pair = var_pair.strip()
                    if var_pair:
                        vars_list.append(var_pair)
                        # Calcular total
                        if '(' in var_pair and ')' in var_pair:
                            try:
                                qty_str = var_pair[var_pair.rfind('(')+1:var_pair.rfind(')')]
                                total += int(qty_str)
                            except:
                                pass
            # Ordenar alfabéticamente y mostrar
            vars_list.sort()
            for var_pair in vars_list:
                var_listbox_tab2.insert('end', var_pair)
            # Actualizar label de total
            total_label_tab2.config(text=f'TOTAL: {total}')
            break


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
            if calc_id != lote_id_filter:
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
    branch_var = tk.StringVar(value=BRANCHES[0])
    branch_cb = ttk.Combobox(tab1, textvariable=branch_var, values=BRANCHES, state='readonly')
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

    create_btn = ttk.Button(btn_frame, text='Crear lote', command=lambda: crear_lote_gui(branch_var, lote_num, stage_var, location_var, notes_var, date_var))
    create_btn.grid(column=0, row=0, padx=4)

    list_btn = ttk.Button(btn_frame, text='Listar todos', command=listar_lotes_gui)
    list_btn.grid(column=1, row=0, padx=4)

    # Tab 2: Agregar variedades a lotes existentes
    tab2 = ttk.Frame(nb, padding=12)
    nb.add(tab2, text='Agregar variedades')

    ttk.Label(tab2, text='Seleccionar lote').grid(column=0, row=0, sticky='w')
    global lote_selector, var_listbox_tab2
    lote_selector = ttk.Combobox(tab2, values=[], state='readonly', width=30)
    lote_selector.grid(column=1, row=0, sticky='w')
    lote_selector.bind('<<ComboboxSelected>>', on_lote_select)

    refresh_btn = ttk.Button(tab2, text='Refrescar lista', command=refresh_lote_selector)
    refresh_btn.grid(column=2, row=0, padx=4)

    # Frame for listbox and scrollbar
    var_listbox_frame = ttk.Frame(tab2)
    var_listbox_frame.grid(column=0, row=1, columnspan=3, sticky='ew', pady=6)

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
            on_lote_select()
            messagebox.showinfo('OK', f'Variedad agregada: {name}({q})')
        else:
            messagebox.showerror('Error', 'No se pudo agregar variedad')

    def remove_sel_tab2():
        lote = lote_selector.get()
        sel = var_listbox_tab2.curselection()
        if not lote or not sel:
            messagebox.showerror('Error', 'Selecciona lote y variedad')
            return
        idx = sel[0]
        if eliminar_variedad_lote(lote, idx):
            on_lote_select()
            messagebox.showinfo('OK', 'Variedad eliminada')
        else:
            messagebox.showerror('Error', 'No se pudo eliminar variedad')

    add_btn2 = ttk.Button(tab2, text='Agregar', command=add_var_tab2)
    add_btn2.grid(column=4, row=3, padx=4)
    remove_btn2 = ttk.Button(tab2, text='Eliminar', command=remove_sel_tab2)
    remove_btn2.grid(column=4, row=1, padx=4)

    # ===== Tab 3: Filtros =====
    tab3 = ttk.Frame(nb, padding=12)
    nb.add(tab3, text='Filtros')

    ttk.Label(tab3, text='Filtrar por sucursal').grid(column=0, row=0, sticky='w')
    branch_filter = tk.StringVar(value='')
    branch_filter_cb = ttk.Combobox(tab3, textvariable=branch_filter, values=[''] + BRANCHES, state='readonly', width=15)
    branch_filter_cb.grid(column=1, row=0, sticky='w', padx=4)

    ttk.Label(tab3, text='Filtrar por etapa').grid(column=0, row=1, sticky='w')
    stage_filter = tk.StringVar(value='')
    stage_filter_cb = ttk.Combobox(tab3, textvariable=stage_filter, values=[''] + STAGES, state='readonly', width=15)
    stage_filter_cb.grid(column=1, row=1, sticky='w', padx=4)

    ttk.Label(tab3, text='Filtrar por ubicación').grid(column=0, row=2, sticky='w')
    location_filter = tk.StringVar(value='')
    location_filter_cb = ttk.Combobox(tab3, textvariable=location_filter, values=[''] + LOCATIONS, state='readonly', width=15)
    location_filter_cb.grid(column=1, row=2, sticky='w', padx=4)

    ttk.Label(tab3, text='Filtrar por lote').grid(column=0, row=3, sticky='w')
    lote_filter = tk.StringVar(value='')
    lote_filter_cb = ttk.Combobox(tab3, textvariable=lote_filter, values=[], state='readonly', width=15)
    lote_filter_cb.grid(column=1, row=3, sticky='w', padx=4)

    ttk.Label(tab3, text='Filtrar por variedad').grid(column=0, row=4, sticky='w')
    variety_filter = tk.StringVar(value='')
    variety_filter_cb = ttk.Combobox(tab3, textvariable=variety_filter, values=[''] + sorted(VARIETIES), state='readonly', width=20)
    variety_filter_cb.grid(column=1, row=4, sticky='w', padx=4)

    def refresh_lote_filter():
        lotes = leer_csv()
        ids = [''] + [f"L{lote.get('LoteNum')}-{lote.get('Branch')}" for lote in lotes]
        lote_filter_cb['values'] = ids

    refresh_filter_btn = ttk.Button(tab3, text='Refrescar', command=refresh_lote_filter)
    refresh_filter_btn.grid(column=2, row=3, padx=4)

    def aplicar_filtros():
        b = branch_filter.get() if branch_filter.get() else None
        s = stage_filter.get() if stage_filter.get() else None
        l = location_filter.get() if location_filter.get() else None
        lote_id = lote_filter.get() if lote_filter.get() else None
        v = variety_filter.get() if variety_filter.get() else None
        filtrar_lotes(b, s, l, lote_id, v)

    filter_btn = ttk.Button(tab3, text='Aplicar filtros', command=aplicar_filtros)
    filter_btn.grid(column=0, row=5, columnspan=2, pady=10)

    # ===== Tab 4: Editar Lote =====
    tab4 = ttk.Frame(nb, padding=12)
    nb.add(tab4, text='Editar Lote')

    ttk.Label(tab4, text='Seleccionar lote').grid(column=0, row=0, sticky='w')
    edit_lote_selector = ttk.Combobox(tab4, values=[], state='readonly', width=30)
    edit_lote_selector.grid(column=1, row=0, sticky='w')
    
    def refresh_edit_lotes():
        lotes = leer_csv()
        ids = [f"L{lote.get('LoteNum')}-{lote.get('Branch')}" for lote in lotes]
        edit_lote_selector['values'] = ids

    refresh_edit_btn = ttk.Button(tab4, text='Refrescar', command=refresh_edit_lotes)
    refresh_edit_btn.grid(column=2, row=0, padx=4)

    ttk.Label(tab4, text='Nueva Etapa').grid(column=0, row=1, sticky='w')
    edit_stage_var = tk.StringVar(value=STAGES[0])
    edit_stage_cb = ttk.Combobox(tab4, textvariable=edit_stage_var, values=STAGES, state='readonly')
    edit_stage_cb.grid(column=1, row=1, sticky='ew')

    ttk.Label(tab4, text='Nueva Ubicación').grid(column=0, row=2, sticky='w')
    edit_location_var = tk.StringVar(value=LOCATIONS[0])
    edit_location_cb = ttk.Combobox(tab4, textvariable=edit_location_var, values=LOCATIONS, state='readonly')
    edit_location_cb.grid(column=1, row=2, sticky='ew')

    def actualizar_lote_gui():
        lote = edit_lote_selector.get()
        stage = edit_stage_var.get()
        location = edit_location_var.get()
        
        if not lote:
            messagebox.showerror('Error', 'Selecciona un lote')
            return
        
        if actualizar_etapa_ubicacion(lote, stage, location):
            messagebox.showinfo('OK', f'Lote {lote} actualizado')
            refresh_edit_lotes()
        else:
            messagebox.showerror('Error', 'No se pudo actualizar el lote')

    update_btn = ttk.Button(tab4, text='Guardar cambios', command=actualizar_lote_gui)
    update_btn.grid(column=0, row=3, columnspan=2, pady=10)

    # ===== Tab 5: Gráficos =====
    tab5 = ttk.Frame(nb, padding=12)
    nb.add(tab5, text='Gráficos')

    ttk.Label(tab5, text='Visualizaciones de datos').grid(column=0, row=0, columnspan=4, sticky='w')

    radar_btn = ttk.Button(tab5, text='Radar: Lotes por Sucursal/Etapa', command=grafico_distribucion_por_sucursal)
    radar_btn.grid(column=0, row=1, padx=4, pady=4, sticky='ew')

    pie_btn = ttk.Button(tab5, text='Pie: Distribución por Etapa', command=grafico_distribucion_etapas)
    pie_btn.grid(column=1, row=1, padx=4, pady=4, sticky='ew')

    bars_btn = ttk.Button(tab5, text='Barras: Lotes por Ubicación', command=grafico_distribucion_ubicaciones)
    bars_btn.grid(column=2, row=1, padx=4, pady=4, sticky='ew')

    # ===== Barra de estado =====
    status_frame = ttk.Frame(root)
    status_frame.pack(side='bottom', fill='x', padx=5, pady=3)
    
    status_indicator = tk.Label(status_frame, text='●', font=('TkDefaultFont', 12))
    status_indicator.pack(side='left')
    
    status_label = ttk.Label(status_frame, text='Verificando conexión...')
    status_label.pack(side='left', padx=5)
    
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
    
    # Verificar conexión al inicio
    root.after(500, check_connection)

    root.mainloop()


if __name__ == '__main__':
    make_gui()
