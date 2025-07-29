import dash
from utils import get_mysql_cursor, mongo_db, NEO4J_URL, AUTH, HEADERS, dash_table, Input, Output, State, html
import requests
from datetime import datetime

def layout():
    return html.Div(
        id="w6-box",
        children=[
            html.Div([
                html.Div("Top 10 Most Cited Publications", className="widget-title"),
                html.Button("Update Research Interests", id="w6-update-btn", style={"float": "right", "fontWeight": "bold", "marginBottom": "8px"})
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "8px"}),
            html.Div(id="w6-prof-indicator", className="widget-filter"),
            dash_table.DataTable(
                id="w6-table",
                columns=[{"name": "Title", "id": "title"}, {"name": "Year", "id": "year"}, {"name": "Citations", "id": "num_citations"}, {"name": "Keywords", "id": "keywords"}],
                data=[], page_size=10,
                style_cell={"fontFamily": "inherit", "padding": "7px 8px", "background": "#fff", "textAlign": "left", "whiteSpace": "normal"},
                style_header={"fontWeight": "bold", "background": "#eaf0f7", "color": "#19324d", "fontSize": "1.05rem"},
                style_table={"overflowX": "auto", "maxHeight": "200px", "width": "100%"},
            ),
            html.Div(id="w6-dummy", style={"display": "none"}),
        ],
        style={"height": "320px", "padding": "18px", "border": "2px solid #6da7d7", "borderRadius": "18px", "background": "#fafdff", "boxShadow": "0 2px 10px #0001"}
    )

def register_callbacks(app):
    @app.callback(
        Output("w6-table", "data"),
        Output("w6-table", "columns"),
        Output("w6-prof-indicator", "children"),
        Input("prof-dd", "value"),
    )
    def load_top_cited_table(selected_prof):
        columns = [{"name": "Title", "id": "title"}, {"name": "Year", "id": "year"}, {"name": "Citations", "id": "num_citations"}, {"name": "Keywords", "id": "keywords"}]
        if not selected_prof:
            prof_text = html.I("Please select a faculty member", style={"color": "#444", "fontSize": "1.1rem", "fontFamily": "inherit"})
            return [], columns, prof_text
        conn, cursor = get_mysql_cursor()
        sql = """
            SELECT p.id, p.title, p.year, p.num_citations
            FROM faculty f
            JOIN faculty_publication fp ON f.id = fp.faculty_id
            JOIN publication p ON fp.publication_id = p.id
            WHERE f.name = %s
            ORDER BY p.num_citations DESC
            LIMIT 10
        """
        cursor.execute(sql, (selected_prof,))
        pubs = cursor.fetchall()
        pub_ids = [row[0] for row in pubs]
        kw_map = {}
        if pub_ids:
            format_strings = ','.join(['%s'] * len(pub_ids))
            kw_sql = f"""
                SELECT pk.publication_id, k.name, pk.score, p.num_citations
                FROM publication_keyword pk
                JOIN keyword k ON pk.keyword_id = k.id
                JOIN publication p ON pk.publication_id = p.id
                WHERE pk.publication_id IN ({format_strings})
            """
            cursor.execute(kw_sql, tuple(pub_ids))
            rows = cursor.fetchall()
            from collections import defaultdict
            kw_map = defaultdict(list)
            for pub_id, kw, score, num_citations in rows:
                kw_map[pub_id].append(kw)
        data = []
        for row in pubs:
            pub_id, title, year, num_citations = row
            keywords = ", ".join(kw_map.get(pub_id, []))
            data.append({"title": title, "year": year, "num_citations": num_citations, "keywords": keywords})
        cursor.close(); conn.close()
        prof_text = html.I(f"Faculty: {selected_prof}", style={"color": "#236", "fontSize": "1.1rem", "fontFamily": "inherit"})
        return data, columns, prof_text

    @app.callback(
        Output("w6-dummy", "children"),
        Output("research-interest-signal", "children"),
        Input("w6-update-btn", "n_clicks"),
        State("prof-dd", "value"),
        State("w6-table", "data"),
    )
    def update_research_interests(n_clicks, selected_prof, table_data):
        if not n_clicks or not selected_prof or not table_data: return dash.no_update, dash.no_update
        conn, cursor = get_mysql_cursor()
        sql = """
            SELECT p.id, p.num_citations
            FROM faculty f
            JOIN faculty_publication fp ON f.id = fp.faculty_id
            JOIN publication p ON fp.publication_id = p.id
            WHERE f.name = %s
            ORDER BY p.num_citations DESC
            LIMIT 10
        """
        cursor.execute(sql, (selected_prof,))
        pubs = cursor.fetchall()
        pub_ids = [row[0] for row in pubs]
        score_map = {}
        if pub_ids:
            format_strings = ','.join(['%s'] * len(pub_ids))
            kw_sql = f"""
                SELECT pk.publication_id, k.name, pk.score, p.num_citations
                FROM publication_keyword pk
                JOIN keyword k ON pk.keyword_id = k.id
                JOIN publication p ON pk.publication_id = p.id
                WHERE pk.publication_id IN ({format_strings})
            """
            cursor.execute(kw_sql, tuple(pub_ids))
            rows = cursor.fetchall()
            from collections import defaultdict
            score_map = defaultdict(float)
            for pub_id, kw, score, num_citations in rows:
                weighted = float(score or 0) * int(num_citations or 0)
                score_map[kw] += weighted
        top5 = sorted(score_map.items(), key=lambda x: (-x[1], x[0]))[:5]
        top_keywords = [kw for kw, _ in top5]
        new_research_interest = ", ".join(top_keywords)
        cursor.close(); conn.close()
        conn, cursor = get_mysql_cursor()
        cursor.execute("UPDATE faculty SET research_interest = %s WHERE name = %s", (new_research_interest, selected_prof))
        conn.commit(); cursor.close(); conn.close()
        mongo_db.faculty.update_one({"name": selected_prof}, {"$set": {"researchInterest": new_research_interest}})
        cypher = "MATCH (f:FACULTY {name:$name}) SET f.researchInterest=$ri"
        params = {"name": selected_prof, "ri": new_research_interest}
        requests.post(NEO4J_URL, auth=AUTH, headers=HEADERS, json={"statements": [{"statement": cypher, "parameters": params}]})
        return dash.no_update, f"{selected_prof} updated {datetime.now().isoformat()}"
