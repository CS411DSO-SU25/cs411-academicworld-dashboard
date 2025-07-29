from utils import html, dash_table, Input, Output, callback_context, get_mysql_cursor, sanitize_input

PREFIX = "w1"

def layout():
    return html.Div(
        id=f"{PREFIX}-box",
        className="widget",
        children=[
            html.H3("Top 10 Faculty by Keyword-Relevant Citations"),
            html.Div(id=f"{PREFIX}-filters", className="widget-filter"),
            dash_table.DataTable(
                id=f"{PREFIX}-table",
                data=[],
                columns=[
                    {"name": "Name", "id": "name"},
                    {"name": "Position", "id": "position"},
                    {"name": "University", "id": "university"},
                    {"name": "Research Interest", "id": "research_interest"},
                    {"name": "KRC", "id": "krc"}
                ],
                style_cell={"textAlign": "left", "whiteSpace": "normal"},
                style_cell_conditional=[{"if": {"column_id": "position"}, "maxWidth": "250px", "minWidth": "120px", "whiteSpace": "normal", "overflow": "hidden", "textOverflow": "ellipsis"}],
                style_table={"maxHeight": "220px", "overflowY": "auto"},
                style_header={"fontWeight": "bold"},
            )
        ]
    )

def register_callbacks(app):
    @app.callback(
        Output(f"{PREFIX}-filters", "children"),
        Output(f"{PREFIX}-table", "data"),
        Input("clear-btn", "n_clicks"),
        Input("kw-dd", "value"),
        Input("uni-dd", "value"),
        Input("w4-signal", "children"),
        Input("research-interest-signal", "children")
    )
    def update_table(clear_clicks, keyword, university, w4_update, signal_value):
        ctx = callback_context
        trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
        if trigger == 'clear-btn' or trigger is None: keyword = None; university = None
        keyword = sanitize_input(keyword)
        university = sanitize_input(university)
        if not keyword: return "Please select a keyword.", []
        filters = [f"Keyword: {keyword}"]
        if university: filters.append(f"University: {university}")
        filter_text = " | ".join(filters)
        sql = [
            "SELECT f.name, f.position, u.name as university, f.research_interest, IFNULL(SUM(pk.score),0) as krc",
            "FROM faculty f",
            "JOIN faculty_publication fp ON f.id = fp.faculty_id",
            "JOIN publication_keyword pk ON fp.publication_id = pk.publication_id",
            "JOIN keyword k ON pk.keyword_id = k.id",
            "JOIN university u ON f.university_id = u.id"
        ]
        conditions = ["k.name = %s"]
        params = [keyword]
        if university: conditions.append("u.name = %s"); params.append(university)
        if conditions: sql.append("WHERE " + " AND ".join(conditions))
        sql.append("GROUP BY f.id ORDER BY krc DESC LIMIT 10")
        conn, cur = get_mysql_cursor()
        cur.execute(" ".join(sql), tuple(params))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        data = [{"name": row[0], "position": str(row[1]) if row[1] else "", "university": row[2], "research_interest": row[3] if row[3] else "", "krc": int(row[4])} for row in rows]
        return filter_text, data
