from utils import html, dcc, px, Input, Output, callback_context, get_mysql_cursor, sanitize_input
PREFIX = "w3"

def layout():
    return html.Div(
        id=f"{PREFIX}-box",
        className="widget",
        children=[
            html.H3("Top 10 Keywords by Faculty Count", className="widget-title"),
            html.Div(id=f"{PREFIX}-filters", className="widget-filter"),
            dcc.Graph(id=f"{PREFIX}-pie", config={"displayModeBar": False}),
        ]
    )

def register_callbacks(app):
    @app.callback(
        Output(f"{PREFIX}-filters", "children"),
        Output(f"{PREFIX}-pie", "figure"),
        Input("clear-btn", "n_clicks"),
        Input("uni-dd", "value"),
        Input("prof-dd", "value"),
    )
    def update_pie(clear_clicks, university, professor):
        ctx = callback_context
        if ctx.triggered:
            trigger = ctx.triggered[0]['prop_id'].split('.')[0]
        else:
            trigger = None

        if trigger == 'clear-btn' or trigger is None:
            university = None
            professor = None

        university = sanitize_input(university)

        filters = []
        if university:
            filters.append(f"University: {university}")

        if filters:
            filter_text = " | ".join(filters)
        else:
            filter_text = "No filters selected"

        params = []
        if university:
            sql = (
                "SELECT keyword, faculty_count "
                "FROM faculty_keyword_summary_view "
                "WHERE university = %s "
                "ORDER BY faculty_count DESC LIMIT 10"
            )
            params.append(university)
        else:
            sql = (
                "SELECT keyword, SUM(faculty_count) as faculty_count "
                "FROM faculty_keyword_summary_view "
                "GROUP BY keyword "
                "ORDER BY faculty_count DESC LIMIT 10"
            )

        conn, cur = get_mysql_cursor()
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            fig = px.pie(names=[], values=[], title="No data to display")
        else:
            keywords = []
            counts = []
            for row in rows:
                keywords.append(row[0])
                counts.append(row[1])
            fig = px.pie(names=keywords, values=counts, title="")
            fig.update_traces(textinfo='percent+label')
            fig.update_layout(
                margin={"l": 32, "r": 8, "t": 8, "b": 32},
                height=260
            )

        return filter_text, fig

