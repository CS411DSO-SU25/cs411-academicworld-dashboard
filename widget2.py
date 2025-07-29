from utils import html, dcc, Input, Output, callback_context, get_mysql_cursor
import plotly.graph_objs as go

def layout():
    return html.Div(
        id="w2-box",
        className="widget widget-green",
        children=[
            html.Div([html.H3("Publication Trends", className="widget-title")], className="widget-header"),
            html.Div(id="w2-filters", className="widget-filter"),
            dcc.Graph(id="w2-graph", config={"displayModeBar": False}),
        ]
    )

def register_callbacks(app):
    @app.callback(
        Output("w2-filters", "children"),
        Output("w2-graph", "figure"),
        Input("prof-dd", "value"),
        Input("clear-btn", "n_clicks"),
        Input("kw-dd", "value"),
        Input("uni-dd", "value"),
        Input("prof-dd", "value"),
    )
    def update_graph(professor, clear_clicks, keyword, university, professor_again):
        ctx = callback_context
        trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        if trigger == "clear-btn" or trigger is None: keyword = university = professor = None
        filters = []
        if keyword: filters.append(f"Keyword: {keyword}")
        if university: filters.append(f"University: {university}")
        if professor: filters.append(f"Professor: {professor}")
        filter_text = " | ".join(filters) if filters else "Showing all publications."
        if not (professor or university or keyword):
            sql = "SELECT p.year, COUNT(p.id) AS num_publications FROM publication p GROUP BY p.year ORDER BY p.year"
            params = []
        else:
            sql_parts = [
                "SELECT p.year, COUNT(p.id) AS num_publications",
                "FROM publication p",
                "JOIN faculty_publication fp ON p.id = fp.publication_id",
                "JOIN faculty f ON fp.faculty_id = f.id"
            ]
            params = []
            if university: sql_parts.append("JOIN university u ON f.university_id = u.id")
            if keyword: sql_parts.append("JOIN publication_keyword pk ON p.id = pk.publication_id"); sql_parts.append("JOIN keyword k ON pk.keyword_id = k.id")
            where = []
            if university: where.append("u.name = %s"); params.append(university)
            if professor: where.append("f.name = %s"); params.append(professor)
            if keyword: where.append("k.name = %s"); params.append(keyword)
            if where: sql_parts.append("WHERE " + " AND ".join(where))
            sql_parts.append("GROUP BY p.year ORDER BY p.year")
            sql = " ".join(sql_parts)
        conn, cur = get_mysql_cursor()
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        if not rows:
            return filter_text, go.Figure(layout={ "height": 350, "annotations": [{"text": "No data to display", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 16}, "x": 0.5, "y": 0.5, "xanchor": "center", "yanchor": "middle"}]})
        years, counts = zip(*rows)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=years, y=counts, marker_line_width=1))
        fig.update_layout(xaxis_title="Year", yaxis_title="Publications", height=220, margin=dict(l=10, r=10, t=10, b=40))
        return filter_text, fig

