import datetime
import httpx
import os


# Dios se apiade de este codigo 

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if not os.getenv("SUPABASE_KEY") and os.path.exists(os.path.join(os.path.dirname(__file__), ".env")):
    try:
        with open(os.path.join(os.path.dirname(__file__), ".env"), "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("SUPABASE_KEY"):
                    k = line.split("=", 1)[1].strip().strip('"').strip("'")
                    os.environ["SUPABASE_KEY"] = k
    except Exception:
        pass

SUPABASE_URL = "https://qapnsmmkjvgbmmjyofan.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY") 
# Deja de poner la api key en publico nos van a hackear todo 

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

PK_MAP = {
    "Categoria": "id_categoria",
    "Lugar": "id_Lugar",
    "Ponente": "id_ponente",
    "Evento": "id_evento",
    "Asistentes": "id_asistentes",
    "Inscripcion": "id_inscripcion",
    "Pago": "id_pago"
}

async def _request(method: str, endpoint: str, params: dict = None, data: dict = None):
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.request(method, url, headers=HEADERS, params=params, json=data)
            if res.status_code >= 400:
                return None, f"Supabase Error {res.status_code}: {res.text}"
            return (res.json() if res.content else []), None
    except Exception as exc:
        return None, f"Fallo de conexión con Supabase: {exc}"

# CRUD DIRECTO EN SUPABASE

async def cargar_categorias(): return await _request("GET", "Categoria", params={"select": "*"})
async def crear_categoria(datos: dict): return await _request("POST", "Categoria", data=datos)
async def actualizar_categoria(id_cat: int, datos: dict): return await _request("PATCH", "Categoria", params={"id_categoria": f"eq.{id_cat}"}, data=datos)
async def eliminar_categoria(id_cat: int):
    evs, _ = await _request("GET", "Evento", params={"id_categoria": f"eq.{id_cat}", "select": "id_evento"})
    for ev in (evs or []): await eliminar_evento(ev["id_evento"])
    return await _request("DELETE", "Categoria", params={"id_categoria": f"eq.{id_cat}"})

async def cargar_lugares(): return await _request("GET", "Lugar", params={"select": "*"})
async def crear_lugar(datos: dict): return await _request("POST", "Lugar", data=datos)
async def actualizar_lugar(id_lug: int, datos: dict): return await _request("PATCH", "Lugar", params={"id_Lugar": f"eq.{id_lug}"}, data=datos)
async def eliminar_lugar(id_lug: int):
    evs, _ = await _request("GET", "Evento", params={"id_lugar": f"eq.{id_lug}", "select": "id_evento"})
    for ev in (evs or []): await eliminar_evento(ev["id_evento"])
    return await _request("DELETE", "Lugar", params={"id_Lugar": f"eq.{id_lug}"})

async def cargar_ponentes(): return await _request("GET", "Ponente", params={"select": "*"})
async def crear_ponente(datos: dict): return await _request("POST", "Ponente", data=datos)
async def actualizar_ponente(id_po: int, datos: dict): return await _request("PATCH", "Ponente", params={"id_ponente": f"eq.{id_po}"}, data=datos)
async def eliminar_ponente(id_po: int):
    await _request("DELETE", "evento_ponente", params={"id_ponente": f"eq.{id_po}"})
    return await _request("DELETE", "Ponente", params={"id_ponente": f"eq.{id_po}"})

async def cargar_eventos(): return await _request("GET", "Evento", params={"select": "*"})
async def crear_evento(datos: dict): return await _request("POST", "Evento", data=datos)
async def actualizar_evento(id_ev: int, datos: dict):
    res, err = await _request("PATCH", "Evento", params={"id_evento": f"eq.{id_ev}"}, data=datos)
    if not err and "fecha y hora" in datos:
        await _request("PATCH", "evento_ponente", params={"id_evento": f"eq.{id_ev}"}, data={"hora": datos["fecha y hora"]})
    return res, err
async def eliminar_evento(id_ev: int):
    await _request("DELETE", "evento_ponente", params={"id_evento": f"eq.{id_ev}"})
    inss, _ = await _request("GET", "Inscripcion", params={"id_evento": f"eq.{id_ev}", "select": "id_inscripcion"})
    for i in (inss or []):
        await _request("DELETE", "Pago", params={"id_inscripcion": f"eq.{i.get('id_inscripcion')}"})
    await _request("DELETE", "Inscripcion", params={"id_evento": f"eq.{id_ev}"})
    return await _request("DELETE", "Evento", params={"id_evento": f"eq.{id_ev}"})

async def cargar_asistentes(): return await _request("GET", "Asistentes", params={"select": "*"})
async def crear_asistente(datos: dict):
    payload = dict(datos)
    res, err = await _request("POST", "Asistentes", data=payload)
    if err and "invalid input syntax for type bigint" in err:
        payload["nombre"] = abs(hash(str(payload.get("nombre", "")))) % (10**9)
        res, err = await _request("POST", "Asistentes", data=payload)
    return res, err
async def actualizar_asistente(id_as: int, datos: dict):
    payload = dict(datos)
    res, err = await _request("PATCH", "Asistentes", params={"id_asistentes": f"eq.{id_as}"}, data=payload)
    if err and "invalid input syntax for type bigint" in err:
        payload["nombre"] = abs(hash(str(payload.get("nombre", "")))) % (10**9)
        res, err = await _request("PATCH", "Asistentes", params={"id_asistentes": f"eq.{id_as}"}, data=payload)
    return res, err

async def eliminar_asistente(id_as: int):
    inss, _ = await _request("GET", "Inscripcion", params={"id_asistentes": f"eq.{id_as}", "select": "id_inscripcion"})
    for i in (inss or []):
        await _request("DELETE", "Pago", params={"id_inscripcion": f"eq.{i.get('id_inscripcion')}"})
    await _request("DELETE", "Inscripcion", params={"id_asistentes": f"eq.{id_as}"})
    return await _request("DELETE", "Asistentes", params={"id_asistentes": f"eq.{id_as}"})


# AGENDA 
async def cargar_evento_ponente(): return await _request("GET", "evento_ponente", params={"select": "*"})

async def crear_evento_ponente(datos: dict):
    payload = dict(datos)
    ev, _ = await _request("GET", "Evento", params={"id_evento": f"eq.{payload.get('id_evento')}", "select": "fecha y hora"})
    if ev and ev[0].get("fecha y hora"):
        payload["hora"] = str(ev[0].get("fecha y hora")).strip()
    else:
        hora_val = str(payload.get("hora", "10:00")).strip()
        if " " not in hora_val and "T" not in hora_val:
            fecha_base = datetime.datetime.now().strftime("%Y-%m-%d")
            if len(hora_val) == 5: hora_val += ":00"
            payload["hora"] = f"{fecha_base} {hora_val}"
    return await _request("POST", "evento_ponente", data=payload)

async def eliminar_evento_ponente(id_ev: int, id_po: int):
    return await _request("DELETE", "evento_ponente", params={"id_evento": f"eq.{id_ev}", "id_ponente": f"eq.{id_po}"})
 #Si no elimina juro que me muero
async def cargar_ponentes_por_evento(id_evento: int):
    rels, _ = await _request("GET", "evento_ponente", params={"id_evento": f"eq.{id_evento}", "select": "*"})
    pos_data, _ = await cargar_ponentes()
    pos = {p["id_ponente"]: p for p in (pos_data or [])}
    return [{
        "id_ponente": r["id_ponente"],
        "nombre": pos.get(r["id_ponente"], {}).get("Nombre", f"Ponente #{r['id_ponente']}"),
        "especialidad": pos.get(r["id_ponente"], {}).get("Especialidad", "General"),
        "hora": str(r.get("hora", "")).replace("T", " ")[11:16] or str(r.get("hora", ""))
    } for r in (rels or [])]

async def mapa_ponentes_por_evento():
    rels, _ = await cargar_evento_ponente()
    pos_data, _ = await cargar_ponentes()
    pos = {p["id_ponente"]: p for p in (pos_data or [])}
    res = {}
    for r in (rels or []):
        eid = r.get("id_evento")
        p = pos.get(r.get("id_ponente"), {})
        nom = p.get("Nombre", "Ponente")
        esp = p.get("Especialidad", "")
        hora = str(r.get("hora", "")).replace("T", " ")[11:16] or str(r.get("hora", ""))
        desc = f"{nom} ({esp}) a las {hora}" if esp else f"{nom} a las {hora}"
        res.setdefault(eid, []).append(desc)
    return res

async def cargar_inscripciones(): return await _request("GET", "Inscripcion", params={"select": "*"})
async def cargar_pagos(): return await _request("GET", "Pago", params={"select": "*"})

# TRANSACCIÓN CENTRAL & REGLA DE NEGOCIO

async def registrar_inscripcion(id_evento: int, datos_asistente: dict, datos_pago: dict):
    # 1. Regla de Negocio: Validar existencia en Supabase
    ev, err_ev = await _request("GET", "Evento", params={"id_evento": f"eq.{id_evento}", "select": "id_evento"})
    if err_ev or not ev:
        return None, "Regla de Negocio: No se puede registrar una inscripción a un evento inexistente."

    # 2. Asistente
    asistente, err_as = await crear_asistente(datos_asistente)
    if err_as or not asistente:
        return None, f"Error al guardar asistente: {err_as}"
    id_asistente = asistente[0]["id_asistentes"]

    # 3. Inscripcion
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inscripcion_data = {"id_evento": id_evento, "id_asistentes": id_asistente, "fecha": now}
    inscripcion, err_ins = await _request("POST", "Inscripcion", data=inscripcion_data)
    if err_ins or not inscripcion:
        return None, f"Error al generar inscripción: {err_ins}"
    id_inscripcion = inscripcion[0]["id_inscripcion"]

    # 4. Pago
    pago_data = {
        "id_inscripcion": id_inscripcion,
        "cantidad": int(datos_pago.get("cantidad", 1)),
        "monto_pago": int(round(float(datos_pago.get("monto_pago", 0)))),
        "fecha": now
    }
    pago, err_pg = await _request("POST", "Pago", data=pago_data)
    if err_pg or not pago:
        return None, f"Error al procesar pago: {err_pg}"

    return {"asistente": asistente[0], "inscripcion": inscripcion[0], "pago": pago[0]}, None

# 3 REPORTES SQL 
async def reporte_agenda():
    rels, err1 = await cargar_evento_ponente()
    evs_data, _ = await cargar_eventos()
    pos_data, _ = await cargar_ponentes()
    
    evs = {e["id_evento"]: e.get("titulo", "N/A") for e in (evs_data or [])}
    pos = {p["id_ponente"]: p for p in (pos_data or [])}
    
    resultado = []
    for r in (rels or []):
        id_ev = r.get("id_evento")
        id_po = r.get("id_ponente")
        p_info = pos.get(id_po, {})
        hora_fmt = str(r.get("hora", "")).replace("T", " ")[:16]
        resultado.append({
            "evento": evs.get(id_ev, f"Evento #{id_ev}"),
            "ponente": p_info.get("Nombre", f"Ponente #{id_po}"),
            "especialidad": p_info.get("Especialidad", "General"),
            "hora": hora_fmt
        })
    return resultado, err1

async def reporte_ocupacion():
    evs, err = await cargar_eventos()
    inss, _ = await cargar_inscripciones()
    counts = {}
    for i in (inss or []):
        eid = i.get("id_evento")
        counts[eid] = counts.get(eid, 0) + 1
    return [{
        "id_evento": e["id_evento"],
        "titulo": e.get("titulo", "N/A"),
        "total_asistentes": counts.get(e["id_evento"], 0)
    } for e in (evs or [])], err

async def reporte_ingresos():
    evs, err = await cargar_eventos()
    inss, _ = await cargar_inscripciones()
    pgs, _ = await cargar_pagos()
    ev_map = {i["id_inscripcion"]: i.get("id_evento") for i in (inss or [])}
    totals, counts = {}, {}
    for p in (pgs or []):
        eid = ev_map.get(p.get("id_inscripcion"))
        if eid:
            totals[eid] = totals.get(eid, 0.0) + float(p.get("monto_pago") or 0)
            counts[eid] = counts.get(eid, 0) + 1
    return [{
        "id_evento": e["id_evento"],
        "titulo": e.get("titulo", "N/A"),
        "num_pagos": counts.get(e["id_evento"], 0),
        "total_ingresos": round(totals.get(e["id_evento"], 0.0), 2)
    } for e in (evs or [])], err

#El codigo funciona