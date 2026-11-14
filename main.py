import asyncio
import datetime
import flet as ft
import supabase_api as api

# Solo Dios entiende este codigo, agradecemos que el diseño sea claro

if not hasattr(ft, "ElevatedButton"):
    ft.ElevatedButton = getattr(ft, "Button", None)

if not hasattr(ft, "Button"):
    ft.Button = getattr(ft, "ElevatedButton", None)

if not hasattr(ft, "Alignment"):
    class _AlignmentWrapper:
        CENTER = getattr(ft.alignment, "center", None)
    ft.Alignment = _AlignmentWrapper

if not hasattr(ft, "Colors") and hasattr(ft, "colors"):
    ft.Colors = ft.colors

if not hasattr(ft, "Icons") and hasattr(ft, "icons"):
    ft.Icons = ft.icons

async def main(page: ft.Page):
    page.title = "Sistema de Gestión de Eventos - Equipo 3"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F0F2F5"
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    def msg(texto: str, error: bool = False):
        snack = ft.SnackBar(
            content=ft.Text(texto, color="#FFFFFF", weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.RED_700 if error else ft.Colors.GREEN_700,
            open=True
        )
        page.overlay.append(snack)
        page.update()

    # PERFIL USUARIO 
    def cargar_vista_usuario():
        lista_eventos = ft.GridView(expand=True, max_extent=380, spacing=20, run_spacing=20)

        # Campos del Asistente
        txt_nombre = ft.TextField(label="Nombre Completo", hint_text="Ej. Carlos Mendoza")
        txt_numero = ft.TextField(label="Teléfono", keyboard_type=ft.KeyboardType.NUMBER)
        txt_correo = ft.TextField(label="Correo Electrónico", hint_text="usuario@correo.com")

        # Campos del Pago
        txt_cantidad = ft.TextField(label="Cantidad de Entradas", value="1", keyboard_type=ft.KeyboardType.NUMBER)
        txt_monto = ft.TextField(label="Monto a Pagar ($)", value="150", keyboard_type=ft.KeyboardType.NUMBER)

        chk_forzar_error = ft.Switch(
            label="Simular ID Inexistente (Demostración Regla de Negocio)",
            value=False
        )

        lbl_user_error = ft.Text("", color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.BOLD, visible=False)
        evento_seleccionado = {"id": None, "titulo": ""}
        lbl_evento_info = ft.Text("", weight=ft.FontWeight.BOLD, color="#252B48")

        async def procesar_inscripcion(e):
            lbl_user_error.visible = False
            page.update()

            if not txt_nombre.value or not txt_numero.value or not txt_correo.value:
                lbl_user_error.value = "Por favor completa los datos del asistente"
                lbl_user_error.visible = True
                page.update()
                return
            if not txt_cantidad.value or not txt_monto.value:
                lbl_user_error.value = "Por favor completa los datos del pago"
                lbl_user_error.visible = True
                page.update()
                return

            try:
                numero_val = int(txt_numero.value)
                cantidad_val = int(txt_cantidad.value)
                monto_val = float(txt_monto.value)
            except ValueError:
                lbl_user_error.value = "Teléfono, cantidad y monto deben ser numéricos"
                lbl_user_error.visible = True
                page.update()
                return

            id_final_evento = 999999 if chk_forzar_error.value else evento_seleccionado["id"]

            asistente_data = {
                "nombre": txt_nombre.value.strip(),
                "numero": numero_val,
                "correo": txt_correo.value.strip()
            }
            pago_data = {
                "cantidad": cantidad_val,
                "monto_pago": monto_val
            }

            btn_confirmar.disabled = True
            btn_confirmar.text = "Procesando..."
            page.update()

            resultado, err = await api.registrar_inscripcion(id_final_evento, asistente_data, pago_data)

            btn_confirmar.disabled = False
            btn_confirmar.text = "Confirmar Inscripción y Pago"

            if err:
                lbl_user_error.value = err
                lbl_user_error.visible = True
                msg(err, error=True)
                page.update()
            else:
                lbl_user_error.visible = False
                msg(f"¡Inscripción y Pago registrados! (Ticket #{resultado['inscripcion']['id_inscripcion']})", error=False)
                dialog_inscripcion.open = False
                page.update()

        btn_confirmar = ft.Button("Confirmar Inscripción y Pago", on_click=lambda e: asyncio.create_task(procesar_inscripcion(e)))

        dialog_inscripcion = ft.AlertDialog(
            title=ft.Text("Inscripción y Pago al Evento"),
            content=ft.Container(
                width=450,
                content=ft.Column([
                    lbl_evento_info,
                    ft.Divider(),
                    ft.Text("Datos del Asistente", weight=ft.FontWeight.BOLD),
                    txt_nombre,
                    txt_numero,
                    txt_correo,
                    ft.Divider(),
                    ft.Text("Datos del Pago", weight=ft.FontWeight.BOLD),
                    ft.Row([txt_cantidad, txt_monto]),
                    ft.Divider(),
                    chk_forzar_error,
                    lbl_user_error
                ], tight=True, scroll=ft.ScrollMode.AUTO)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_inscripcion, "open", False) or page.update()),
                btn_confirmar
            ]
        )
        page.overlay.append(dialog_inscripcion)

        def abrir_modal_inscripcion(ev):
            evento_seleccionado["id"] = ev["id_evento"]
            evento_seleccionado["titulo"] = ev.get("titulo", "Evento")
            lbl_evento_info.value = f"Evento: {evento_seleccionado['titulo']} (ID: {evento_seleccionado['id']})"
            lbl_user_error.visible = False
            txt_nombre.value = ""
            txt_numero.value = ""
            txt_correo.value = ""
            txt_cantidad.value = "1"
            txt_monto.value = "150"
            chk_forzar_error.value = False
            dialog_inscripcion.open = True
            page.update()

        #El programa ya renderiza, ya me puedo retirar

        async def renderizar_cartelera():
            eventos, error_ev = await api.cargar_eventos()
            lugares, _ = await api.cargar_lugares()
            map_ponentes = await api.mapa_ponentes_por_evento()

            map_lugares = {}
            for lug in (lugares or []):
                id_lug = lug.get("id_Lugar") or lug.get("id_lugar")
                if id_lug is not None:
                    map_lugares[id_lug] = lug.get("Nombre", "Lugar")

            lista_eventos.controls.clear()

            if error_ev:
                lista_eventos.controls.append(ft.Text(f"Error al conectar con Supabase: {error_ev}", color=ft.Colors.RED_600))
                page.update()
                return

            if not eventos:
                lista_eventos.controls.append(ft.Text("No hay eventos disponibles en este momento."))
                page.update()
                return

            for ev in eventos:
                eid = ev.get("id_evento")
                nombre_lugar = map_lugares.get(ev.get("id_lugar"), f"Lugar #{ev.get('id_lugar', 'N/A')}")
                fecha_hora = ev.get("fecha y hora") or ev.get("fecha_y_hora") or "Por confirmar"
                
                # Ponentes asignados al evento
                ponentes_ev = map_ponentes.get(eid, [])
                texto_ponentes = " • ".join(ponentes_ev) if ponentes_ev else "Por confirmar"

                #Nunca supe resolver error, no experimentar mas por favor

                tarjeta = ft.Container(
                    bgcolor="#FFFFFF",
                    padding=20,
                    border_radius=12,
                    shadow=ft.BoxShadow(blur_radius=8, color="#0000001A", offset=ft.Offset(0, 2)),
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.EVENT, color="#4361EE"),
                            ft.Text(ev.get("titulo", "Evento Sin Título"), size=18, weight=ft.FontWeight.BOLD, expand=True)
                        ]),
                        ft.Divider(),
                        ft.Row([ft.Icon(ft.Icons.ACCESS_TIME, size=16, color="#666666"), ft.Text(f"Fecha: {fecha_hora}", color="#555555")]),
                        ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=16, color="#666666"), ft.Text(f"Lugar: {nombre_lugar}", color="#555555")]),
                        ft.Row([
                            ft.Icon(ft.Icons.RECORD_VOICE_OVER, size=16, color="#4361EE"),
                            ft.Text(f"Ponentes: {texto_ponentes}", color="#1E2235", weight=ft.FontWeight.W_500, expand=True)
                        ]),
                        ft.Container(height=10),
                        ft.Button(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color="#FFFFFF", size=18),
                                ft.Text("Inscribirme al Evento", color="#FFFFFF", weight=ft.FontWeight.BOLD)
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            bgcolor="#4361EE",
                            on_click=lambda e, item=ev: abrir_modal_inscripcion(item)
                        )
                    ])
                )
                lista_eventos.controls.append(tarjeta)

            page.update()

        asyncio.create_task(renderizar_cartelera())

        page.controls.clear()
        page.add(
            ft.Column([
                ft.Row([
                    ft.Text("Cartelera de Eventos", size=26, weight=ft.FontWeight.BOLD, color="#252B48"),
                    ft.TextButton("Cambiar Rol / Login", icon=ft.Icons.LOGOUT, on_click=lambda e: cargar_login())
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                lista_eventos
            ], expand=True)
        )
        page.update()

    # PERFIL ADMINISTRADOR 
    def cargar_vista_admin():
        pantalla_principal = ft.Container(expand=True, padding=20)


        #Asignacion ponentes
        #Si mueves aqui juro que te mato, el programa ya funciona 
        async def abrir_gestion_ponentes_evento(evento):
            eid = evento["id_evento"]
            titulo_ev = evento.get("titulo", f"Evento #{eid}")
            fecha_ev = str(evento.get("fecha y hora") or evento.get("fecha_y_hora") or "Por confirmar")
            
            lista_asignados = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            dd_ponentes = ft.Dropdown(label="Seleccionar Ponente", expand=True)
            lbl_asig_error = ft.Text("", color=ft.Colors.RED_600, size=12, visible=False, weight=ft.FontWeight.BOLD)

            badge_horario = ft.Container(
                bgcolor="#EEF2FF",
                padding=10,
                border_radius=8,
                border=ft.border.all(1, "#C7D2FE"),
                content=ft.Row([
                    ft.Icon(ft.Icons.SCHEDULE, color="#4361EE", size=20),
                    ft.Column([
                        ft.Text("Horario Sincronizado:", size=11, color="#4B5563"),
                        ft.Text(f"{fecha_ev}", size=13, weight=ft.FontWeight.BOLD, color="#1E2235")
                    ], spacing=2, expand=True)
                ])
            )

            async def recargar_asignados():
                asignados = await api.cargar_ponentes_por_evento(eid)
                lista_asignados.controls.clear()
                if not asignados:
                    lista_asignados.controls.append(ft.Text("No hay ponentes asignados a este evento aún.", italic=True, color="#6B7280"))
                else:
                    for p in asignados:
                        id_p = p["id_ponente"]
                        lista_asignados.controls.append(
                            ft.Container(
                                bgcolor="#F9FAFB", padding=10, border_radius=8,
                                border=ft.border.all(1, "#E5E7EB"),
                                content=ft.Row([
                                    ft.Icon(ft.Icons.MIC, color="#4361EE", size=20),
                                    ft.Column([
                                        ft.Text(f"{p['nombre']} ({p['especialidad']})", weight=ft.FontWeight.BOLD, color="#1E2235"),
                                        ft.Text(f"Horario Sincronizado: {p['hora']}", color="#4361EE", size=12, weight=ft.FontWeight.W_500)
                                    ], expand=True),
                                    ft.IconButton(
                                        ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_600, tooltip="Desvincular Ponente",
                                        on_click=lambda e, po=id_p, nom=p['nombre']: confirmar_desvincular(po, nom)
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            )
                        )
                
                # Opciones disponibles ey
                todos_ponentes, _ = await api.cargar_ponentes()
                ids_ya = {p["id_ponente"] for p in asignados}
                dd_ponentes.options = [
                    ft.dropdown.Option(str(po["id_ponente"]), f"{po['Nombre']} ({po.get('Especialidad', 'General')})")
                    for po in (todos_ponentes or []) if po["id_ponente"] not in ids_ya
                ]
                dd_ponentes.value = None
                page.update()

            def confirmar_desvincular(id_po, nombre_po):
                async def ejecutar_desvinculacion(e):
                    dialog_conf.open = False
                    page.update()
                    try:
                        _, err = await api.eliminar_evento_ponente(eid, id_po)
                        if err:
                            msg(f"Error al desvincular: {err}", error=True)
                        else:
                            msg(f"Ponente '{nombre_po}' desvinculado del evento")
                            await recargar_asignados()
                    except Exception as ex:
                        msg(f"Error inesperado al desvincular: {ex}", error=True)
                    #No planeo revisar los errores yo , asunto tuyo papi 


                dialog_conf = ft.AlertDialog(
                    title=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_600), ft.Text("Desvincular Ponente")]),
                    content=ft.Text(f"¿Deseas desvincular al ponente '{nombre_po}' de este evento?"),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_conf, "open", False) or page.update()),
                        ft.Button("Desvincular", bgcolor=ft.Colors.RED_600, color="#FFFFFF", on_click=lambda e: asyncio.create_task(ejecutar_desvinculacion(e)))
                    ]
                )
                page.overlay.append(dialog_conf)
                dialog_conf.open = True
                page.update()

            async def vincular_nuevo(e):
                lbl_asig_error.visible = False
                if not dd_ponentes.value:
                    lbl_asig_error.value = "Por favor selecciona un ponente de la lista"
                    lbl_asig_error.visible = True
                    page.update()
                    return

                btn_vincular.disabled = True
                btn_vincular.text = "Guardando..."
                page.update()

                _, err = await api.crear_evento_ponente({
                    "id_evento": eid,
                    "id_ponente": int(dd_ponentes.value),
                    "hora": fecha_ev
                })

                btn_vincular.disabled = False
                btn_vincular.text = "Asignar Ponente"

                if err:
                    lbl_asig_error.value = f"Error: {err}"
                    lbl_asig_error.visible = True
                    msg(f"Error: {err}", error=True)
                    page.update()
                else:
                    msg("¡Ponente asignado al evento en Supabase (Horario sincronizado)!", error=False)
                    await recargar_asignados()

            btn_vincular = ft.Button("Asignar Ponente", icon=ft.Icons.PERSON_ADD, on_click=lambda e: asyncio.create_task(vincular_nuevo(e)))

            dialog_gestion = ft.AlertDialog(
                title=ft.Text(f"Ponentes de: {titulo_ev} (Relación N:M)"),
                content=ft.Container(
                    width=540, height=440,
                    content=ft.Column([
                        ft.Text("Ponentes Asignados (Tabla evento_ponente)", weight=ft.FontWeight.BOLD, color="#1E2235"),
                        ft.Container(height=170, content=lista_asignados),
                        ft.Divider(),
                        ft.Text("Asignar Ponente", weight=ft.FontWeight.BOLD, color="#1E2235"),
                        dd_ponentes,
                        badge_horario,
                        lbl_asig_error,
                        ft.Row([btn_vincular], alignment=ft.MainAxisAlignment.END)
                    ], tight=True)
                ),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda e: setattr(dialog_gestion, "open", False) or page.update())
                ]
            )
            page.overlay.append(dialog_gestion)
            dialog_gestion.open = True
            page.update()
            await recargar_asignados()

        # VISTA ESPECIALIZADA: EVENTOS 
        # Esto funciona no lo muevas pls

        def crear_vista_eventos():
            tabla_contenedor = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            lbl_evento_error = ft.Text("", color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.BOLD, visible=False)

            eventos_cache = []
            categorias_cache = []
            lugares_cache = []
            map_pos_cache = {}

            txt_titulo = ft.TextField(label="Título del Evento", hint_text="Ej. Simposio de Inteligencia Artificial", expand=True)
            txt_fecha = ft.TextField(
                label="Fecha (YYYY-MM-DD)",
                value=datetime.date.today().strftime("%Y-%m-%d"),
                hint_text="YYYY-MM-DD",
                expand=True
            )

            horas_opciones = [f"{h:02d}:00" for h in range(7, 23)] + [f"{h:02d}:30" for h in range(7, 23)]
            horas_opciones.sort()
            dd_hora = ft.Dropdown(
                label="Hora",
                options=[ft.dropdown.Option(h) for h in horas_opciones],
                value="10:00",
                width=120
            )

            dd_categoria = ft.Dropdown(label="Categoría del Evento", expand=True)
            dd_lugar = ft.Dropdown(label="Lugar / Sede", expand=True)

            def on_date_change(e):
                if dp_fecha.value:
                    if hasattr(dp_fecha.value, "strftime"):
                        txt_fecha.value = dp_fecha.value.strftime("%Y-%m-%d")
                    else:
                        txt_fecha.value = str(dp_fecha.value).split("T")[0].split(" ")[0]
                    page.update()

            dp_fecha = ft.DatePicker(
                first_date=datetime.datetime(2020, 1, 1),
                last_date=datetime.datetime(2035, 12, 31),
                value=datetime.datetime.now(),
                on_change=on_date_change
            )

            def abrir_calendario(e):
                if dp_fecha not in page.overlay:
                    page.overlay.append(dp_fecha)
                dp_fecha.open = True
                page.update()

            btn_abrir_cal = ft.Button(
                "📅 Calendario",
                bgcolor="#4361EE",
                color="#FFFFFF",
                tooltip="Abrir selector de fecha interactivo",
                on_click=abrir_calendario
            )

            txt_buscar_ev = ft.TextField(
                hint_text="Buscar evento por título...",
                prefix_icon=ft.Icons.SEARCH,
                width=320,
                on_change=lambda e: renderizar_tabla_eventos()
            )

            def renderizar_tabla_eventos():
                map_cat = {c["id_categoria"]: c.get("Tipo", f"Cat #{c['id_categoria']}") for c in categorias_cache}
                map_lug = {(l.get("id_Lugar") or l.get("id_lugar")): l.get("Nombre", f"Lugar #{l.get('id_Lugar') or l.get('id_lugar')}") for l in lugares_cache}

                query = txt_buscar_ev.value.strip().lower() if txt_buscar_ev.value else ""
                filtrados = [
                    ev for ev in eventos_cache
                    if not query or query in str(ev.get("titulo", "")).lower() or query in map_cat.get(ev.get("id_categoria"), "").lower() or query in map_lug.get(ev.get("id_lugar"), "").lower()
                ]

                tabla_contenedor.controls.clear()
                if not filtrados:
                    msg_txt = "No se encontraron eventos coincidentes con la búsqueda." if query else "No hay eventos registrados. Haz clic en '+ Nuevo Evento' para registrar uno."
                    tabla_contenedor.controls.append(ft.Text(msg_txt, italic=True, color="#6B7280"))
                    page.update()
                    return

                filas = []
                for ev in filtrados:
                    eid = ev.get("id_evento")
                    titulo_ev = ev.get("titulo", "")
                    fecha_str = ev.get("fecha y hora") or ev.get("fecha_y_hora", "")
                    cat_nom = map_cat.get(ev.get("id_categoria"), f"ID {ev.get('id_categoria')}")
                    lug_nom = map_lug.get(ev.get("id_lugar"), f"ID {ev.get('id_lugar')}")
                    ponentes_list = map_pos_cache.get(eid, [])
                    ponentes_str = ", ".join(ponentes_list) if ponentes_list else "Sin ponentes confirmados"

                    filas.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(str(eid))),
                                ft.DataCell(ft.Text(titulo_ev, weight=ft.FontWeight.W_500)),
                                ft.DataCell(ft.Text(str(fecha_str))),
                                ft.DataCell(ft.Text(cat_nom)),
                                ft.DataCell(ft.Text(lug_nom)),
                                ft.DataCell(ft.Text(ponentes_str, color="#4361EE" if ponentes_list else "#6B7280")),
                                ft.DataCell(
                                    ft.Row([
                                        ft.IconButton(
                                            ft.Icons.RECORD_VOICE_OVER,
                                            icon_color="#4361EE",
                                            tooltip="Asignar / Gestionar Ponentes",
                                            on_click=lambda e, item=ev: asyncio.create_task(abrir_gestion_ponentes_evento(item))
                                        ),
                                        ft.IconButton(
                                            ft.Icons.EDIT_OUTLINED,
                                            icon_color="#3B82F6",
                                            tooltip="Editar Evento",
                                            on_click=lambda e, item=ev: asyncio.create_task(abrir_modal_editar_evento(item))
                                        ),
                                        ft.IconButton(
                                            ft.Icons.DELETE_OUTLINE,
                                            icon_color=ft.Colors.RED_600,
                                            tooltip="Eliminar Evento",
                                            on_click=lambda e, i=eid, t=titulo_ev: abrir_dialogo_eliminar_evento(i, t)
                                        )
                                    ], tight=True)
                                )
                            ]
                        )
                    )

                columnas = [
                    ft.DataColumn(ft.Text("ID", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Título del Evento", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Fecha y Hora", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Categoría", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Lugar / Sede", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Ponentes (Relación N:M)", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD))
                ]
                tabla_contenedor.controls = [ft.DataTable(columns=columnas, rows=filas, heading_row_color="#E9ECEF")]
                page.update()

            async def recargar():

                #No fue idea mia pero funciona, gracias

                nonlocal eventos_cache, categorias_cache, lugares_cache, map_pos_cache
                eventos, err_ev = await api.cargar_eventos()
                categorias, _ = await api.cargar_categorias()
                lugares, _ = await api.cargar_lugares()
                map_pos_cache = await api.mapa_ponentes_por_evento()

                eventos_cache = eventos or []
                categorias_cache = categorias or []
                lugares_cache = lugares or []

                dd_categoria.options = [
                    ft.dropdown.Option(str(c["id_categoria"]), f"{c['Tipo']} ({c.get('Descripción', '')})")
                    for c in categorias_cache
                ]
                if dd_categoria.options and not dd_categoria.value:
                    dd_categoria.value = dd_categoria.options[0].key

                dd_lugar.options = [
                    ft.dropdown.Option(str(l.get("id_Lugar") or l.get("id_lugar")), f"{l['Nombre']} (Cap: {l.get('Capacidad', 'N/A')})")
                    for l in lugares_cache
                ]
                if dd_lugar.options and not dd_lugar.value:
                    dd_lugar.value = dd_lugar.options[0].key

                if err_ev:
                    tabla_contenedor.controls.clear()
                    tabla_contenedor.controls.append(ft.Text(f"Error al consultar Supabase: {err_ev}", color=ft.Colors.RED_600))
                    page.update()
                    return

                renderizar_tabla_eventos()

            # Editar evento, viene en el documento, se tuvo que agregar
            async def abrir_modal_editar_evento(ev):
                eid = ev["id_evento"]
                lbl_edit_error = ft.Text("", color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.BOLD, visible=False)

                txt_edit_titulo = ft.TextField(label="Título del Evento", value=ev.get("titulo", ""), expand=True)

                raw_fecha = str(ev.get("fecha y hora") or ev.get("fecha_y_hora") or "")
                fecha_part = raw_fecha[:10] if len(raw_fecha) >= 10 else datetime.date.today().strftime("%Y-%m-%d")
                hora_part = raw_fecha[11:16] if len(raw_fecha) >= 16 else "10:00"

                txt_edit_fecha = ft.TextField(label="Fecha (YYYY-MM-DD)", value=fecha_part, expand=True)

                dd_edit_hora = ft.Dropdown(
                    label="Hora",
                    options=[ft.dropdown.Option(h) for h in horas_opciones],
                    value=hora_part if hora_part in horas_opciones else "10:00",
                    width=120
                )

                def on_edit_date_change(e):
                    if dp_edit_fecha.value:
                        if hasattr(dp_edit_fecha.value, "strftime"):
                            txt_edit_fecha.value = dp_edit_fecha.value.strftime("%Y-%m-%d")
                        else:
                            txt_edit_fecha.value = str(dp_edit_fecha.value).split("T")[0].split(" ")[0]
                        page.update()

                dp_edit_fecha = ft.DatePicker(
                    first_date=datetime.datetime(2020, 1, 1),
                    last_date=datetime.datetime(2035, 12, 31),
                    value=datetime.datetime.now(),
                    on_change=on_edit_date_change
                )

                def abrir_edit_calendario(e):
                    if dp_edit_fecha not in page.overlay:
                        page.overlay.append(dp_edit_fecha)
                    dp_edit_fecha.open = True
                    page.update()

                btn_edit_cal = ft.Button("📅", bgcolor="#4361EE", color="#FFFFFF", on_click=abrir_edit_calendario)

                #Pura fanforreneria, pero si ve bien el calendario 

                cats, _ = await api.cargar_categorias()
                lugs, _ = await api.cargar_lugares()

                dd_edit_cat = ft.Dropdown(
                    label="Categoría del Evento",
                    options=[ft.dropdown.Option(str(c["id_categoria"]), f"{c['Tipo']} ({c.get('Descripción', '')})") for c in (cats or [])],
                    value=str(ev.get("id_categoria", "")),
                    expand=True
                )
                dd_edit_lug = ft.Dropdown(
                    label="Lugar / Sede",
                    options=[ft.dropdown.Option(str(l.get("id_Lugar") or l.get("id_lugar")), f"{l['Nombre']} (Cap: {l.get('Capacidad', 'N/A')})") for l in (lugs or [])],
                    value=str(ev.get("id_lugar", "")),
                    expand=True
                )

                async def guardar_cambios_evento(e):

                    #No muevas ya funciona 

                    lbl_edit_error.visible = False
                    if not txt_edit_titulo.value.strip():
                        lbl_edit_error.value = "Por favor ingresa un título válido"
                        lbl_edit_error.visible = True
                        page.update()
                        return

                    hora_f = dd_edit_hora.value.strip() if dd_edit_hora.value else "10:00"
                    fecha_f = f"{txt_edit_fecha.value.strip()} {hora_f}:00"

                    btn_guardar_edit.disabled = True
                    btn_guardar_edit.text = "Guardando..."
                    page.update()

                    payload = {
                        "titulo": txt_edit_titulo.value.strip(),
                        "fecha y hora": fecha_f,
                        "id_categoria": int(dd_edit_cat.value),
                        "id_lugar": int(dd_edit_lug.value)
                    }

                    res, err = await api.actualizar_evento(eid, payload)
                    btn_guardar_edit.disabled = False
                    btn_guardar_edit.text = "Guardar Cambios"

                    if err:
                        lbl_edit_error.value = f"{err}"
                        lbl_edit_error.visible = True
                        msg(err, error=True)
                        page.update()
                    else:
                        msg(f"Evento '{txt_edit_titulo.value}' actualizado y ponentes sincronizados", error=False)
                        dialog_editar_ev.open = False
                        page.update()
                        await recargar()

                btn_guardar_edit = ft.Button("Guardar Cambios", bgcolor="#4361EE", color="#FFFFFF", on_click=lambda e: asyncio.create_task(guardar_cambios_evento(e)))

                dialog_editar_ev = ft.AlertDialog(
                    title=ft.Row([ft.Icon(ft.Icons.EDIT, color="#4361EE"), ft.Text(f"Editar Evento (ID: {eid})")]),
                    content=ft.Container(
                        width=480,
                        content=ft.Column([
                            txt_edit_titulo,
                            ft.Text("Fecha y Hora:", weight=ft.FontWeight.BOLD, size=13),
                            ft.Row([txt_edit_fecha, btn_edit_cal, dd_edit_hora]),
                            dd_edit_cat,
                            dd_edit_lug,
                            lbl_edit_error
                        ], tight=True, scroll=ft.ScrollMode.AUTO)
                    ),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_editar_ev, "open", False) or page.update()),
                        btn_guardar_edit
                    ]
                )
                page.overlay.append(dialog_editar_ev)
                dialog_editar_ev.open = True
                page.update()

            def abrir_dialogo_eliminar_evento(eid, nombre_ev):
                async def confirmar(e):
                    dialog_eliminar.open = False
                    page.update()
                    try:
                        _, err = await api.eliminar_evento(eid)
                        if err:
                            msg(f"Error al eliminar evento: {err}", error=True)
                        else:
                            msg(f"Evento '{nombre_ev}' eliminado correctamente", error=False)
                            await recargar()
                    except Exception as ex:
                        msg(f"Error inesperado al eliminar: {ex}", error=True)

                dialog_eliminar = ft.AlertDialog(
                    title=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_600), ft.Text("Confirmar Eliminación de Evento")]),
                    content=ft.Text(f"¿Estás seguro de que deseas eliminar permanentemente el evento '{nombre_ev}' (ID: {eid})?\n\nEsta acción eliminará automáticamente sus asignaciones de agenda, inscripciones y pagos asociados en cascada."),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_eliminar, "open", False) or page.update()),
                        ft.Button("Eliminar definitivamente", bgcolor=ft.Colors.RED_600, color="#FFFFFF", on_click=lambda e: asyncio.create_task(confirmar(e)))
                    ]
                )
                page.overlay.append(dialog_eliminar)
                dialog_eliminar.open = True
                page.update()

            async def guardar_evento(e):
                lbl_evento_error.visible = False
                if not txt_titulo.value or not txt_titulo.value.strip():
                    lbl_evento_error.value = "Por favor ingresa un título para el evento"
                    lbl_evento_error.visible = True
                    page.update()
                    return
                if not txt_fecha.value or not txt_fecha.value.strip():
                    lbl_evento_error.value = "Por favor selecciona una fecha con el calendario"
                    lbl_evento_error.visible = True
                    page.update()
                    return
                if not dd_categoria.value:
                    lbl_evento_error.value = "Por favor selecciona una categoría existente"
                    lbl_evento_error.visible = True
                    page.update()
                    return
                if not dd_lugar.value:
                    lbl_evento_error.value = "Por favor selecciona un lugar existente"
                    lbl_evento_error.visible = True
                    page.update()
                    return

                hora_val = dd_hora.value.strip() if dd_hora.value else "10:00"
                fecha_final = f"{txt_fecha.value.strip()} {hora_val}:00"

                btn_guardar_ev.disabled = True
                btn_guardar_ev.text = "Guardando..."
                page.update()

                payload = {
                    "titulo": txt_titulo.value.strip(),
                    "fecha y hora": fecha_final,
                    "id_categoria": int(dd_categoria.value),
                    "id_lugar": int(dd_lugar.value)
                }

                res, err = await api.crear_evento(payload)
                btn_guardar_ev.disabled = False
                btn_guardar_ev.text = "Guardar Evento"

                if err:
                    lbl_evento_error.value = f"{err}"
                    lbl_evento_error.visible = True
                    msg(err, error=True)
                    page.update()
                else:
                    msg("¡Evento registrado exitosamente en Supabase!", error=False)
                    dialog_nuevo_evento.open = False
                    page.update()
                    await recargar()

            btn_guardar_ev = ft.Button("Guardar Evento", icon=ft.Icons.SAVE, bgcolor="#4361EE", color="#FFFFFF", on_click=lambda e: asyncio.create_task(guardar_evento(e)))

            dialog_nuevo_evento = ft.AlertDialog(
                title=ft.Row([ft.Icon(ft.Icons.EVENT_AVAILABLE, color="#4361EE"), ft.Text("Nuevo Evento")]),
                content=ft.Container(
                    width=480,
                    content=ft.Column([
                        txt_titulo,
                        ft.Text("Fecha y Hora:", weight=ft.FontWeight.BOLD, size=13, color="#1E2235"),
                        ft.Row([txt_fecha, btn_abrir_cal, dd_hora], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        dd_categoria,
                        dd_lugar,
                        lbl_evento_error
                    ], tight=True, scroll=ft.ScrollMode.AUTO)
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_nuevo_evento, "open", False) or page.update()),
                    btn_guardar_ev
                ]
            )

            async def abrir_modal_nuevo_evento(e):
                lbl_evento_error.visible = False
                txt_titulo.value = ""
                txt_fecha.value = datetime.date.today().strftime("%Y-%m-%d")
                dd_hora.value = "10:00"

                cats, _ = await api.cargar_categorias()
                lugs, _ = await api.cargar_lugares()

                dd_categoria.options = [
                    ft.dropdown.Option(str(c["id_categoria"]), f"{c['Tipo']} ({c.get('Descripción', '')})")
                    for c in (cats or [])
                ]
                if dd_categoria.options:
                    dd_categoria.value = dd_categoria.options[0].key

                dd_lugar.options = [
                    ft.dropdown.Option(str(l.get("id_Lugar") or l.get("id_lugar")), f"{l['Nombre']} (Cap: {l.get('Capacidad', 'N/A')})")
                    for l in (lugs or [])
                ]
                if dd_lugar.options:
                    dd_lugar.value = dd_lugar.options[0].key

                if dialog_nuevo_evento not in page.overlay:
                    page.overlay.append(dialog_nuevo_evento)
                dialog_nuevo_evento.open = True
                page.update()

            asyncio.create_task(recargar())

            return ft.Column([
                ft.Row([
                    ft.Text("Eventos", size=24, weight=ft.FontWeight.BOLD, color="#1E2235"),
                    ft.Row([
                        txt_buscar_ev,
                        ft.IconButton(ft.Icons.REFRESH, tooltip="Actualizar lista", on_click=lambda e: asyncio.create_task(recargar())),
                        ft.Button("Nuevo Evento", icon=ft.Icons.ADD, bgcolor="#4361EE", color="#FFFFFF", on_click=lambda e: asyncio.create_task(abrir_modal_nuevo_evento(e)))
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(
                    bgcolor="#FFFFFF",
                    padding=15,
                    border_radius=10,
                    expand=True,
                    content=ft.Row([tabla_contenedor], scroll=ft.ScrollMode.ALWAYS, expand=True)
                )
            ], expand=True)

     
        # Vistas Crud y borrar

        def crear_vista_crud(titulo, cargar_fn, crear_fn, eliminar_fn, columnas, campos_form, map_row, actualizar_fn=None):
            tabla_contenedor = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            lbl_dialog_error = ft.Text("", color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.BOLD, visible=False)
            form_inputs = {}
            edit_inputs = {}
            datos_cache = []

            for item in campos_form:
                label = item[0]
                key = item[1]
                tipo_o_opts = item[2]
                if isinstance(tipo_o_opts, list):
                    form_inputs[key] = ft.Dropdown(
                        label=label,
                        options=[ft.dropdown.Option(opt_val, opt_txt) for opt_val, opt_txt in tipo_o_opts],
                        value=tipo_o_opts[0][0] if tipo_o_opts else None,
                        expand=True
                    )
                    edit_inputs[key] = ft.Dropdown(
                        label=label,
                        options=[ft.dropdown.Option(opt_val, opt_txt) for opt_val, opt_txt in tipo_o_opts],
                        value=tipo_o_opts[0][0] if tipo_o_opts else None,
                        expand=True
                    )
                else:
                    form_inputs[key] = ft.TextField(
                        label=label,
                        keyboard_type=ft.KeyboardType.NUMBER if tipo_o_opts in (int, float) else ft.KeyboardType.TEXT
                    )
                    edit_inputs[key] = ft.TextField(
                        label=label,
                        keyboard_type=ft.KeyboardType.NUMBER if tipo_o_opts in (int, float) else ft.KeyboardType.TEXT
                    )

            txt_buscar_crud = ft.TextField(
                hint_text=f"Buscar en {titulo}...",
                prefix_icon=ft.Icons.SEARCH,
                width=300,
                on_change=lambda e: renderizar_tabla()
            )

            def renderizar_tabla():
                query = txt_buscar_crud.value.strip().lower() if txt_buscar_crud.value else ""
                tabla_contenedor.controls.clear()

                filtrados = [
                    d for d in datos_cache
                    if not query or any(query in str(v).lower() for v in d.values() if v is not None)
                ]

                if not filtrados:
                    msg_txt = "No hay registros que coincidan con la búsqueda." if query else f"No hay registros en {titulo}."
                    tabla_contenedor.controls.append(ft.Text(msg_txt, italic=True, color="#6B7280"))
                    page.update()
                    return

                filas = []
                for d in filtrados:
                    valores = map_row(d)
                    id_val = valores[0]
                    nombre_rep = str(valores[1] if len(valores) > 1 else id_val)

                    acciones_fila = []
                    if actualizar_fn:
                        acciones_fila.append(
                            ft.IconButton(
                                ft.Icons.EDIT_OUTLINED,
                                icon_color="#3B82F6",
                                tooltip="Editar registro",
                                on_click=lambda e, item=d: abrir_dialogo_editar(item)
                            )
                        )
                    acciones_fila.append(
                        ft.IconButton(
                            ft.Icons.DELETE_OUTLINE,
                            icon_color=ft.Colors.RED_600,
                            tooltip="Eliminar registro",
                            on_click=lambda e, i=id_val, n=nombre_rep: abrir_dialogo_eliminar(i, n)
                        )
                    )

                    filas.append(
                        ft.DataRow(
                            cells=[ft.DataCell(ft.Text(str(val if val is not None else ""))) for val in valores] + [
                                ft.DataCell(ft.Row(acciones_fila, tight=True))
                            ]
                        )
                    )

                columnas_datatable = [ft.DataColumn(ft.Text(c, weight=ft.FontWeight.BOLD)) for c in columnas] + [
                    ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD))
                ]
                tabla_contenedor.controls = [
                    ft.DataTable(columns=columnas_datatable, rows=filas, heading_row_color="#E9ECEF")
                ]
                page.update()

            async def recargar():

                #Recargar 

                nonlocal datos_cache
                datos, error = await cargar_fn()
                if error:
                    tabla_contenedor.controls.clear()
                    tabla_contenedor.controls.append(ft.Text(f"Error al consultar Supabase: {error}", color=ft.Colors.RED_600))
                    page.update()
                    return

                datos_cache = datos or []
                renderizar_tabla()

            def abrir_dialogo_eliminar(id_val, nombre_item):
                async def confirmar(e):
                    dialog_eliminar.open = False
                    page.update()
                    try:
                        id_to_del = int(id_val) if (isinstance(id_val, str) and id_val.isdigit()) else id_val
                        res, err = await eliminar_fn(id_to_del)
                        if err:
                            msg(f"Error al eliminar: {err}", error=True)
                        else:
                            msg("Registro eliminado correctamente", error=False)
                            await recargar()
                    except Exception as ex:
                        msg(f"Error al eliminar: {ex}", error=True)

                dialog_eliminar = ft.AlertDialog(
                    title=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_600), ft.Text(f"Eliminar en {titulo}")]),
                    content=ft.Text(f"¿Estás seguro de que deseas eliminar permanentemente '{nombre_item}' (ID: {id_val})?\n\nEsta acción eliminará también sus dependencias asociadas en cascada."),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_eliminar, "open", False) or page.update()),
                        ft.Button("Eliminar definitivamente", bgcolor=ft.Colors.RED_600, color="#FFFFFF", on_click=lambda e: asyncio.create_task(confirmar(e)))
                    ]
                )
                page.overlay.append(dialog_eliminar)
                dialog_eliminar.open = True
                page.update()

            # Modal de EDICIÓN
            lbl_edit_error = ft.Text("", color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.BOLD, visible=False)
            id_editando = {"id": None}

            async def guardar_edicion(e):
                lbl_edit_error.visible = False
                btn_guardar_edit.disabled = True
                btn_guardar_edit.text = "Guardando..."
                page.update()

                datos_payload = {}
                for item in campos_form:
                    key = item[1]
                    tipo_o_opts = item[2]
                    val = edit_inputs[key].value
                    if val is not None and str(val).strip() != "":
                        val_str = str(val).strip()
                        if isinstance(tipo_o_opts, list) or tipo_o_opts == int:
                            try:
                                datos_payload[key] = int(val_str)
                            except ValueError:
                                datos_payload[key] = val_str
                        elif tipo_o_opts == float:
                            try:
                                datos_payload[key] = float(val_str)
                            except ValueError:
                                datos_payload[key] = val_str
                        else:
                            datos_payload[key] = val_str

                res, err = await actualizar_fn(id_editando["id"], datos_payload)
                btn_guardar_edit.disabled = False
                btn_guardar_edit.text = "Guardar Cambios"

                if err:
                    lbl_edit_error.value = str(err)
                    lbl_edit_error.visible = True
                    msg(err, error=True)
                    page.update()
                else:
                    msg(f"{titulo} actualizado exitosamente", error=False)
                    dialog_editar.open = False
                    page.update()
                    await recargar()

            btn_guardar_edit = ft.Button("Guardar Cambios", bgcolor="#4361EE", color="#FFFFFF", on_click=lambda e: asyncio.create_task(guardar_edicion(e)))

            dialog_editar = ft.AlertDialog(
                title=ft.Row([ft.Icon(ft.Icons.EDIT, color="#4361EE"), ft.Text(f"Editar en {titulo}")]),
                content=ft.Container(
                    width=440,
                    content=ft.Column(list(edit_inputs.values()) + [lbl_edit_error], tight=True, scroll=ft.ScrollMode.AUTO)
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_editar, "open", False) or page.update()),
                    btn_guardar_edit
                ]
            )

            def abrir_dialogo_editar(item):
                lbl_edit_error.visible = False
                # Detectar ID primario del item
                valores = map_row(item)
                id_editando["id"] = valores[0]
                for k in edit_inputs:
                    val_actual = item.get(k)
                    if isinstance(edit_inputs[k], ft.Dropdown):
                        edit_inputs[k].value = str(val_actual) if val_actual is not None else None
                    else:
                        edit_inputs[k].value = str(val_actual) if val_actual is not None else ""
                if dialog_editar not in page.overlay:
                    page.overlay.append(dialog_editar)
                dialog_editar.open = True
                page.update()

            async def guardar(e):
                lbl_dialog_error.visible = False
                btn_guardar.disabled = True
                btn_guardar.text = "Guardando..."
                page.update()

                datos_payload = {}
                for item in campos_form:
                    key = item[1]
                    tipo_o_opts = item[2]
                    val = form_inputs[key].value
                    if val is not None and str(val).strip() != "":
                        val_str = str(val).strip()
                        if isinstance(tipo_o_opts, list) or tipo_o_opts == int:
                            try:
                                datos_payload[key] = int(val_str)
                            except ValueError:
                                datos_payload[key] = val_str
                        elif tipo_o_opts == float:
                            try:
                                datos_payload[key] = float(val_str)
                            except ValueError:
                                datos_payload[key] = val_str
                        else:
                            datos_payload[key] = val_str

                res, err = await crear_fn(datos_payload)

                btn_guardar.disabled = False
                btn_guardar.text = "Guardar"

                if err:
                    lbl_dialog_error.value = f"{err}"
                    lbl_dialog_error.visible = True
                    msg(err, error=True)
                    page.update()
                else:
                    lbl_dialog_error.visible = False
                    msg(f"{titulo} guardado exitosamente", error=False)
                    dialog_nuevo.open = False
                    page.update()
                    await recargar()

            btn_guardar = ft.Button("Guardar", on_click=lambda e: asyncio.create_task(guardar(e)))

            dialog_nuevo = ft.AlertDialog(
                title=ft.Text(f"Nuevo Registro en {titulo}"),
                content=ft.Container(
                    width=420,
                    content=ft.Column(list(form_inputs.values()) + [lbl_dialog_error], tight=True, scroll=ft.ScrollMode.AUTO)
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_nuevo, "open", False) or page.update()),
                    btn_guardar
                ]
            )

            def abrir_dialogo_nuevo(e):
                lbl_dialog_error.visible = False
                for k in form_inputs:
                    if isinstance(form_inputs[k], ft.Dropdown):
                        opts = form_inputs[k].options
                        form_inputs[k].value = opts[0].key if opts else None
                    else:
                        form_inputs[k].value = ""
                if dialog_nuevo not in page.overlay:
                    page.overlay.append(dialog_nuevo)
                dialog_nuevo.open = True
                page.update()

            asyncio.create_task(recargar())

            return ft.Column([
                ft.Row([
                    ft.Text(titulo, size=24, weight=ft.FontWeight.BOLD, color="#1E2235"),
                    ft.Row([
                        txt_buscar_crud,
                        ft.IconButton(ft.Icons.REFRESH, tooltip="Actualizar", on_click=lambda e: asyncio.create_task(recargar())),
                        ft.Button("Nuevo", icon=ft.Icons.ADD, on_click=abrir_dialogo_nuevo)
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(
                    bgcolor="#FFFFFF",
                    padding=15,
                    border_radius=10,
                    expand=True,
                    content=ft.Row([tabla_contenedor], scroll=ft.ScrollMode.ALWAYS, expand=True)
                )
            ], expand=True)

        # VISTA AGENDA 
        def crear_vista_agenda():
            tabla_contenedor = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
            lbl_agenda_error = ft.Text("", color=ft.Colors.RED_600, size=13, weight=ft.FontWeight.BOLD, visible=False)
            
            dd_evento = ft.Dropdown(label="Seleccionar Evento", expand=True)
            dd_ponente = ft.Dropdown(label="Seleccionar Ponente", expand=True)
            
            badge_hora_agenda = ft.Container(
                bgcolor="#EEF2FF",
                padding=10,
                border_radius=8,
                border=ft.border.all(1, "#C7D2FE"),
                content=ft.Row([
                    ft.Icon(ft.Icons.SCHEDULE, color="#4361EE", size=18),
                    ft.Column([
                        ft.Text("Horario Sincronizado:", size=11, color="#4B5563"),
                        ft.Text("Selecciona un evento para ver su horario", size=12, color="#1E2235", weight=ft.FontWeight.BOLD)
                    ], spacing=2, expand=True)
                ])
            )

            map_fechas_eventos = {}

            def on_evento_change(e):
                if dd_evento.value and int(dd_evento.value) in map_fechas_eventos:
                    f = map_fechas_eventos[int(dd_evento.value)]
                    badge_hora_agenda.content.controls[1].controls[1].value = str(f)
                else:
                    badge_hora_agenda.content.controls[1].controls[1].value = "Selecciona un evento"
                page.update()

            dd_evento.on_change = on_evento_change

            async def recargar():
                nonlocal map_fechas_eventos
                datos, err = await api.cargar_evento_ponente()
                eventos, _ = await api.cargar_eventos()
                ponentes, _ = await api.cargar_ponentes()

                map_eventos = {e["id_evento"]: e.get("titulo", "") for e in (eventos or [])}
                map_fechas_eventos = {e["id_evento"]: (e.get("fecha y hora") or e.get("fecha_y_hora") or "Por confirmar") for e in (eventos or [])}
                map_ponentes = {p["id_ponente"]: p for p in (ponentes or [])}

                dd_evento.options = [ft.dropdown.Option(str(e["id_evento"]), e.get("titulo", f"Evento #{e['id_evento']}")) for e in (eventos or [])]
                dd_ponente.options = [ft.dropdown.Option(str(p["id_ponente"]), f"{p['Nombre']} ({p.get('Especialidad', 'General')})") for p in (ponentes or [])]

                tabla_contenedor.controls.clear()
                if err:
                    tabla_contenedor.controls.append(ft.Text(f"Error: {err}", color=ft.Colors.RED_600))
                    page.update()
                    return

                if not datos:
                    tabla_contenedor.controls.append(ft.Text("No hay asignaciones en evento_ponente."))
                    page.update()
                    return

                filas = []
                for d in datos:
                    id_ev = d.get("id_evento")
                    id_po = d.get("id_ponente")
                    hora_val = str(d.get("hora", "")).replace("T", " ")
                    nombre_ev = map_eventos.get(id_ev, f"Evento #{id_ev}")
                    p_obj = map_ponentes.get(id_po, {})
                    nombre_po = p_obj.get("Nombre", f"Ponente #{id_po}")
                    esp_po = p_obj.get("Especialidad", "General")

                    filas.append(
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(nombre_ev)),
                            ft.DataCell(ft.Text(nombre_po)),
                            ft.DataCell(ft.Text(esp_po)),
                            ft.DataCell(ft.Text(str(hora_val))),
                            ft.DataCell(
                                ft.IconButton(
                                    ft.Icons.DELETE_OUTLINE,
                                    icon_color=ft.Colors.RED_600,
                                    tooltip="Desvincular",
                                    on_click=lambda e, ev=id_ev, po=id_po, nev=nombre_ev, npo=nombre_po: confirmar_borrar(ev, po, nev, npo)
                                )
                            )
                        ])
                    )

                columnas = [
                    ft.DataColumn(ft.Text("Evento", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Ponente", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Especialidad", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Fecha y Hora Sincronizada", weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD))
                ]
                tabla_contenedor.controls = [ft.DataTable(columns=columnas, rows=filas, heading_row_color="#E9ECEF")]
                page.update()

            def confirmar_borrar(id_ev, id_po, nom_ev, nom_po):

                #Dios no puedes repetir , el mismo codigo ¿Porque no funciono antes?

                async def ejecutar_borrado(e):
                    dialog_del.open = False
                    page.update()
                    try:
                        _, err = await api.eliminar_evento_ponente(id_ev, id_po)
                        if err:
                            msg(f"Error al desvincular: {err}", error=True)
                        else:
                            msg(f"Asignación de '{nom_po}' en '{nom_ev}' eliminada", error=False)
                            await recargar()
                    except Exception as ex:
                        msg(f"Error inesperado al desvincular: {ex}", error=True)

                dialog_del = ft.AlertDialog(
                    title=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.RED_600), ft.Text("Confirmar Desvinculación")]),
                    content=ft.Text(f"¿Deseas desvincular al ponente '{nom_po}' del evento '{nom_ev}'?"),
                    actions=[
                        ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_del, "open", False) or page.update()),
                        ft.Button("Desvincular", bgcolor=ft.Colors.RED_600, color="#FFFFFF", on_click=lambda e: asyncio.create_task(ejecutar_borrado(e)))
                    ]
                )
                page.overlay.append(dialog_del)
                dialog_del.open = True
                page.update()

            async def guardar(e):

                # Guarda

                lbl_agenda_error.visible = False
                if not dd_evento.value or not dd_ponente.value:
                    lbl_agenda_error.value = "Selecciona Evento y Ponente"
                    lbl_agenda_error.visible = True
                    page.update()
                    return

                btn_guardar_agenda.disabled = True
                btn_guardar_agenda.text = "Guardando..."
                page.update()

                eid = int(dd_evento.value)
                horario_evento = map_fechas_eventos.get(eid, "10:00")

                payload = {
                    "id_evento": eid,
                    "id_ponente": int(dd_ponente.value),
                    "hora": horario_evento
                }
                _, err = await api.crear_evento_ponente(payload)

                btn_guardar_agenda.disabled = False
                btn_guardar_agenda.text = "Guardar Asignación"

                if err:
                    lbl_agenda_error.value = f"{err}"
                    lbl_agenda_error.visible = True
                    msg(err, error=True)
                    page.update()
                else:
                    lbl_agenda_error.visible = False
                    msg("Ponente asignado al evento con horario sincronizado automáticamente", error=False)
                    dialog_agenda.open = False
                    page.update()
                    await recargar()

            btn_guardar_agenda = ft.Button("Guardar Asignación", on_click=lambda e: asyncio.create_task(guardar(e)))

            dialog_agenda = ft.AlertDialog(
                title=ft.Text("Asignación de Agenda (N:M)"),
                content=ft.Container(
                    width=460,
                    content=ft.Column([
                        dd_evento,
                        dd_ponente,
                        badge_hora_agenda,
                        lbl_agenda_error
                    ], tight=True)
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog_agenda, "open", False) or page.update()),
                    btn_guardar_agenda
                ]
            )

            def abrir_dialogo(e):
                lbl_agenda_error.visible = False
                dd_evento.value = None
                dd_ponente.value = None
                badge_hora_agenda.content.controls[1].controls[1].value = "Selecciona un evento para ver su horario"
                if dialog_agenda not in page.overlay:
                    page.overlay.append(dialog_agenda)
                dialog_agenda.open = True
                page.update()

            asyncio.create_task(recargar())

            return ft.Column([
                ft.Row([
                    ft.Text("Agenda (Relación N:M: evento_ponente)", size=24, weight=ft.FontWeight.BOLD, color="#1E2235"),
                    ft.Button("Nueva Asignación", icon=ft.Icons.ADD, on_click=abrir_dialogo)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Container(
                    bgcolor="#FFFFFF",
                    padding=15,
                    border_radius=10,
                    expand=True,
                    content=ft.Row([tabla_contenedor], scroll=ft.ScrollMode.ALWAYS, expand=True)
                )
            ], expand=True)

        # VISTA DE REPORTES SQL 
        def crear_vista_reportes():
            tabla_rep1 = ft.Column(scroll=ft.ScrollMode.AUTO)
            tabla_rep2 = ft.Column(scroll=ft.ScrollMode.AUTO)
            tabla_rep3 = ft.Column(scroll=ft.ScrollMode.AUTO)

            rep1_cache = []
            rep2_cache = []
            rep3_cache = []

            txt_filtro_rep = ft.TextField(
                hint_text="Filtrar reportes por nombre o palabra clave...",
                prefix_icon=ft.Icons.SEARCH,
                width=340,
                on_change=lambda e: renderizar_reportes()
            )

            def renderizar_reportes():
                q = txt_filtro_rep.value.strip().lower() if txt_filtro_rep.value else ""

                # Reporte 1
                f1 = [r for r in rep1_cache if not q or q in str(r.get("evento", "")).lower() or q in str(r.get("ponente", "")).lower() or q in str(r.get("especialidad", "")).lower()]
                tabla_rep1.controls.clear()
                if not f1:
                    tabla_rep1.controls.append(ft.Text("Sin registros que coincidan.", italic=True, color="#6B7280"))
                else:
                    filas1 = [
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(r["evento"])),
                            ft.DataCell(ft.Text(r["ponente"])),
                            ft.DataCell(ft.Text(r["especialidad"])),
                            ft.DataCell(ft.Text(str(r["hora"])))
                        ]) for r in f1
                    ]
                    cols1 = [
                        ft.DataColumn(ft.Text("Evento", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Ponente", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Especialidad", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Hora Sincronizada", weight=ft.FontWeight.BOLD))
                    ]
                    tabla_rep1.controls = [ft.DataTable(columns=cols1, rows=filas1, heading_row_color="#E9ECEF")]

                # Reporte 2
                f2 = [r for r in rep2_cache if not q or q in str(r.get("titulo", "")).lower() or q in str(r.get("id_evento", "")).lower()]
                tabla_rep2.controls.clear()
                if not f2:
                    tabla_rep2.controls.append(ft.Text("Sin registros que coincidan.", italic=True, color="#6B7280"))
                else:
                    filas2 = [
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(r["id_evento"]))),
                            ft.DataCell(ft.Text(r["titulo"])),
                            ft.DataCell(ft.Text(str(r["total_asistentes"])))
                        ]) for r in f2
                    ]
                    cols2 = [
                        ft.DataColumn(ft.Text("ID Evento", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Título del Evento", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Total Asistentes Inscritos", weight=ft.FontWeight.BOLD))
                    ]
                    tabla_rep2.controls = [ft.DataTable(columns=cols2, rows=filas2, heading_row_color="#E9ECEF")]

                # Reporte 3
                f3 = [r for r in rep3_cache if not q or q in str(r.get("titulo", "")).lower() or q in str(r.get("id_evento", "")).lower()]
                tabla_rep3.controls.clear()
                if not f3:
                    tabla_rep3.controls.append(ft.Text("Sin registros que coincidan.", italic=True, color="#6B7280"))
                else:
                    filas3 = [
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(str(r["id_evento"]))),
                            ft.DataCell(ft.Text(r["titulo"])),
                            ft.DataCell(ft.Text(str(r["num_pagos"]))),
                            ft.DataCell(ft.Text(f"${r['total_ingresos']:.2f}"))
                        ]) for r in f3
                    ]
                    cols3 = [
                        ft.DataColumn(ft.Text("ID Evento", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Título del Evento", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Transacciones", weight=ft.FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Total Ingresos ($)", weight=ft.FontWeight.BOLD))
                    ]
                    tabla_rep3.controls = [ft.DataTable(columns=cols3, rows=filas3, heading_row_color="#E9ECEF")]

                page.update()

            async def cargar_todos_reportes():
                nonlocal rep1_cache, rep2_cache, rep3_cache
                d1, _ = await api.reporte_agenda()
                d2, _ = await api.reporte_ocupacion()
                d3, _ = await api.reporte_ingresos()

                rep1_cache = d1 or []
                rep2_cache = d2 or []
                rep3_cache = d3 or []

                renderizar_reportes()

            asyncio.create_task(cargar_todos_reportes())

            return ft.Column([
                ft.Row([
                    ft.Text("Reportes", size=24, weight=ft.FontWeight.BOLD, color="#1E2235"),
                    ft.Row([
                        txt_filtro_rep,
                        ft.Button("Actualizar", icon=ft.Icons.REFRESH, on_click=lambda e: asyncio.create_task(cargar_todos_reportes()))
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Column([
                    ft.Container(
                        bgcolor="#FFFFFF", padding=15, border_radius=10,
                        content=ft.Column([
                            ft.Text("Reporte 1: Agenda (JOIN N:M: Evento ↔ Ponente)", size=16, weight=ft.FontWeight.BOLD, color="#4361EE"),
                            ft.Row([tabla_rep1], scroll=ft.ScrollMode.ALWAYS)
                        ])
                    ),
                    ft.Container(
                        bgcolor="#FFFFFF", padding=15, border_radius=10,
                        content=ft.Column([
                            ft.Text("Reporte 2: Ocupación por Evento (COUNT)", size=16, weight=ft.FontWeight.BOLD, color="#4361EE"),
                            ft.Row([tabla_rep2], scroll=ft.ScrollMode.ALWAYS)
                        ])
                    ),
                    ft.Container(
                        bgcolor="#FFFFFF", padding=15, border_radius=10,
                        content=ft.Column([
                            ft.Text("Reporte 3: Ingresos por Evento (SUM)", size=16, weight=ft.FontWeight.BOLD, color="#4361EE"),
                            ft.Row([tabla_rep3], scroll=ft.ScrollMode.ALWAYS)
                        ])
                    ),
                ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=15)
            ], expand=True)

        def cambiar_modulo(nombre):
            if nombre == "Eventos":
                pantalla_principal.content = crear_vista_eventos()
            elif nombre == "Ponentes":
                pantalla_principal.content = crear_vista_crud(
                    "Ponentes",
                    api.cargar_ponentes,
                    api.crear_ponente,
                    api.eliminar_ponente,
                    ["ID", "Nombre", "Edad", "Sexo", "Teléfono", "Correo", "Identificación", "Especialidad"],
                    [
                        ("Nombre Completo", "Nombre", str),
                        ("Edad", "Edad", int),
                        ("Sexo", "Sexo", [("1", "1 - Masculino"), ("2", "2 - Femenino")]),
                        ("Teléfono", "Telefono", int),
                        ("Correo Electrónico", "Correo", str),
                        ("Identificación", "Identificacion", str),
                        ("Especialidad", "Especialidad", str)
                    ],
                    lambda d: [
                        d.get("id_ponente", ""),
                        d.get("Nombre", ""),
                        d.get("Edad", ""),
                        "Masculino (1)" if str(d.get("Sexo")) == "1" else ("Femenino (2)" if str(d.get("Sexo")) == "2" else d.get("Sexo", "")),
                        d.get("Telefono", ""),
                        d.get("Correo", ""),
                        d.get("Identificacion", ""),
                        d.get("Especialidad", "")
                    ],
                    actualizar_fn=api.actualizar_ponente
                )
            elif nombre == "Asistentes":
                pantalla_principal.content = crear_vista_crud(
                    "Asistentes",
                    api.cargar_asistentes,
                    api.crear_asistente,
                    api.eliminar_asistente,
                    ["ID", "Nombre", "Teléfono / Número", "Correo Electrónico"],
                    [
                        ("Nombre Completo", "nombre", str),
                        ("Teléfono / Número", "numero", int),
                        ("Correo Electrónico", "correo", str)
                    ],
                    lambda d: [
                        d.get("id_asistentes", ""),
                        d.get("nombre", ""),
                        d.get("numero", ""),
                        d.get("correo", "")
                    ],
                    actualizar_fn=api.actualizar_asistente
                )
            elif nombre == "Lugares":
                pantalla_principal.content = crear_vista_crud(
                    "Lugares / Sedes",
                    api.cargar_lugares,
                    api.crear_lugar,
                    api.eliminar_lugar,
                    ["ID", "Nombre de Sede", "Capacidad", "Dirección"],
                    [
                        ("Nombre de la Sede", "Nombre", str),
                        ("Capacidad", "Capacidad", int),
                        ("Dirección / Ubicación", "Dirección", str)
                    ],
                    lambda d: [
                        d.get("id_Lugar") or d.get("id_lugar", ""),
                        d.get("Nombre", ""),
                        d.get("Capacidad", ""),
                        d.get("Dirección") or d.get("Direccion", "")
                    ],
                    actualizar_fn=api.actualizar_lugar
                )
            elif nombre == "Categorías":
                pantalla_principal.content = crear_vista_crud(
                    "Categorías",
                    api.cargar_categorias,
                    api.crear_categoria,
                    api.eliminar_categoria,
                    ["ID", "Tipo / Nombre", "Descripción"],
                    [
                        ("Tipo de Categoría", "Tipo", str),
                        ("Descripción", "Descripción", str)
                    ],
                    lambda d: [
                        d.get("id_categoria", ""),
                        d.get("Tipo", ""),
                        d.get("Descripción") or d.get("Descripcion", "")
                    ],
                    actualizar_fn=api.actualizar_categoria
                )
            elif nombre in ("Agenda", "Agenda (N:M)"):
                pantalla_principal.content = crear_vista_agenda()
            elif nombre == "Reportes":
                pantalla_principal.content = crear_vista_reportes()

            page.update()

        sidebar = ft.Container(
            width=230,
            bgcolor="#1E2235",
            padding=15,
            border_radius=12,
            content=ft.Column([
                ft.Text("ADMINISTRACIÓN", color="#FFFFFF", weight=ft.FontWeight.BOLD, size=18),
                ft.Divider(color="#3D4566"),
                *[
                    ft.Container(
                        content=ft.Row([ft.Icon(icono, color="#FFFFFF", size=20), ft.Text(texto, color="#FFFFFF")]),
                        padding=10,
                        border_radius=8,
                        ink=True,
                        on_click=lambda e, m=texto: cambiar_modulo(m)
                    )
                    for icono, texto in [
                        (ft.Icons.EVENT, "Eventos"),
                        (ft.Icons.RECORD_VOICE_OVER, "Ponentes"),
                        (ft.Icons.PEOPLE, "Asistentes"),
                        (ft.Icons.SHARE, "Agenda (N:M)"),
                        (ft.Icons.LOCATION_ON, "Lugares"),
                        (ft.Icons.CATEGORY, "Categorías"),
                        (ft.Icons.BAR_CHART, "Reportes")
                    ]
                ],
                ft.Divider(color="#3D4566"),
                ft.Container(
                    content=ft.Row([ft.Icon(ft.Icons.LOGOUT, color="#FF6B6B", size=20), ft.Text("Cerrar Sesión", color="#FF6B6B")]),
                    padding=10,
                    border_radius=8,
                    ink=True,
                    on_click=lambda e: cargar_login()
                )
            ])
        )

        cambiar_modulo("Eventos")
        page.controls.clear()
        page.add(ft.Row([sidebar, pantalla_principal], expand=True, vertical_alignment=ft.CrossAxisAlignment.START))
        page.update()

    # LOGIN 
    # De nuevo estas repitiendo
    def cargar_login():
        page.controls.clear()
        page.add(
            ft.Container(
                expand=True,
                alignment=getattr(ft.Alignment, "CENTER", ft.Alignment(0, 0)),
                content=ft.Container(
                    width=480,
                    padding=35,
                    bgcolor="#FFFFFF",
                    border_radius=16,
                    shadow=ft.BoxShadow(blur_radius=15, color="#00000015", offset=ft.Offset(0, 4)),
                    content=ft.Column([
                        ft.Icon(ft.Icons.PERSON, size=70, color="#4361EE"),
                        ft.Text("Organización de Eventos", size=28, weight=ft.FontWeight.BOLD, color="#1E2235"),
                        ft.Divider(height=20),
                        ft.Button(
                            "Cliente",
                            icon=ft.Icons.PERSON,
                            width=380,
                            style=ft.ButtonStyle(padding=15, bgcolor="#4361EE", color="#FFFFFF"),
                            on_click=lambda e: cargar_vista_usuario()
                        ),
                        ft.Button(
                            "Administrador",
                            icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                            width=380,
                            style=ft.ButtonStyle(padding=15, bgcolor="#1E2235", color="#FFFFFF"),
                            on_click=lambda e: cargar_vista_admin()
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
                )
            )
        )
        page.update()

    cargar_login()

if __name__ == "__main__":
    import os, sys
    is_web = "--web" in sys.argv or "PORT" in os.environ or os.environ.get("FLET_WEB") == "1"
    port = int(os.environ.get("PORT", 8550 if is_web else 0))
    host = "0.0.0.0" if is_web else None
    view = (ft.AppView.WEB_BROWSER if ("--web" in sys.argv) else None) if is_web else ft.AppView.FLET_APP

    if hasattr(ft, "run"):
        ft.run(main, host=host, port=port, view=view)
    else:
        ft.app(target=main, host=host, port=port, view=view)
#Agradecemos al equipo por este proyecto, a Dios y a gemini 