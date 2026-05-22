from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import pandas as pd
import io
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

WRC_POINTS = [50, 40, 34, 30, 27, 24, 21, 19, 17, 15, 13, 11, 9, 7, 6, 5, 4, 3, 2, 1]
PS_POINTS = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1] 

def get_db_connection():
    conn = sqlite3.connect("wrc_liga.db")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    
    try:
        conn.execute("ALTER TABLE teams ADD COLUMN is_factory INTEGER DEFAULT 0")
        conn.execute("ALTER TABLE drivers ADD COLUMN car TEXT DEFAULT ''")
        conn.commit()
    except sqlite3.OperationalError:
        pass 
        
    return conn

def get_champ(conn, champ_id):
    return conn.execute("SELECT * FROM championships WHERE id = ?", (champ_id,)).fetchone()

def format_time(ms):
    if ms == 0: return "DNF"
    minutes = ms // 60000; seconds = (ms % 60000) // 1000; milliseconds = ms % 1000
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def parse_racenet_time(time_str):
    if pd.isna(time_str) or not isinstance(time_str, str): return 0
    try:
        main_part = time_str.split('.')[0]
        fractions = time_str.split('.')[1][:3] if '.' in time_str else "000"
        elements = main_part.split(':')
        if len(elements) == 3: h, m, s = elements
        elif len(elements) == 2: h = 0; m, s = elements
        elif len(elements) == 1: h, m = 0, 0; s = elements[0]
        else: return 0
        return (int(h) * 3600000) + (int(m) * 60000) + (int(s) * 1000) + int(fractions)
    except Exception: return 0

# ================= 1. MAIN CHAMPIONSHIP PANEL =================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    conn = get_db_connection()
    champs = conn.execute("SELECT * FROM championships ORDER BY id DESC").fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="index.html", context={"request": request, "champs": champs, "champ": None})

@app.post("/add_championship")
def add_champ(name: str = Form(...)):
    conn = get_db_connection()
    conn.execute("INSERT INTO championships (name) VALUES (?)", (name,))
    conn.commit(); conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete_championship/{champ_id}")
def del_champ(champ_id: int):
    conn = get_db_connection()
    conn.execute("DELETE FROM championships WHERE id = ?", (champ_id,))
    conn.commit(); conn.close()
    return RedirectResponse(url="/", status_code=303)

# ================= 2. INNER WORKSPACE VIEWS =================

@app.get("/c/{champ_id}/dashboard", response_class=HTMLResponse)
def champ_dashboard(request: Request, champ_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id); conn.close()
    return templates.TemplateResponse(request=request, name="champ_dashboard.html", context={"request": request, "champ": champ})

@app.get("/c/{champ_id}/rallies", response_class=HTMLResponse)
def rallies(request: Request, champ_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id)
    rallies = conn.execute("SELECT * FROM rallies WHERE champ_id = ?", (champ_id,)).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="rallies.html", context={"request": request, "champ": champ, "rallies": rallies})

@app.get("/c/{champ_id}/teams", response_class=HTMLResponse)
def teams(request: Request, champ_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id)
    teams = conn.execute("SELECT * FROM teams WHERE champ_id = ?", (champ_id,)).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="teams.html", context={"request": request, "champ": champ, "teams": teams})

@app.get("/c/{champ_id}/drivers", response_class=HTMLResponse)
def drivers(request: Request, champ_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id)
    teams = conn.execute("SELECT * FROM teams WHERE champ_id = ?", (champ_id,)).fetchall()
    drivers = conn.execute("SELECT * FROM drivers WHERE champ_id = ? ORDER BY id DESC", (champ_id,)).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="drivers.html", context={"request": request, "champ": champ, "drivers": drivers, "teams": teams})

@app.get("/c/{champ_id}/import", response_class=HTMLResponse)
def import_page(request: Request, champ_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id)
    rallies = conn.execute("SELECT * FROM rallies WHERE champ_id = ?", (champ_id,)).fetchall()
    uploaded_raw = conn.execute("SELECT DISTINCT sr.rally_id, sr.stage_number FROM stage_results sr JOIN rallies r ON sr.rally_id = r.id WHERE r.champ_id = ?", (champ_id,)).fetchall()
    conn.close()
    
    uploaded_stages = {}
    for row in uploaded_raw:
        r_id = str(row['rally_id'])
        if r_id not in uploaded_stages: uploaded_stages[r_id] = []
        uploaded_stages[r_id].append(row['stage_number'])
        
    return templates.TemplateResponse(request=request, name="import.html", context={"request": request, "champ": champ, "rallies": rallies, "uploaded_stages": json.dumps(uploaded_stages)})

@app.get("/c/{champ_id}/graphics", response_class=HTMLResponse)
def graphics_page(request: Request, champ_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id)
    rallies = conn.execute("SELECT * FROM rallies WHERE champ_id = ?", (champ_id,)).fetchall()
    conn.close()
    return templates.TemplateResponse(request=request, name="graphics.html", context={"request": request, "champ": champ, "rallies": rallies})

# ================= 3. CRUD & IMPORT LOGIC =================

@app.post("/c/{champ_id}/upload_csv")
async def upload_csv(request: Request, champ_id: int):
    form = await request.form(); rally_id = int(form.get("rally_id"))
    conn = get_db_connection(); cursor = conn.cursor()
    
    for key, file_obj in form.items():
        if key.startswith("file_") and hasattr(file_obj, "filename") and file_obj.filename:
            stage_number = int(key.split("_")[1])
            contents = await file_obj.read()
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
            
            for index, row in df.iterrows():
                ea_nick = str(row.get('DisplayName', '')).strip()
                time_str = str(row.get('Time', '')).strip()
                platform_val = str(row.get('Platform', '')).strip()
                vehicle_val = str(row.get('Vehicle', '')).strip()
                rank_val = row.get('Rank', 999)
                rank_val = int(rank_val) if not pd.isna(rank_val) else 999
                
                if not ea_nick or ea_nick == "nan": continue
                
                cursor.execute("SELECT id, car FROM drivers WHERE ea_nickname = ? AND champ_id = ?", (ea_nick, champ_id))
                res = cursor.fetchone()
                if res: 
                    driver_id = res['id']
                    if vehicle_val and not res['car']:
                        cursor.execute("UPDATE drivers SET car = ? WHERE id = ?", (vehicle_val, driver_id))
                else:
                    cursor.execute("INSERT INTO drivers (champ_id, discord_name, ea_nickname, platform, car) VALUES (?, ?, ?, ?, ?)", (champ_id, ea_nick, ea_nick, platform_val, vehicle_val))
                    driver_id = cursor.lastrowid
                    
                time_ms = parse_racenet_time(time_str)
                cursor.execute("DELETE FROM stage_results WHERE rally_id=? AND driver_id=? AND stage_number=?", (rally_id, driver_id, stage_number))
                cursor.execute("INSERT INTO stage_results (rally_id, driver_id, stage_number, time_ms, stage_rank) VALUES (?, ?, ?, ?, ?)", (rally_id, driver_id, stage_number, time_ms, rank_val))

    conn.commit(); conn.close()
    return RedirectResponse(url=f"/c/{champ_id}/import", status_code=303)

@app.post("/c/{champ_id}/add_rally")
def add_r(champ_id: int, name: str=Form(...), stages_count: int=Form(...)):
    conn=get_db_connection(); conn.execute("INSERT INTO rallies (champ_id, name, stages_count) VALUES (?,?,?)", (champ_id, name, stages_count)); conn.commit(); return RedirectResponse(f"/c/{champ_id}/rallies", 303)

@app.post("/c/{champ_id}/add_team")
def add_t(champ_id: int, name: str=Form(...), car: str=Form(...), color_hex: str=Form(...), color_border_hex: str=Form(...), is_factory: bool=Form(False)):
    conn=get_db_connection(); conn.execute("INSERT INTO teams (champ_id, name, car, color_hex, color_border_hex, is_factory) VALUES (?,?,?,?,?,?)", (champ_id, name,car,color_hex,color_border_hex, int(is_factory))); conn.commit(); return RedirectResponse(f"/c/{champ_id}/teams", 303)

@app.post("/c/{champ_id}/update_driver/{d_id}")
def update_d(champ_id: int, d_id: int, discord_name: str=Form(...), team_id: int=Form(...), nationality: str=Form(...), car: str=Form("")):
    conn=get_db_connection()
    conn.execute("UPDATE drivers SET discord_name=?, team_id=?, nationality=?, car=? WHERE id=? AND champ_id=?", 
                 (discord_name, None if team_id==0 else team_id, nationality, car, d_id, champ_id))
    conn.commit(); conn.close()
    return RedirectResponse(f"/c/{champ_id}/drivers", 303)

@app.post("/c/{champ_id}/delete_rally/{rally_id}")
def delete_r(champ_id: int, rally_id: int):
    conn=get_db_connection(); conn.execute("DELETE FROM rallies WHERE id = ? AND champ_id=?", (rally_id, champ_id)); conn.commit(); return RedirectResponse(f"/c/{champ_id}/rallies", 303)

@app.post("/c/{champ_id}/delete_team/{team_id}")
def del_team(champ_id: int, team_id: int):
    conn = get_db_connection(); conn.execute("DELETE FROM teams WHERE id = ? AND champ_id=?", (team_id, champ_id)); conn.commit(); return RedirectResponse(f"/c/{champ_id}/teams", 303)

@app.post("/c/{champ_id}/delete_driver/{driver_id}")
def del_driver(champ_id: int, driver_id: int):
    conn = get_db_connection(); conn.execute("DELETE FROM drivers WHERE id = ? AND champ_id=?", (driver_id, champ_id)); conn.commit(); return RedirectResponse(f"/c/{champ_id}/drivers", 303)

# ================= 4. GRAPHIC RENDERING =================

def paginate_results(results):
    pages = []
    if not results: return pages
    pages.append(results[:10])
    for i in range(10, len(results), 10):
        page = [results[0]] + results[i:i+10]
        pages.append(page)
    return pages

def build_graphic_dict(r, leader_time=None, pts=0):
    w = dict(r)
    w['display_car'] = w['team_car'] if w.get('team_id') else w.get('driver_car', 'Unknown Car')
    w['is_factory'] = bool(w.get('is_factory', 0))
    
    if 'total_time' in w:
        if w['total_time'] == 0: 
            w['time'] = "DNF"; w['gap'] = "-"
        else: 
            w['time'] = format_time(w['total_time'])
            if leader_time: w['gap'] = "-" if w['total_time'] == leader_time else "+" + format_time(w['total_time'] - leader_time)
            else: w['gap'] = "-"
            
    w['points'] = pts
    return w

@app.get("/c/{champ_id}/render/rally/{rally_id}", response_class=HTMLResponse)
def render_rally(request: Request, champ_id: int, rally_id: int):
    conn = get_db_connection()
    champ = get_champ(conn, champ_id)
    has_overall = conn.execute("SELECT COUNT(*) as c FROM stage_results WHERE rally_id=? AND stage_number=0", (rally_id,)).fetchone()['c']
    
    query_select = "SELECT d.id as d_id, d.discord_name, d.nationality, d.car as driver_car, d.team_id, t.name as team_name, t.car as team_car, t.is_factory, t.color_hex, t.color_border_hex"
    if has_overall > 0:
        results = conn.execute(f"""
            {query_select}, sr.time_ms as total_time
            FROM stage_results sr JOIN drivers d ON sr.driver_id = d.id LEFT JOIN teams t ON d.team_id = t.id
            WHERE sr.rally_id = ? AND sr.stage_number = 0 ORDER BY sr.stage_rank ASC
        """, (rally_id,)).fetchall()
    else:
        max_stages = conn.execute("SELECT MAX(c) as max_c FROM (SELECT COUNT(stage_number) as c FROM stage_results WHERE rally_id=? AND stage_number>0 GROUP BY driver_id)", (rally_id,)).fetchone()['max_c'] or 0
        results = conn.execute(f"""
            {query_select}, SUM(sr.time_ms) as total_time
            FROM stage_results sr JOIN drivers d ON sr.driver_id = d.id LEFT JOIN teams t ON d.team_id = t.id
            WHERE sr.rally_id = ? AND sr.stage_number > 0 GROUP BY d.id HAVING COUNT(sr.stage_number) = ? AND MIN(sr.time_ms) > 0 ORDER BY total_time ASC
        """, (rally_id, max_stages)).fetchall()
        
    stages_count = conn.execute("SELECT stages_count FROM rallies WHERE id=?", (rally_id,)).fetchone()['stages_count']
    ps_results = conn.execute("SELECT driver_id FROM stage_results WHERE rally_id=? AND stage_number=? ORDER BY stage_rank ASC LIMIT 10", (rally_id, stages_count)).fetchall()
    ps_points_map = {row['driver_id']: PS_POINTS[idx] for idx, row in enumerate(ps_results) if idx < len(PS_POINTS)}

    results_data = []
    if results:
        leader_time = results[0]['total_time']
        for i, r in enumerate(results):
            pts = (WRC_POINTS[i] if i < len(WRC_POINTS) else 0) + ps_points_map.get(r['d_id'], 0)
            w = build_graphic_dict(r, leader_time, pts)
            w['pos'] = i + 1
            results_data.append(w)
            
    rally_info = conn.execute("SELECT name FROM rallies WHERE id=?", (rally_id,)).fetchone()
    conn.close()
    return templates.TemplateResponse(request=request, name="render_table.html", context={
        "request": request, "pages": paginate_results(results_data), "title": f"RESULTS: {rally_info['name']} - {champ['name']}", "show_points": True
    })

@app.get("/c/{champ_id}/render/powerstage/{rally_id}", response_class=HTMLResponse)
def render_powerstage(request: Request, champ_id: int, rally_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id)
    rally_info = conn.execute("SELECT name, stages_count FROM rallies WHERE id=?", (rally_id,)).fetchone()
    
    results = conn.execute("""
        SELECT d.id as d_id, d.discord_name, d.nationality, d.car as driver_car, d.team_id, t.name as team_name, t.car as team_car, t.is_factory, t.color_hex, t.color_border_hex, sr.time_ms as total_time
        FROM stage_results sr JOIN drivers d ON sr.driver_id = d.id LEFT JOIN teams t ON d.team_id = t.id
        WHERE sr.rally_id = ? AND sr.stage_number = ? ORDER BY sr.stage_rank ASC LIMIT 10
    """, (rally_id, rally_info['stages_count'])).fetchall()
    
    results_data = []
    if results:
        leader_time = results[0]['total_time']
        for i, r in enumerate(results):
            w = build_graphic_dict(r, leader_time, PS_POINTS[i] if i < len(PS_POINTS) else 0)
            w['pos'] = i + 1
            results_data.append(w)
            
    conn.close()
    return templates.TemplateResponse(request=request, name="render_table.html", context={
        "request": request, "pages": paginate_results(results_data), "title": f"POWERSTAGE: {rally_info['name']} - {champ['name']}", "show_points": True
    })

@app.get("/c/{champ_id}/render/championship", response_class=HTMLResponse)
def render_championship(request: Request, champ_id: int):
    conn = get_db_connection(); champ = get_champ(conn, champ_id)
    rallies = conn.execute("SELECT id, stages_count FROM rallies WHERE champ_id=?", (champ_id,)).fetchall()
    participants_db = conn.execute("SELECT DISTINCT id FROM drivers WHERE champ_id = ?", (champ_id,)).fetchall()
    participant_ids = [row['id'] for row in participants_db]

    driver_points = {}
    for r in rallies:
        r_id = r['id']
        has_overall = conn.execute("SELECT COUNT(*) as c FROM stage_results WHERE rally_id=? AND stage_number=0", (r_id,)).fetchone()['c']
        if has_overall > 0:
            gen = conn.execute("SELECT driver_id FROM stage_results WHERE rally_id=? AND stage_number=0 ORDER BY stage_rank ASC", (r_id,)).fetchall()
        else:
            max_stages = conn.execute("SELECT MAX(c) as max_c FROM (SELECT COUNT(stage_number) as c FROM stage_results WHERE rally_id=? AND stage_number>0 GROUP BY driver_id)", (r_id,)).fetchone()['max_c'] or 0
            gen = conn.execute("SELECT driver_id, SUM(time_ms) as t FROM stage_results WHERE rally_id=? AND stage_number>0 GROUP BY driver_id HAVING COUNT(stage_number) = ? AND MIN(time_ms) > 0 ORDER BY t ASC", (r_id, max_stages)).fetchall()
        for i, row in enumerate(gen):
            if i < len(WRC_POINTS): driver_points[row['driver_id']] = driver_points.get(row['driver_id'], 0) + WRC_POINTS[i]
        ps = conn.execute("SELECT driver_id FROM stage_results WHERE rally_id=? AND stage_number=? ORDER BY stage_rank ASC LIMIT 10", (r_id, r['stages_count'])).fetchall()
        for i, row in enumerate(ps):
            if i < len(PS_POINTS): driver_points[row['driver_id']] = driver_points.get(row['driver_id'], 0) + PS_POINTS[i]
                
    drivers_data = conn.execute("""
        SELECT d.id as d_id, d.discord_name, d.nationality, d.car as driver_car, d.team_id, t.name as team_name, t.car as team_car, t.is_factory, t.color_hex, t.color_border_hex 
        FROM drivers d LEFT JOIN teams t ON d.team_id = t.id WHERE d.champ_id = ?
    """, (champ_id,)).fetchall()
    
    results_data = []
    for r in drivers_data:
        if r['d_id'] in participant_ids or r['d_id'] in driver_points:
            w = build_graphic_dict(r, None, 0)
            w['total_points'] = driver_points.get(r['d_id'], 0)
            results_data.append(w)
            
    results_data.sort(key=lambda x: x['total_points'], reverse=True)
    if results_data:
        leader_pts = results_data[0]['total_points']
        for i, w in enumerate(results_data):
            w['pos'] = i + 1; w['time'] = f"{w['total_points']} pts"
            w['gap'] = "-" if i == 0 else f"-{leader_pts - w['total_points']} pts"
            w['points'] = ""

    conn.close()
    return templates.TemplateResponse(request=request, name="render_table.html", context={
        "request": request, "pages": paginate_results(results_data), "title": f"STANDINGS: {champ['name']}", "show_points": False
    })