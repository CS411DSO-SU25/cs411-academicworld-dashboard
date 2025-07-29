from dash import html, dcc, Input, Output, State, no_update
import dash
import time
from utils import get_mysql_cursor

def layout():
    return html.Div(
        id="w4-box",
        className="widget",
        children=[
            html.Div([
                html.Div("Faculty Profile", className="widget-title"),
                html.Div([
                    html.Button("Edit", id="w4-edit-btn", n_clicks=0, style={"marginRight": "10px"}),
                    html.Button("Update", id="w4-update-btn", n_clicks=0, style={"display": "none"})
                ], style={"display": "flex"}),
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "8px"}),
            html.Div(id="w4-prof-indicator", className="widget-filter"),
            html.Div(
                style={"display": "flex", "flex": "1"},
                children=[
                    html.Div(id="w4-photo-box", style={"flex": "0 0 100px", "textAlign": "center"}),
                    html.Div(
                        id="w4-details-edit-container",
                        style={"background": "#fff", "borderRadius": "12px", "padding": "16px", "height": "208px",
                               "overflowY": "auto", "boxSizing": "border-box", "boxShadow": "0 1px 5px #0001",
                               "flex": "1", "display": "flex", "flexDirection": "column"},
                        children=[
                            html.Div(id="w4-details-view"),
                            html.Div([
                                html.Div([html.Label("Title:"), dcc.Input(id="w4-edit-title", type="text", style={"width": "100%"})], style={"marginBottom": "6px"}),
                                html.Div([html.Label("Phone:"), dcc.Input(id="w4-edit-phone", type="text", style={"width": "100%"})], style={"marginBottom": "6px"}),
                                html.Div([html.Label("Email:"), dcc.Input(id="w4-edit-email", type="email", style={"width": "100%"})], style={"marginBottom": "6px"}),
                                html.Div([html.Label("Research Interest:"), dcc.Input(id="w4-edit-ri", type="text", style={"width": "100%"})], style={"marginBottom": "6px"}),
                            ], id="w4-edit-fields", style={"display": "none", "marginTop": "10px"})
                        ]
                    )
                ]
            ),
            html.Div(id="w4-signal", style={"display": "none"})
        ]
    )

def register_callbacks(app):
    @app.callback(
        Output("w4-prof-indicator", "children"),
        Input("prof-dd", "value"),
    )
    def update_indicator(faculty_name):
        if not faculty_name:
            return html.I("Please select a faculty member", style={"fontStyle": "italic", "color": "#444", "fontSize": "1.1rem"})
        return html.I(f"Faculty: {faculty_name}", style={"fontStyle": "italic", "color": "#444", "fontSize": "1.1rem"})

    @app.callback(
        Output("w4-photo-box", "children"),
        Output("w4-details-view", "children"),
        Output("w4-details-edit-container", "style"),
        Output("w4-edit-fields", "style"),
        Output("w4-edit-title", "value"),
        Output("w4-edit-phone", "value"),
        Output("w4-edit-email", "value"),
        Output("w4-edit-ri", "value"),
        Output("w4-edit-btn", "style"),
        Output("w4-update-btn", "style"),
        Output("w4-signal", "children"),
        Input("prof-dd", "value"),
        Input("w4-edit-btn", "n_clicks"),
        Input("w4-update-btn", "n_clicks"),
        Input("research-interest-signal", "children"),
        State("w4-edit-title", "value"),
        State("w4-edit-phone", "value"),
        State("w4-edit-email", "value"),
        State("w4-edit-ri", "value"),
        prevent_initial_call=True
    )
    def update_profile(faculty_name, edit_clicks, update_clicks, research_signal, edit_title, edit_phone, edit_email, edit_ri):
        ctx = dash.callback_context
        triggered = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        show_edit = False
        signal_value = no_update
        if triggered == "w4-edit-btn":
            show_edit = True
        if triggered == "w4-update-btn" and faculty_name:
            conn, cursor = get_mysql_cursor()
            cursor.execute("UPDATE faculty SET position=%s, phone=%s, email=%s, research_interest=%s WHERE name=%s",
                (edit_title, edit_phone, edit_email, edit_ri, faculty_name))
            conn.commit()
            cursor.close()
            conn.close()
            show_edit = False
            signal_value = str(time.time())
        photo_url = None
        position = phone = email = research_interest = university = "-"
        total_citations = num_publications = "-"
        top_paper_title = top_paper_year = "-"
        if faculty_name:
            conn, cursor = get_mysql_cursor()
            cursor.execute("""SELECT f.position, f.phone, f.email, f.research_interest, f.photo_url, u.name
                              FROM faculty f JOIN university u ON f.university_id = u.id WHERE f.name = %s""", (faculty_name,))
            result = cursor.fetchone()
            if result:
                position, phone, email, research_interest, photo_url, university = result
            cursor.execute("""SELECT p.title, p.year, p.num_citations
                              FROM faculty f JOIN faculty_publication fp ON f.id = fp.faculty_id
                              JOIN publication p ON fp.publication_id = p.id
                              WHERE f.name = %s ORDER BY p.num_citations DESC""", (faculty_name,))
            pubs = cursor.fetchall()
            num_publications = len(pubs)
            total_citations = sum(row[2] for row in pubs) if pubs else 0
            if pubs:
                top_paper_title, top_paper_year, _ = pubs[0]
            cursor.close()
            conn.close()
        view_content = [
            html.Div(f"University: {university}", style={"marginBottom": "2px"}),
            html.Div(f"Title: {position}", style={"marginBottom": "2px"}),
            html.Div(f"Phone: {phone}", style={"marginBottom": "2px"}),
            html.Div(f"Email: {email}", style={"marginBottom": "2px"}),
            html.Div(f"Research Interest: {research_interest}", style={"marginBottom": "2px"}),
            html.Div(f"Number of Publications: {num_publications}", style={"marginBottom": "2px"}),
            html.Div(f"Total Citations: {total_citations}", style={"marginBottom": "2px"}),
            html.Div(f"Most Cited Paper: {top_paper_title} ({top_paper_year})", style={"marginBottom": "2px"}),
        ] if faculty_name else [html.Div("Please select a faculty member.", style={"color": "#999"})]
        if photo_url:
            photo = html.Img(src=photo_url, style={
                "width": "84px", "height": "84px", "objectFit": "cover", "borderRadius": "14px",
                "background": "#eee", "border": "1px solid #ccc"
            })
        else:
            photo = html.Div("No photo", style={
                "width": "84px", "height": "84px", "borderRadius": "14px", "background": "#eee",
                "display": "flex", "alignItems": "center", "justifyContent": "center",
                "color": "#888", "fontWeight": "bold", "border": "1px solid #ccc"
            })
        edit_field_style = {"display": "block", "marginTop": "10px"} if show_edit else {"display": "none"}
        view_container_style = {
            "background": "#fff", "borderRadius": "12px", "padding": "16px", "height": "208px",
            "overflowY": "auto", "boxSizing": "border-box", "boxShadow": "0 1px 5px #0001", "flex": "1",
            "display": "flex", "flexDirection": "column"
        }
        return (photo, view_content, view_container_style, edit_field_style,
                position if faculty_name else "", phone if faculty_name else "",
                email if faculty_name else "", research_interest if faculty_name else "",
                {"display": "none"} if show_edit else {"marginRight": "10px"},
                {"display": "inline-block"} if show_edit else {"display": "none"}, signal_value)
