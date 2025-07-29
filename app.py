from utils import html, dcc, Input, Output, State, callback_context, get_mysql_cursor
import dash
import widget1, widget2, widget3, widget4, widget5, widget6


app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Dashboard to Rule the Academic World"

header_section = html.Div( className="headerbar",
    children=[ html.Div( "Dashboard to Rule the Academic World", className="dashboard-title"),
    html.Div( className="filter-bar-row",
    children=[ html.Div([ dcc.Input( id="kw-search", type="text", placeholder="Search keyword...", className="search-input"), dcc.Dropdown( id="kw-dd", options=[], placeholder="", disabled=True, clearable=False, className="dropdown-btn"),], 
    className="input-dropdown-pair"),
    dcc.Dropdown( id="uni-dd", options=[], placeholder="-- Please select a university --", className="uni-dropdown"),
        html.Div([ dcc.Input(id="prof-search", type="text", placeholder="Search faculty...", className="search-input"),dcc.Dropdown( id="prof-dd", options=[], placeholder="", disabled=True, clearable=False, className="dropdown-btn"),], 
             className="input-dropdown-pair"), html.Button("Clear", id="clear-btn", className="clear-btn")
            ]
        )
    ]
)

app.layout = html.Div( id="root", className="page-root", children=[ header_section, html.Div( id="grid", className="dashboard-grid", 
                    children=[ widget1.layout(), widget2.layout(), widget3.layout(), widget4.layout(), widget5.layout(), widget6.layout(), 
                              html.Div(id="research-interest-signal", style={"display": "none"})
                        ]
                    )
                ]
)


def generate_university_dropdown_options(kw, prof):
    conn, cur = get_mysql_cursor()
    params = []
    if kw:
        sql = """
            SELECT DISTINCT u.name
            FROM university u
            JOIN faculty f ON f.university_id = u.id
            JOIN faculty_publication fp ON fp.faculty_id = f.id
            JOIN publication p ON fp.publication_id = p.id
            JOIN publication_keyword pk ON pk.publication_id = p.id
            JOIN keyword k ON pk.keyword_id = k.id
            WHERE k.name = %s
        """
        params.append(kw)
        if prof:
            sql += " AND f.name = %s"
            params.append(prof)
        sql += " LIMIT 20"
        cur.execute(sql, tuple(params))
        uni_opts = [{"label": row[0], "value": row[0]} for row in cur.fetchall()]
    else:
        cur.execute("SELECT DISTINCT name FROM university")
        uni_opts = [{"label": row[0], "value": row[0]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return uni_opts

def generate_keyword_dropdown_options(prof_val, uni_val, kw_search):
    query = None
    params = []
    if prof_val and uni_val:
        query = '''
            SELECT DISTINCT k.name
            FROM keyword k
            JOIN publication_keyword pk ON pk.keyword_id = k.id
            JOIN publication p ON pk.publication_id = p.id
            JOIN faculty_publication fp ON p.id = fp.publication_id
            JOIN faculty f ON fp.faculty_id = f.id
            JOIN university u ON f.university_id = u.id
            WHERE f.name = %s AND u.name = %s
            LIMIT 20
        '''
        params = (prof_val, uni_val)
    elif kw_search and len(kw_search.strip()) >= 2:
        query = "SELECT DISTINCT k.name FROM keyword k WHERE k.name LIKE %s LIMIT 20"
        params = (f"%{kw_search.strip()}%",)
    result = []
    if query:
        conn, cur = get_mysql_cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        for name in rows:
            option = { "label": name[0], "value": name[0]}
            result.append(option)
        cur.close()
        conn.close()
    return result

def generate_faculty_dropdown_options(kw_val, uni_val, prof_search):
    query = None
    params = []
    if kw_val and uni_val:
        query = """
            SELECT DISTINCT f.name
            FROM faculty f
            JOIN faculty_publication fp ON f.id = fp.faculty_id
            JOIN publication_keyword pk ON fp.publication_id = pk.publication_id
            JOIN keyword k ON pk.keyword_id = k.id
            JOIN university u ON f.university_id = u.id
            WHERE k.name = %s AND u.name = %s
            LIMIT 20
            """
        params = (kw_val, uni_val)
    elif prof_search and len(prof_search.strip()) >= 2:
        query = "SELECT DISTINCT f.name FROM faculty f"
        joins = []
        wheres = ["f.name LIKE %s"]
        params = [f"%{prof_search.strip()}%"]
        if kw_val:
            joins.append("JOIN faculty_keyword fk ON fk.faculty_id = f.id")
            joins.append("JOIN keyword k ON fk.keyword_id = k.id")
            wheres.append("k.name = %s")
            params.append(kw_val)
        if uni_val:
            joins.append("JOIN university u ON f.university_id = u.id")
            wheres.append("u.name = %s")
            params.append(uni_val)
        query += " " + " ".join(joins)
        if wheres:
            query += " WHERE " + " AND ".join(wheres)
        query += " LIMIT 20"
        params = tuple(params)
    result = []
    if query:
        conn, cur = get_mysql_cursor()        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        for name in rows:
            option = { "label": name[0], "value": name[0]}
            result.append(option)
        cur.close()
        conn.close()
    return result

@app.callback(
    Output("kw-dd", "options"),
    Output("kw-dd", "disabled"),
    Output("kw-dd", "value"),
    Output("kw-search", "value"),
    Output("kw-search", "disabled"),
    Output("prof-dd", "options"),
    Output("prof-dd", "disabled"),
    Output("prof-dd", "value"),
    Output("prof-search", "value"),
    Output("prof-search", "disabled"),
    Output("uni-dd", "options"),
    Output("uni-dd", "disabled"),
    Output("uni-dd", "value"),
    Input("kw-search", "value"),
    Input("prof-search", "value"),
    Input("kw-dd", "value"),
    Input("prof-dd", "value"),
    Input("uni-dd", "value"),
    Input("clear-btn", "n_clicks"),
)
def update_all_dropdowns(kw_search, prof_search, kw_val, prof_val, uni_val, clear_clicks):
    ctx = callback_context
    triggered = None
    if ctx.triggered:
        triggered = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered == "clear-btn":
        uni_opts = generate_university_dropdown_options(None, None)
        return (
            [], True, None, "", False,
            [], True, None, "", False,
            uni_opts, False, None
        )

    show_kw_options = False
    if prof_val and uni_val:
        show_kw_options = True
        kw_search = '   '
    elif prof_val or uni_val:
        show_kw_options = True
    elif ( kw_search and len(kw_search.strip()) >= 2 ) or (prof_val and uni_val):
        show_kw_options = True

    if show_kw_options:
        kw_opts = generate_keyword_dropdown_options(
            prof_val,
            uni_val,
            kw_search
        )
    else:
        kw_opts = []

    valid_kw_values = []
    for o in kw_opts:
        valid_kw_values.append(o["value"])

    if len(kw_opts) == 1:
        kw_dd_value = kw_opts[0]["value"]
        kw_disabled = True
        kw_search_disabled = True
    elif len(kw_opts) > 1:
        if kw_val in valid_kw_values:
            kw_dd_value = kw_val
        else:
            kw_dd_value = None
        kw_disabled = False
        kw_search_disabled = False
    else:
        kw_dd_value = None
        kw_disabled = True
        kw_search_disabled = False

    if kw_dd_value:
        kw_search_out = kw_dd_value
    elif kw_search:
        kw_search_out = kw_search
    else:
        kw_search_out = ""

    show_prof_options = False
    if kw_dd_value or uni_val:
        show_prof_options = True
    elif prof_search and len(prof_search.strip()) >= 2:
        show_prof_options = True

    if show_prof_options:
        prof_opts = generate_faculty_dropdown_options(
            kw_val=kw_dd_value,
            uni_val=uni_val,
            prof_search=prof_search
        )
    else:
        prof_opts = []

    valid_prof_values = []
    for o in prof_opts:
        valid_prof_values.append(o["value"])

    if len(prof_opts) == 1:
        prof_dd_value = prof_opts[0]["value"]
        prof_disabled = True
        prof_search_disabled = True
    elif len(prof_opts) > 1:
        if prof_val in valid_prof_values:
            prof_dd_value = prof_val
        else:
            prof_dd_value = None
        prof_disabled = False
        prof_search_disabled = False
    else:
        prof_dd_value = None
        prof_disabled = True
        prof_search_disabled = False

    if prof_dd_value:
        prof_search_out = prof_dd_value
    elif prof_search:
        prof_search_out = prof_search
    else:
        prof_search_out = ""

    uni_opts = generate_university_dropdown_options(kw_dd_value, prof_dd_value)
    valid_uni_values = []
    for o in uni_opts:
        valid_uni_values.append(o["value"])

    uni_val_final = None
    uni_disabled = False

    if uni_val:
        uni_val_final = uni_val
        uni_disabled = True        
    elif len(uni_opts) == 1:
        uni_val_final = uni_opts[0]["value"]
        uni_val = uni_val_final
        uni_disabled = True
    elif prof_dd_value:
        conn, cur = get_mysql_cursor()
        cur.execute("""
            SELECT u.name
            FROM university u
            JOIN faculty f ON f.university_id = u.id
            WHERE f.name = %s
            LIMIT 1
        """, (prof_dd_value,))
        row = cur.fetchone()
        if row:
            uni_val_final = row[0]
            uni_disabled = True
        cur.close()
        conn.close()
    elif len(uni_opts) > 1:
        if uni_val in valid_uni_values:
            uni_val_final = uni_val
        else:
            uni_val_final = None
        uni_disabled = False
    else:
        uni_val_final = None
        uni_disabled = True

    return (
        kw_opts, kw_disabled, kw_dd_value, kw_search_out, kw_search_disabled,
        prof_opts, prof_disabled, prof_dd_value, prof_search_out, prof_search_disabled,
        uni_opts, uni_disabled, uni_val_final
    )







    

widget1.register_callbacks(app)
widget2.register_callbacks(app)
widget3.register_callbacks(app)
widget4.register_callbacks(app)
widget5.register_callbacks(app)
widget6.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)
