"""
Control de Lotes - Versión Flet (Android/Desktop/Web)
Adaptado de lotes_gui.py (Tkinter) para funcionar en múltiples plataformas.
"""

import flet as ft
import csv
import os
import sys
import base64
import json
from datetime import datetime
import requests
import shutil
import glob

# ========== CONFIGURACIÓN ==========

if getattr(sys, 'frozen', False):
    BASE_PATH = os.path.dirname(sys.executable)
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_PATH, "github_config.txt")
LOTES_CSV = os.path.join(BASE_PATH, "lotes_template.csv")
REGISTROS_DIR = os.path.join(BASE_PATH, "registros")

VERSION = '1.0.5'
BRANCH = ['FSM', 'SMB', 'RP']
STAGES = ['CLONADO', 'VEG. TEMPRANO', 'VEG. TARDIO', 'FLORACIÓN', 'TRANSICIÓN', 'SECADO', 'PT']
LOCATIONS = ['PT', 'CUARTO 1', 'CUARTO 2', 'CUARTO 3', 'CUARTO 4', 'VEGETATIVO', 'ENFERMERÍA', 'MADRES']
VARIETIES = [
    'Ak-47', 'Apple Fritter', 'Banana Latte', 'Blackberry Honey', 'Desconocida',
    'Gran Jefa', 'HG23 (Michael Jordan)', 'Kandy Kush', 'King Kush Breath',
    'Kosher Kush', 'Mozzerella', 'Orangel', 'Purple Diesel', 'ReCon',
    'Red Red Wine', 'Runtz', 'Sugar Cane', 'Wedding Cake', 'Zallah Bread',
]

# Variables globales
GITHUB_REPO = ""
GITHUB_TOKEN = ""
GITHUB_FILE_PATH = "lotes_template.csv"
GITHUB_BRANCH = "main"


def get_config_path():
    """Obtiene la ruta del archivo de configuración según la plataforma."""
    # En Android, usar el directorio de la app
    if hasattr(sys, 'getandroidapilevel'):
        config_dir = os.path.join(os.environ.get('HOME', '/data/data/com.example.app'), '.config')
    else:
        # Desktop: usar directorio del proyecto o home
        config_dir = BASE_PATH
    
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "lotes_config.json")


def cargar_config_desde_storage(page=None):
    """Carga la configuración desde archivo JSON."""
    global GITHUB_REPO, GITHUB_TOKEN
    
    config_path = get_config_path()
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            repo = config.get("github_repo", "")
            token = config.get("github_token", "")
            
            if repo and token and "/" in repo:
                GITHUB_REPO = repo
                GITHUB_TOKEN = token
                return True, "Config cargada"
        except:
            pass
    
    return False, "Configura GitHub en ⚙️"


def guardar_config_en_storage(page, repo, token):
    """Guarda la configuración en archivo JSON."""
    global GITHUB_REPO, GITHUB_TOKEN
    
    config_path = get_config_path()
    config = {
        "github_repo": repo,
        "github_token": token
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    GITHUB_REPO = repo
    GITHUB_TOKEN = token


def descargar_csv_github():
    """Descarga el CSV desde GitHub."""
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
            contenido = base64.b64decode(data['content']).decode('utf-8')
            with open(LOTES_CSV, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return True, 'Conectado'
        elif response.status_code == 401:
            return False, 'Token inválido'
        elif response.status_code == 404:
            return False, 'Repo o archivo no encontrado'
        else:
            return False, f'Error HTTP {response.status_code}'
    except requests.exceptions.ConnectionError:
        return False, 'Sin conexión a internet'
    except requests.exceptions.Timeout:
        return False, 'Timeout'
    except Exception as e:
        return False, f'Error: {str(e)[:50]}'


def subir_csv_github():
    """Sube el CSV a GitHub."""
    if not GITHUB_TOKEN:
        return False, 'Sin token'
    
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(url, headers=headers, params={'ref': GITHUB_BRANCH}, timeout=10)
        sha = response.json().get('sha', '') if response.status_code == 200 else ''
        
        with open(LOTES_CSV, 'r', encoding='utf-8') as f:
            content = f.read()
        
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            'message': f'Actualización lotes - {datetime.now().strftime("%Y-%m-%d %H:%M")}',
            'content': encoded_content,
            'branch': GITHUB_BRANCH
        }
        if sha:
            data['sha'] = sha
        
        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code in [200, 201]:
            return True, 'Sincronizado'
        else:
            return False, f'Error {response.status_code}'
    except Exception as e:
        return False, f'Error: {str(e)[:50]}'


def leer_csv():
    """Lee lotes del CSV."""
    if not os.path.exists(LOTES_CSV):
        return []
    try:
        with open(LOTES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            lotes_final = []
            for row in reader:
                variedades = []
                for i in range(1, 21):
                    v = row.get(f'Variedad_{i}', '').strip()
                    c = row.get(f'Cantidad_{i}', '').strip()
                    if v:
                        try:
                            c = int(c)
                        except:
                            c = 0
                        variedades.append({'name': v, 'count': c})
                row['Variedades'] = variedades
                lotes_final.append(row)
            return lotes_final
    except Exception:
        return []


def guardar_csv(lotes):
    """Guarda lotes en el CSV."""
    try:
        with open(LOTES_CSV, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['ID', 'Branch', 'LoteNum', 'Stage', 'Location', 'Semana', 
                         'DateCreated', 'ÚltimaActualización', 'Notes']
            for i in range(1, 21):
                fieldnames.extend([f'Variedad_{i}', f'Cantidad_{i}'])
            
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            writer.writeheader()
            
            for row in lotes:
                if 'ÚltimaActualización' not in row:
                    row['ÚltimaActualización'] = ''
                if 'Variedades' in row:
                    variedades = row['Variedades']
                    for i in range(1, 21):
                        row[f'Variedad_{i}'] = ''
                        row[f'Cantidad_{i}'] = ''
                    for i, v in enumerate(variedades[:20], start=1):
                        row[f'Variedad_{i}'] = v.get('name', '')
                        row[f'Cantidad_{i}'] = str(v.get('count', 0))
                    del row['Variedades']
                writer.writerow(row)
        return True
    except Exception:
        return False


def ensure_registros_dir():
    os.makedirs(REGISTROS_DIR, exist_ok=True)


def crear_backup():
    if not os.path.exists(LOTES_CSV):
        return None
    ensure_registros_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(REGISTROS_DIR, f"lotes_template_{timestamp}.csv")
    try:
        shutil.copy2(LOTES_CSV, dest)
        return dest
    except Exception:
        return None


def find_lote_by_id(lote_id, lotes=None):
    """Busca un lote por su ID, considerando ubicación si está presente."""
    if lotes is None:
        lotes = leer_csv()
    
    sel = lote_id.strip()
    location_filter = None
    
    # Extraer ubicación si está en formato "L1-FSM (CUARTO 1)"
    if '(' in sel and sel.endswith(')'):
        parts = sel.rsplit('(', 1)
        sel = parts[0].strip()
        location_filter = parts[1].rstrip(')').strip()
    
    if '|' in sel:
        sel = sel.split('|', 1)[0].strip()
    
    for idx, lote in enumerate(lotes):
        calc_id = f"L{lote.get('LoteNum')}-{lote.get('Branch')}"
        if sel == calc_id or sel == lote.get('ID'):
            # Si hay filtro de ubicación, verificar que coincida
            if location_filter:
                if lote.get('Location', '') == location_filter:
                    return idx, lote
            else:
                return idx, lote
    return None, None


def get_lote_ids_sorted():
    """Retorna lista de IDs de lotes ordenados."""
    lotes = leer_csv()
    
    def lote_key(lote):
        try:
            return (lote.get('Branch', ''), int(lote.get('LoteNum', 0)))
        except:
            return (lote.get('Branch', ''), 0)
    
    lotes_sorted = sorted(lotes, key=lote_key)
    
    counts = {}
    for lote in lotes_sorted:
        cid = f"L{lote.get('LoteNum')}-{lote.get('Branch')}"
        counts[cid] = counts.get(cid, 0) + 1
    
    ids = []
    for lote in lotes_sorted:
        cid = f"L{lote.get('LoteNum')}-{lote.get('Branch')}"
        if counts.get(cid, 0) > 1:
            label = f"{cid} ({lote.get('Location', '')})"
        else:
            label = cid
        ids.append(label)
    return ids


# ========== APLICACIÓN FLET ==========

def main(page: ft.Page):
    page.title = "Control de Lotes"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    
    # Cargar configuración desde client_storage
    config_ok, config_msg = cargar_config_desde_storage(page)
    
    # Estado - usando controles directos en lugar de Ref
    connection_status = ft.Ref[ft.Container]()
    status_text = ft.Ref[ft.Text]()
    
    # Controles directos para variedades (más confiable que Ref)
    lote_info_label = ft.Text(value="Selecciona un lote", size=12, color=ft.Colors.GREY_700)
    varieties_listview = ft.ListView(
        spacing=0, 
        height=350, 
        padding=0,
        # Mostrar barra de scroll siempre visible
    )
    total_label = ft.Text(value="TOTAL: 0 plantas", size=14, weight=ft.FontWeight.BOLD)
    
    # Variable para guardar el valor seleccionado
    selected_lote = {"value": None}
    
    def update_status(connected: bool, message: str):
        if connection_status.current:
            connection_status.current.bgcolor = ft.Colors.GREEN if connected else ft.Colors.RED
        if status_text.current:
            status_text.current.value = message
        page.update()
    
    def refresh_lotes_dropdown():
        # Ahora usa los radios en lugar del dropdown
        refresh_lotes_list_radios()
    
    def check_connection(e=None):
        update_status(False, "Verificando...")
        success, msg = descargar_csv_github()
        update_status(success, msg)
        if success:
            refresh_lotes_dropdown()
    
    def sync_to_github(e):
        update_status(False, "Sincronizando...")
        success, msg = subir_csv_github()
        update_status(success, msg)
    
    def create_lote(branch, lote_num, stage, location, semana, notes):
        lotes = leer_csv()
        lotes_rama = [l for l in lotes if l.get('Branch') == branch]
        
        if lote_num == 'AUTO':
            try:
                existing = [int(l.get('LoteNum')) for l in lotes_rama if l.get('LoteNum', '').isdigit()]
                n = max(existing) + 1 if existing else 1
            except:
                n = len(lotes_rama) + 1
        else:
            n = int(lote_num.lstrip('L'))
        
        entry = {
            'ID': f"L{n}-{branch}",
            'Branch': branch,
            'LoteNum': str(n),
            'Stage': stage,
            'Location': location,
            'Semana': str(semana),
            'DateCreated': datetime.now().strftime('%Y-%m-%d'),
            'Notes': notes or '',
            'Variedades': []
        }
        
        lotes.append(entry)
        guardar_csv(lotes)
        subir_csv_github()
        return f"L{n}-{branch}"
    
    def add_variety_to_lote(lote_id, variety_name, qty):
        lotes = leer_csv()
        idx, lote = find_lote_by_id(lote_id, lotes)
        
        if lote is None:
            return False
        
        vars_list = lote.get('Variedades', [])
        found = False
        for v in vars_list:
            if v['name'] == variety_name:
                v['count'] += qty
                found = True
                break
        
        if not found:
            if len(vars_list) >= 20:
                return False
            vars_list.append({'name': variety_name, 'count': qty})
        
        lote['Variedades'] = vars_list
        guardar_csv(lotes)
        subir_csv_github()
        return True
    
    def remove_variety_from_lote(lote_id, variety_name):
        lotes = leer_csv()
        idx, lote = find_lote_by_id(lote_id, lotes)
        
        if lote is None:
            return False
        
        vars_list = lote.get('Variedades', [])
        for i, v in enumerate(vars_list):
            if v['name'] == variety_name:
                del vars_list[i]
                lote['Variedades'] = vars_list
                guardar_csv(lotes)
                subir_csv_github()
                return True
        return False
    
    # ========== UI COMPONENTS ==========
    
    # Barra de estado
    status_bar = ft.Container(
        content=ft.Row([
            ft.Container(
                ref=connection_status,
                width=12,
                height=12,
                border_radius=6,
                bgcolor=ft.Colors.GREY,
            ),
            ft.Text(ref=status_text, value="Iniciando...", size=12),
            ft.Container(expand=True),
            ft.TextButton("↻ Reconectar", on_click=check_connection),
            ft.TextButton("↑ Sincronizar", on_click=sync_to_github),
            ft.Text(f"v{VERSION}", size=10, color=ft.Colors.GREY),
        ]),
        padding=10,
        bgcolor=ft.Colors.GREY_100,
        border_radius=8,
    )
    
    # ========== TAB 1: CREAR LOTE ==========
    branch_dd = ft.Dropdown(
        label="Sucursal",
        options=[ft.dropdown.Option(b) for b in BRANCH],
        value=BRANCH[0],
        width=150,
    )
    
    lote_num_dd = ft.Dropdown(
        label="Nº Lote",
        options=[ft.dropdown.Option("AUTO")] + [ft.dropdown.Option(f"L{i}") for i in range(1, 33)],
        value="AUTO",
        width=100,
    )
    
    stage_dd = ft.Dropdown(
        label="Etapa",
        options=[ft.dropdown.Option(s) for s in STAGES],
        value=STAGES[0],
        width=180,
    )
    
    location_dd = ft.Dropdown(
        label="Ubicación",
        options=[ft.dropdown.Option(l) for l in LOCATIONS],
        value=LOCATIONS[0],
        width=150,
    )
    
    semana_dd = ft.Dropdown(
        label="Semana",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 23)],
        value="1",
        width=100,
    )
    
    notes_field = ft.TextField(label="Notas", width=300)
    
    def on_create_click(e):
        lote_id = create_lote(
            branch_dd.value,
            lote_num_dd.value,
            stage_dd.value,
            location_dd.value,
            semana_dd.value,
            notes_field.value
        )
        page.snack_bar = ft.SnackBar(ft.Text(f"Lote creado: {lote_id}"))
        page.snack_bar.open = True
        refresh_lotes_dropdown()
        page.update()
    
    tab_crear = ft.Column([
        ft.Text("Crear nuevo lote", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([branch_dd, lote_num_dd], wrap=True),
        ft.Row([stage_dd, location_dd], wrap=True),
        ft.Row([semana_dd], wrap=True),
        notes_field,
        ft.FilledButton(
            "Crear Lote",
            icon=ft.Icons.ADD,
            on_click=on_create_click,
            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
        ),
    ], spacing=15, scroll=ft.ScrollMode.AUTO)
    
    # ========== TAB 2: AGREGAR VARIEDADES ==========
    variety_dd = ft.Dropdown(
        label="Variedad",
        options=[ft.dropdown.Option(v) for v in sorted(VARIETIES)],
        value=sorted(VARIETIES)[0],
        width=200,
    )
    
    qty_field = ft.TextField(label="Cantidad", value="1", width=100, keyboard_type=ft.KeyboardType.NUMBER)
    
    # Variable para tracking (se define antes de usarse)
    current_lote_id = {"value": None}
    
    def on_add_variety(e):
        if not current_lote_id["value"]:
            page.snack_bar = ft.SnackBar(ft.Text("Selecciona un lote primero"))
            page.snack_bar.open = True
            page.update()
            return
        
        try:
            qty = int(qty_field.value)
        except:
            page.snack_bar = ft.SnackBar(ft.Text("Cantidad inválida"))
            page.snack_bar.open = True
            page.update()
            return
        
        if add_variety_to_lote(current_lote_id["value"], variety_dd.value, qty):
            page.snack_bar = ft.SnackBar(ft.Text(f"Agregado: {variety_dd.value} x{qty}"))
            load_lote_data(current_lote_id["value"])
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Error al agregar"))
        page.snack_bar.open = True
        page.update()
    
    # Usar PopupMenuButton que SÍ tiene on_click funcional
    lote_selector_text = ft.Text("Seleccionar lote...", size=14)
    lotes_popup_menu = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.FOLDER_OPEN, size=20),
                lote_selector_text,
                ft.Icon(ft.Icons.ARROW_DROP_DOWN),
            ], spacing=8),
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
        ),
        items=[],
    )
    
    def on_lote_selected(lote_id):
        """Cuando se selecciona un lote del popup menu."""
        current_lote_id["value"] = lote_id
        lote_selector_text.value = lote_id
        load_lote_data(lote_id)
        page.update()
    
    def refresh_lotes_list_radios():
        """Actualiza la lista de lotes en el popup menu."""
        ids = get_lote_ids_sorted()
        lotes_popup_menu.items.clear()
        for lote_id in ids:
            item = ft.PopupMenuItem(
                content=ft.Text(lote_id),
                on_click=lambda e, lid=lote_id: on_lote_selected(lid),
            )
            lotes_popup_menu.items.append(item)
        if ids:
            current_lote_id["value"] = ids[0]
            lote_selector_text.value = ids[0]
            load_lote_data(ids[0])
        page.update()
    
    def eliminar_variedad(variedad_name):
        """Elimina una variedad del lote actual."""
        if not current_lote_id["value"]:
            return
        
        lotes = leer_csv()
        idx, lote = find_lote_by_id(current_lote_id["value"], lotes)
        
        if lote is None:
            return
        
        vars_list = lote.get('Variedades', [])
        for i, v in enumerate(vars_list):
            if v['name'] == variedad_name:
                del vars_list[i]
                lote['Variedades'] = vars_list
                guardar_csv(lotes)
                subir_csv_github()
                page.snack_bar = ft.SnackBar(ft.Text(f"Eliminado: {variedad_name}"))
                page.snack_bar.open = True
                load_lote_data(current_lote_id["value"])
                return
    
    def confirmar_eliminar(variedad_name):
        """Muestra diálogo de confirmación antes de eliminar."""
        def cerrar_dialogo(e):
            dialogo.open = False
            page.update()
        
        def confirmar(e):
            dialogo.open = False
            page.update()
            eliminar_variedad(variedad_name)
        
        dialogo = ft.AlertDialog(
            modal=True,
            title=ft.Text("¿Eliminar variedad?"),
            content=ft.Text(f"¿Seguro que deseas eliminar '{variedad_name}' del lote?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                ft.TextButton("Eliminar", on_click=confirmar, style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()
    
    def build_variety_tile(v):
        """Construye un tile de variedad con botón eliminar."""
        return ft.Container(
            content=ft.Row([
                ft.Text("🌿", size=11),
                ft.Text(v['name'], size=12, expand=True),
                ft.Text(str(v['count']), size=12, weight=ft.FontWeight.BOLD, width=35, text_align=ft.TextAlign.RIGHT),
                ft.GestureDetector(
                    content=ft.Container(
                        content=ft.Text("✕", size=16, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding(left=8, right=4, top=0, bottom=0),
                    ),
                    data=v['name'],
                    on_tap=lambda e: confirmar_eliminar(e.control.data),
                ),
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(left=8, right=4, top=4, bottom=4),
            border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.GREY_200)),
        )
    
    def load_lote_data(sel):
        """Carga los datos de un lote específico."""
        if not sel:
            return
        
        current_lote_id["value"] = sel
        
        # Siempre leer datos frescos del CSV
        lotes_data = leer_csv()
        idx, lote = find_lote_by_id(sel, lotes_data)
        
        if lote is None:
            lote_info_label.value = "Lote no encontrado"
            varieties_listview.controls.clear()
            total_label.value = "TOTAL: 0 plantas"
            page.update()
            return
        
        # Actualizar info
        lote_info_label.value = f"🌱 {lote.get('Stage', '')} | 📍 {lote.get('Location', '')} | 📅 Sem. {lote.get('Semana', '')}"
        
        # Actualizar lista de variedades
        variedades = lote.get('Variedades', [])
        total = sum(v['count'] for v in variedades)
        
        varieties_listview.controls.clear()
        if not variedades:
            varieties_listview.controls.append(
                ft.Text("Sin variedades", color=ft.Colors.GREY_500, italic=True)
            )
        else:
            for v in sorted(variedades, key=lambda x: x['name']):
                varieties_listview.controls.append(build_variety_tile(v))
        
        total_label.value = f"🌿 TOTAL: {total} plantas"
        page.update()

    tab_variedades = ft.Column([
        ft.Text("Agregar variedades", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Text("Selecciona un lote:", size=12),
        ft.Row([
            lotes_popup_menu,
            ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: refresh_lotes_list_radios(), tooltip="Refrescar lista"),
        ]),
        lote_info_label,
        ft.Container(
            content=varieties_listview,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=5,
        ),
        total_label,
        ft.Divider(),
        ft.Row([variety_dd, qty_field], wrap=True),
        ft.FilledButton(
            "Agregar variedad",
            icon=ft.Icons.ADD_CIRCLE,
            on_click=on_add_variety,
            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
        ),
    ], spacing=10, scroll=ft.ScrollMode.AUTO)
    
    # ========== TAB 3: GRÁFICOS ==========
    
    def build_stage_chart():
        """Construye visualización de distribución por etapa usando barras."""
        lotes = leer_csv()
        por_etapa = {}
        
        for lote in lotes:
            stage = lote.get('Stage', 'Sin etapa')
            por_etapa[stage] = por_etapa.get(stage, 0) + 1
        
        if not por_etapa:
            return ft.Text("No hay datos para mostrar")
        
        total = sum(por_etapa.values())
        colors = [
            ft.Colors.GREEN_400, ft.Colors.BLUE_400, ft.Colors.PURPLE_400,
            ft.Colors.ORANGE_400, ft.Colors.RED_400, ft.Colors.TEAL_400, ft.Colors.PINK_400
        ]
        
        # Usar barras de progreso visuales en lugar de PieChart
        items = []
        max_count = max(por_etapa.values())
        
        for i, (stage, count) in enumerate(sorted(por_etapa.items(), key=lambda x: -x[1])):
            pct = (count / total) * 100
            bar_width = (count / max_count)
            
            items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(stage, size=12, weight=ft.FontWeight.BOLD, width=120),
                            ft.Container(
                                width=150 * bar_width,
                                height=20,
                                bgcolor=colors[i % len(colors)],
                                border_radius=4,
                            ),
                            ft.Text(f" {count} ({pct:.0f}%)", size=12),
                        ], spacing=10),
                    ]),
                    padding=5,
                )
            )
        
        items.append(ft.Divider())
        items.append(ft.Text(f"Total: {total} lotes", weight=ft.FontWeight.BOLD))
        
        return ft.Column(items, spacing=5)
    
    def build_location_chart():
        """Construye visualización por ubicación."""
        lotes = leer_csv()
        por_ubicacion = {}
        
        for lote in lotes:
            loc = lote.get('Location', 'Sin ubicación')
            por_ubicacion[loc] = por_ubicacion.get(loc, 0) + 1
        
        if not por_ubicacion:
            return ft.Text("No hay datos para mostrar")
        
        max_val = max(por_ubicacion.values())
        total = sum(por_ubicacion.values())
        
        items = []
        for loc, count in sorted(por_ubicacion.items(), key=lambda x: -x[1]):
            bar_width = (count / max_val)
            items.append(
                ft.Row([
                    ft.Text(loc, size=11, width=100),
                    ft.Container(
                        width=180 * bar_width,
                        height=18,
                        bgcolor=ft.Colors.BLUE_400,
                        border_radius=4,
                    ),
                    ft.Text(f" {count}", size=11, weight=ft.FontWeight.BOLD),
                ], spacing=8)
            )
        
        items.append(ft.Divider())
        items.append(ft.Text(f"Total: {total} lotes", weight=ft.FontWeight.BOLD))
        
        return ft.Column(items, spacing=8)
    
    def build_branch_chart():
        """Construye visualización por sucursal y etapa."""
        lotes = leer_csv()
        data = {}
        
        for lote in lotes:
            branch = lote.get('Branch', 'N/A')
            stage = lote.get('Stage', 'N/A')
            key = (branch, stage)
            data[key] = data.get(key, 0) + 1
        
        if not data:
            return ft.Text("No hay datos para mostrar")
        
        branches = sorted(list(set(k[0] for k in data.keys())))
        stages_order = ['CLONADO', 'VEG. TEMPRANO', 'VEG. TARDIO', 'FLORACIÓN', 'TRANSICIÓN', 'SECADO', 'PT']
        
        stage_colors = {
            'CLONADO': ft.Colors.GREEN_300,
            'VEG. TEMPRANO': ft.Colors.GREEN_500,
            'VEG. TARDIO': ft.Colors.GREEN_700,
            'FLORACIÓN': ft.Colors.PURPLE_400,
            'TRANSICIÓN': ft.Colors.ORANGE_400,
            'SECADO': ft.Colors.BROWN_400,
            'PT': ft.Colors.GREY_400,
        }
        
        items = []
        
        for branch in branches:
            branch_row = [ft.Text(branch, size=14, weight=ft.FontWeight.BOLD, width=50)]
            
            for stage in stages_order:
                count = data.get((branch, stage), 0)
                if count > 0:
                    branch_row.append(
                        ft.Container(
                            content=ft.Text(str(count), size=10, color=ft.Colors.WHITE),
                            bgcolor=stage_colors.get(stage, ft.Colors.BLUE_400),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=4,
                            tooltip=f"{stage}: {count}",
                        )
                    )
            
            items.append(ft.Row(branch_row, spacing=5, wrap=True))
        
        # Leyenda
        legend = ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.Container(width=12, height=12, bgcolor=color, border_radius=2),
                    ft.Text(stage[:10], size=9),
                ], spacing=2),
                padding=2,
            )
            for stage, color in stage_colors.items()
        ], wrap=True, spacing=3)
        
        items.append(ft.Divider())
        items.append(legend)
        
        return ft.Column(items, spacing=10)
    
    chart_container = ft.Ref[ft.Container]()
    
    def show_chart(chart_type):
        if chart_container.current:
            if chart_type == "etapas":
                chart_container.current.content = build_stage_chart()
            elif chart_type == "ubicaciones":
                chart_container.current.content = build_location_chart()
            elif chart_type == "sucursales":
                chart_container.current.content = build_branch_chart()
            page.update()
    
    tab_graficos = ft.Column([
        ft.Text("Gráficos", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row([
            ft.FilledButton("Por Etapa", icon=ft.Icons.PIE_CHART, 
                            on_click=lambda e: show_chart("etapas")),
            ft.FilledButton("Por Ubicación", icon=ft.Icons.BAR_CHART,
                            on_click=lambda e: show_chart("ubicaciones")),
            ft.FilledButton("Por Sucursal", icon=ft.Icons.STACKED_BAR_CHART,
                            on_click=lambda e: show_chart("sucursales")),
        ], wrap=True),
        ft.Container(
            ref=chart_container,
            content=ft.Text("Selecciona un gráfico", color=ft.Colors.GREY),
            height=350,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            padding=10,
        ),
    ], spacing=15, scroll=ft.ScrollMode.AUTO)
    
    # ========== TAB 4: LISTADO ==========
    lotes_listview = ft.Ref[ft.ListView]()
    
    def refresh_lotes_list():
        lotes = leer_csv()
        
        def lote_key(lote):
            try:
                return (lote.get('Branch', ''), int(lote.get('LoteNum', 0)))
            except:
                return (lote.get('Branch', ''), 0)
        
        lotes_sorted = sorted(lotes, key=lote_key)
        
        if lotes_listview.current:
            lotes_listview.current.controls.clear()
            for lote in lotes_sorted:
                branch = lote.get('Branch', '')
                lote_num = lote.get('LoteNum', '')
                lote_id = f"L{lote_num}-{branch}"
                
                variedades = lote.get('Variedades', [])
                total = sum(v['count'] for v in variedades)
                
                # Mostrar todas las variedades en líneas separadas
                vars_widgets = []
                if variedades:
                    for v in sorted(variedades, key=lambda x: x['name']):
                        vars_widgets.append(
                            ft.Text(f"  🌿 {v['name']}: {v['count']}", size=11, color=ft.Colors.GREY_700)
                        )
                else:
                    vars_widgets.append(ft.Text("  Sin variedades", size=11, color=ft.Colors.GREY_500, italic=True))
                
                lotes_listview.current.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(lote_id, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Container(expand=True),
                                    ft.Chip(label=ft.Text(lote.get('Stage', '')), bgcolor=ft.Colors.GREEN_100),
                                ]),
                                ft.Text(f"📍 {lote.get('Location', '')} | 📅 Semana {lote.get('Semana', '')}", size=12),
                                ft.Column(vars_widgets, spacing=0),
                                ft.Text(f"🌱 Total: {total} plantas", size=12, weight=ft.FontWeight.W_500),
                            ], spacing=4),
                            padding=12,
                        ),
                    )
                )
            page.update()
    
    tab_listado = ft.Column([
        ft.Row([
            ft.Text("Listado de Lotes", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: refresh_lotes_list()),
        ]),
        ft.Divider(),
        ft.ListView(ref=lotes_listview, spacing=8, expand=True),
    ], expand=True)
    
    # ========== TAB 5: EDITAR LOTE ==========
    edit_lote_selector_text = ft.Text("Seleccionar lote...", size=14)
    edit_lote_popup = ft.PopupMenuButton(
        content=ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.EDIT, size=20),
                edit_lote_selector_text,
                ft.Icon(ft.Icons.ARROW_DROP_DOWN),
            ], spacing=8),
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            border=ft.Border.all(1, ft.Colors.GREY_400),
            border_radius=8,
        ),
        items=[],
    )
    
    current_edit_lote = {"value": None}
    edit_info_label = ft.Text("", size=12, color=ft.Colors.GREY_600)
    
    edit_stage_dd = ft.Dropdown(
        label="Nueva Etapa",
        options=[ft.dropdown.Option(s) for s in STAGES],
        width=200,
    )
    
    edit_location_dd = ft.Dropdown(
        label="Nueva Ubicación",
        options=[ft.dropdown.Option(l) for l in LOCATIONS],
        width=200,
    )
    
    edit_semana_dd = ft.Dropdown(
        label="Nueva Semana",
        options=[ft.dropdown.Option(str(i)) for i in range(1, 23)],
        width=120,
    )
    
    def on_edit_lote_selected(lote_id):
        """Cuando se selecciona un lote para editar."""
        current_edit_lote["value"] = lote_id
        edit_lote_selector_text.value = lote_id
        
        # Cargar datos del lote
        lotes = leer_csv()
        idx, lote = find_lote_by_id(lote_id, lotes)
        
        if lote:
            edit_stage_dd.value = lote.get('Stage', '')
            edit_location_dd.value = lote.get('Location', '')
            edit_semana_dd.value = lote.get('Semana', '')
            edit_info_label.value = f"Editando: {lote_id}"
        else:
            edit_info_label.value = "Lote no encontrado"
        
        page.update()
    
    def refresh_edit_lotes_popup():
        """Actualiza la lista de lotes en el popup de edición."""
        ids = get_lote_ids_sorted()
        edit_lote_popup.items.clear()
        for lote_id in ids:
            item = ft.PopupMenuItem(
                content=ft.Text(lote_id),
                on_click=lambda e, lid=lote_id: on_edit_lote_selected(lid),
            )
            edit_lote_popup.items.append(item)
        if ids and not current_edit_lote["value"]:
            on_edit_lote_selected(ids[0])
        page.update()
    
    def on_guardar_edicion(e):
        """Guarda los cambios del lote editado."""
        if not current_edit_lote["value"]:
            page.snack_bar = ft.SnackBar(ft.Text("Selecciona un lote primero"))
            page.snack_bar.open = True
            page.update()
            return
        
        lotes = leer_csv()
        idx, lote = find_lote_by_id(current_edit_lote["value"], lotes)
        
        if lote is None:
            page.snack_bar = ft.SnackBar(ft.Text("Lote no encontrado"))
            page.snack_bar.open = True
            page.update()
            return
        
        cambios = []
        
        # Aplicar cambios
        if edit_stage_dd.value and lote.get('Stage') != edit_stage_dd.value:
            lote['Stage'] = edit_stage_dd.value
            cambios.append('Etapa')
        
        if edit_location_dd.value and lote.get('Location') != edit_location_dd.value:
            lote['Location'] = edit_location_dd.value
            cambios.append('Ubicación')
        
        if edit_semana_dd.value and lote.get('Semana') != edit_semana_dd.value:
            lote['Semana'] = edit_semana_dd.value
            cambios.append('Semana')
        
        if not cambios:
            page.snack_bar = ft.SnackBar(ft.Text("No hay cambios para guardar"))
            page.snack_bar.open = True
            page.update()
            return
        
        # Guardar y sincronizar
        guardar_csv(lotes)
        subir_csv_github()
        
        page.snack_bar = ft.SnackBar(ft.Text(f"✅ Lote actualizado ({', '.join(cambios)})"))
        page.snack_bar.open = True
        
        # Refrescar listas
        refresh_edit_lotes_popup()
        refresh_lotes_dropdown()
        page.update()
    
    tab_editar = ft.Column([
        ft.Text("Editar Lote", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Text("Selecciona un lote:", size=12),
        ft.Row([
            edit_lote_popup,
            ft.IconButton(ft.Icons.REFRESH, on_click=lambda e: refresh_edit_lotes_popup(), tooltip="Refrescar lista"),
        ]),
        edit_info_label,
        ft.Container(height=10),
        edit_stage_dd,
        edit_location_dd,
        edit_semana_dd,
        ft.Container(height=15),
        ft.FilledButton(
            "Guardar cambios",
            icon=ft.Icons.SAVE,
            on_click=on_guardar_edicion,
            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE),
        ),
        ft.Divider(),
        ft.Text("Actualización automática", size=16, weight=ft.FontWeight.BOLD),
        ft.Text(
            "Avanza +1 semana a todos los lotes según la semana ISO actual.\n"
            "También actualiza la etapa automáticamente según la semana.",
            size=11,
            color=ft.Colors.GREY_600,
        ),
    ], spacing=10, scroll=ft.ScrollMode.AUTO)
    
    def etapa_por_semana(semana):
        """Determina la etapa según la semana del lote."""
        semana = int(semana)
        if 1 <= semana <= 4:
            return 'CLONADO'
        elif 5 <= semana <= 7:
            return 'VEG. TEMPRANO'
        elif 8 <= semana <= 9:
            return 'VEG. TARDIO'
        elif 10 <= semana <= 20:
            return 'FLORACIÓN'
        elif semana == 21:
            return 'SECADO'
        elif semana == 22:
            return 'PT'
        else:
            return ''
    
    def actualizar_semanas_etapas_auto(e=None):
        """Actualiza semanas y etapas de todos los lotes según semana ISO."""
        try:
            lotes = leer_csv()
            hoy = datetime.now()
            semana_iso_actual = hoy.isocalendar()[1]
            
            cambios = []
            
            for lote in lotes:
                try:
                    sem = int(lote.get('Semana', '0'))
                except:
                    continue
                
                # Leer la semana ISO de la última actualización
                ultima_act = lote.get('ÚltimaActualización', '')
                semana_iso_lote = None
                if ultima_act:
                    try:
                        semana_iso_lote = datetime.strptime(ultima_act, '%Y-%m-%d').isocalendar()[1]
                    except:
                        semana_iso_lote = None
                
                # Solo avanzar si la semana ISO actual es distinta a la última registrada
                if 1 <= sem < 22 and (semana_iso_lote is None or semana_iso_lote != semana_iso_actual):
                    nueva_sem = sem + 1
                    nueva_etapa = etapa_por_semana(nueva_sem)
                    etapa_ant = lote.get('Stage', '')
                    
                    cambios.append({
                        'id': lote.get('ID', ''),
                        'sem_ant': sem,
                        'sem_nueva': nueva_sem,
                        'etapa_ant': etapa_ant,
                        'etapa_nueva': nueva_etapa,
                    })
                    
                    lote['Semana'] = str(nueva_sem)
                    lote['Stage'] = nueva_etapa
                    lote['ÚltimaActualización'] = hoy.strftime('%Y-%m-%d')
            
            if not cambios:
                # Usar diálogo en lugar de snackbar para mayor visibilidad
                def cerrar_info(e):
                    dlg_info.open = False
                    page.update()
                
                dlg_info = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("✅ Sin cambios"),
                    content=ft.Text("Todos los lotes ya están actualizados para esta semana."),
                    actions=[ft.TextButton("OK", on_click=cerrar_info)],
                )
                page.overlay.append(dlg_info)
                dlg_info.open = True
                page.update()
                return
            
            # Mostrar diálogo de confirmación
            cambios_text = "\n".join([
                f"{c['id']}: Sem {c['sem_ant']}→{c['sem_nueva']} | {c['etapa_ant']}→{c['etapa_nueva']}"
                for c in cambios[:10]  # Mostrar máximo 10
            ])
            if len(cambios) > 10:
                cambios_text += f"\n... y {len(cambios) - 10} más"
            
            def cerrar_dialogo(e):
                dialogo.open = False
                page.update()
            
            def confirmar_actualizacion(e):
                dialogo.open = False
                page.update()
                
                # Guardar y sincronizar
                guardar_csv(lotes)
                subir_csv_github()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ {len(cambios)} lotes actualizados"))
                page.snack_bar.open = True
                
                # Refrescar listas
                refresh_edit_lotes_popup()
                refresh_lotes_dropdown()
                page.update()
            
            dialogo = ft.AlertDialog(
                modal=True,
                title=ft.Text(f"¿Actualizar {len(cambios)} lotes?"),
                content=ft.Container(
                    content=ft.Text(cambios_text, size=12),
                    height=200,
                    width=300,
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cerrar_dialogo),
                    ft.TextButton(
                        "Actualizar", 
                        on_click=confirmar_actualizacion,
                        style=ft.ButtonStyle(color=ft.Colors.PURPLE),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            page.overlay.append(dialogo)
            dialogo.open = True
            page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"))
            page.snack_bar.open = True
            page.update()
    
    # Agregar botón de actualización al tab_editar
    tab_editar.controls.append(
        ft.FilledButton(
            "⏰ Actualizar semanas y etapas",
            icon=ft.Icons.UPDATE,
            on_click=actualizar_semanas_etapas_auto,
            style=ft.ButtonStyle(bgcolor=ft.Colors.PURPLE, color=ft.Colors.WHITE),
        )
    )
    
    # ========== TAB 6: CONFIGURACIÓN ==========
    config_repo_field = ft.TextField(
        label="Repositorio GitHub",
        hint_text="usuario/nombre-repo",
        value=GITHUB_REPO or "",
        width=300,
        prefix_icon=ft.Icons.FOLDER,
    )
    
    config_token_field = ft.TextField(
        label="Token de GitHub",
        hint_text="ghp_xxxxxxxxxxxx",
        value=GITHUB_TOKEN or "",
        width=300,
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.Icons.KEY,
    )
    
    config_status = ft.Text("", size=12)
    
    def on_save_config(e):
        repo = config_repo_field.value.strip()
        token = config_token_field.value.strip()
        
        if not repo or "/" not in repo:
            config_status.value = "❌ Formato de repo inválido (usuario/repo)"
            config_status.color = ft.Colors.RED
            page.update()
            return
        
        if not token or len(token) < 10:
            config_status.value = "❌ Token inválido"
            config_status.color = ft.Colors.RED
            page.update()
            return
        
        guardar_config_en_storage(page, repo, token)
        config_status.value = "✅ Configuración guardada"
        config_status.color = ft.Colors.GREEN
        page.update()
    
    def on_test_connection(e):
        config_status.value = "🔄 Probando conexión..."
        config_status.color = ft.Colors.BLUE
        page.update()
        
        success, msg = descargar_csv_github()
        if success:
            config_status.value = f"✅ Conexión exitosa"
            config_status.color = ft.Colors.GREEN
            update_status(True, "Conectado")
        else:
            config_status.value = f"❌ Error: {msg}"
            config_status.color = ft.Colors.RED
            update_status(False, msg)
        page.update()
    
    def on_clear_config(e):
        config_path = get_config_path()
        if os.path.exists(config_path):
            os.remove(config_path)
        config_repo_field.value = ""
        config_token_field.value = ""
        config_status.value = "🗑️ Configuración eliminada"
        config_status.color = ft.Colors.ORANGE
        page.update()
    
    tab_config = ft.Column([
        ft.Text("⚙️ Configuración GitHub", size=20, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Text(
            "Configura tu repositorio de GitHub para sincronizar los datos.",
            size=12,
            color=ft.Colors.GREY_700,
        ),
        ft.Container(height=10),
        config_repo_field,
        config_token_field,
        ft.Container(height=10),
        ft.Row([
            ft.FilledButton(
                "Guardar",
                icon=ft.Icons.SAVE,
                on_click=on_save_config,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
            ),
            ft.OutlinedButton(
                "Probar conexión",
                icon=ft.Icons.WIFI,
                on_click=on_test_connection,
            ),
            ft.TextButton(
                "Limpiar",
                icon=ft.Icons.DELETE_OUTLINE,
                on_click=on_clear_config,
            ),
        ], wrap=True),
        config_status,
        ft.Divider(),
        ft.Text("ℹ️ Cómo obtener un token:", size=14, weight=ft.FontWeight.BOLD),
        ft.Text(
            "1. Ve a GitHub → Settings → Developer settings\n"
            "2. Personal access tokens → Tokens (classic)\n"
            "3. Generate new token\n"
            "4. Selecciona permisos: repo (full control)",
            size=11,
            color=ft.Colors.GREY_700,
        ),
    ], spacing=10, scroll=ft.ScrollMode.AUTO)
    
    # ========== NAVEGACIÓN CON CONTENIDO ==========
    content_area = ft.Container(
        content=ft.Container(tab_crear, padding=15),
        expand=True,
    )
    
    def change_view(e):
        index = e.control.selected_index
        views = [tab_crear, tab_variedades, tab_editar, tab_graficos, tab_listado, tab_config]
        content_area.content = ft.Container(views[index], padding=15)
        page.update()
    
    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=change_view,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.ADD_BOX, label="Crear"),
            ft.NavigationBarDestination(icon=ft.Icons.GRASS, label="Variedades"),
            ft.NavigationBarDestination(icon=ft.Icons.EDIT, label="Editar"),
            ft.NavigationBarDestination(icon=ft.Icons.ANALYTICS, label="Gráficos"),
            ft.NavigationBarDestination(icon=ft.Icons.LIST, label="Listado"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Config"),
        ],
    )
    
    # Layout principal
    page.add(
        ft.Column([
            status_bar,
            content_area,
        ], expand=True),
    )
    page.navigation_bar = nav_bar
    
    # Inicialización
    if config_ok:
        check_connection()
    else:
        update_status(False, config_msg)
    
    refresh_lotes_list()
    refresh_edit_lotes_popup()


# Punto de entrada
if __name__ == "__main__":
    ft.app(main)  # Compatible con versiones anteriores también
