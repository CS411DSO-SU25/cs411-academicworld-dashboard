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

def generate_university_dropdown_options(kw_val, prof_val):
    if kw_val and prof_val:
        query = (
            "SELECT DISTINCT u.name "
            "FROM university u "
            "JOIN faculty f ON f.university_id = u.id "
            "JOIN faculty_keyword fk ON fk.faculty_id = f.id "
            "JOIN keyword k ON fk.keyword_id = k.id "
            "WHERE k.name = %s AND f.name = %s "
        )
        params = (kw_val, prof_val)
    elif kw_val:
        query = (
            "SELECT DISTINCT u.name "
            "FROM university u "
            "JOIN faculty f ON f.university_id = u.id "
            "JOIN faculty_publication fp ON f.id = fp.faculty_id "
            "JOIN publication_keyword pk ON fp.publication_id = pk.publication_id "
            "JOIN keyword k ON pk.keyword_id = k.id "
            "WHERE k.name = %s "
        )
        params = (kw_val,)
    elif prof_val:
        query = (
            "SELECT DISTINCT u.name "
            "FROM university u "
            "JOIN faculty f ON f.university_id = u.id "
            "WHERE f.name = %s "
        )
        params = (prof_val,)
    else:
        query = "SELECT DISTINCT u.name FROM university u"
        params = ()
    conn, cur = get_mysql_cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    result = []
    for (name,) in rows:
        result.append({"label": name, "value": name})
    cur.close()
    conn.close()
    return result

def generate_faculty_dropdown_options(kw_val, uni_val, prof_search):
    if kw_val and uni_val:
        query = (
            "SELECT DISTINCT f.name "
            "FROM faculty f "
            "JOIN faculty_publication fp ON f.id = fp.faculty_id "
            "JOIN publication_keyword pk ON fp.publication_id = pk.publication_id "
            "JOIN keyword k ON pk.keyword_id = k.id "
            "JOIN university u ON f.university_id = u.id "
            "WHERE k.name = %s AND u.name = %s "
            "LIMIT 50"
        )
        params = (kw_val, uni_val)
    elif uni_val:
        query = (
            "SELECT DISTINCT f.name "
            "FROM faculty f "
            "JOIN university u ON f.university_id = u.id "
            "WHERE u.name = %s "
            "LIMIT 50"
        )
        params = (uni_val,)
    elif kw_val:
        query = (
            "SELECT DISTINCT f.name "
            "FROM faculty f "
            "JOIN faculty_publication fp ON f.id = fp.faculty_id "
            "JOIN publication_keyword pk ON fp.publication_id = pk.publication_id "
            "JOIN keyword k ON pk.keyword_id = k.id "
            "WHERE k.name = %s "
            "LIMIT 50"
        )
        params = (kw_val,)
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
        query += " WHERE " + " AND ".join(wheres)
        query += " LIMIT 20"
        params = tuple(params)
    else:
        return []
    conn, cur = get_mysql_cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    result = []
    for (name,) in rows:
        result.append({"label": name, "value": name})
    cur.close()
    conn.close()
    return result

def generate_keyword_dropdown_options(prof_val, uni_val, kw_search):
    if prof_val and uni_val:
        query = (
            "SELECT name FROM ("
            "SELECT DISTINCT k.name AS name "
            "FROM keyword k "
            "JOIN faculty_keyword fk ON fk.keyword_id = k.id "
            "JOIN faculty f ON fk.faculty_id = f.id "
            "JOIN university u ON f.university_id = u.id "
            "WHERE f.name = %s AND u.name = %s "
            "UNION "
            "SELECT DISTINCT k2.name AS name "
            "FROM keyword k2 "
            "JOIN publication_keyword pk ON pk.keyword_id = k2.id "
            "JOIN faculty_publication fp ON fp.publication_id = pk.publication_id "
            "JOIN faculty f2 ON fp.faculty_id = f2.id "
            "JOIN university u2 ON f2.university_id = u2.id "
            "WHERE f2.name = %s AND u2.name = %s"
            ") AS combined"
            " LIMIT 50"
        )
        params = (prof_val, uni_val, prof_val, uni_val)
    elif prof_val:
        query = (
            "SELECT name FROM ("
            "SELECT DISTINCT k.name AS name "
            "FROM keyword k "
            "JOIN faculty_keyword fk ON fk.keyword_id = k.id "
            "JOIN faculty f ON fk.faculty_id = f.id "
            "WHERE f.name = %s "
            "UNION "
            "SELECT DISTINCT k2.name AS name "
            "FROM keyword k2 "
            "JOIN publication_keyword pk ON pk.keyword_id = k2.id "
            "JOIN faculty_publication fp ON fp.publication_id = pk.publication_id "
            "JOIN faculty f2 ON fp.faculty_id = f2.id "
            "WHERE f2.name = %s"
            ") AS combined"
            " LIMIT 50"
        )
        params = (prof_val, prof_val)
    elif kw_search and len(kw_search.strip()) >= 2:
        query = "SELECT DISTINCT k.name FROM keyword k"
        joins = []
        wheres = ["k.name LIKE %s"]
        params = [f"%{kw_search.strip()}%"]
        if prof_val:
            joins.append("JOIN faculty_keyword fk ON fk.keyword_id = k.id")
            joins.append("JOIN faculty f ON fk.faculty_id = f.id")
            wheres.append("f.name = %s")
            params.append(prof_val)
        if uni_val:
            joins.append("JOIN faculty_keyword fk2 ON fk2.keyword_id = k.id")
            joins.append("JOIN faculty f2 ON fk2.faculty_id = f2.id")
            joins.append("JOIN university u ON f2.university_id = u.id")
            wheres.append("u.name = %s")
            params.append(uni_val)
        query += " " + " ".join(joins)
        query += " WHERE " + " AND ".join(wheres)
        query += " LIMIT 50"
        params = tuple(params)
    else:
        return []
    conn, cur = get_mysql_cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    result = []
    for (name,) in rows:
        result.append({"label": name, "value": name})
    cur.close()
    conn.close()
    return result



@app.callback(
    Output("kw-dd","options"),
    Output("kw-dd","disabled"),
    Output("kw-dd","value"),
    Output("kw-search","value"),
    Output("kw-search","disabled"),
    Output("prof-dd","options"),
    Output("prof-dd","disabled"),
    Output("prof-dd","value"),
    Output("prof-search","value"),
    Output("prof-search","disabled"),
    Output("uni-dd","options"),
    Output("uni-dd","disabled"),
    Output("uni-dd","value"),
    Input("kw-search","value"),
    Input("prof-search","value"),
    Input("kw-dd","value"),
    Input("prof-dd","value"),
    Input("uni-dd","value"),
    Input("clear-btn","n_clicks"),
)
def update_all_dropdowns(kw_search, prof_search, kw_val, prof_val, uni_val, clear_clicks):
    ctx = callback_context
    triggered = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    if triggered == "clear-btn":
        uni_opts = generate_university_dropdown_options(None, None)
        return [], False, None, "", False, [], False, None, "", False, uni_opts, False, None

    prof_opts_all = generate_faculty_dropdown_options(kw_val, uni_val, prof_search)
    valid_prof = []
    for opt in prof_opts_all:
        valid_prof.append(opt["value"])
    if prof_val:
        prof_val_out = prof_val
        prof_disabled = True
        prof_search_disabled = True
        prof_opts = [{"label": prof_val, "value": prof_val}]
    elif len(prof_opts_all) == 1:
        prof_val_out = prof_opts_all[0]["value"]
        prof_disabled = True
        prof_search_disabled = True
        prof_opts = prof_opts_all
    else:
        prof_val_out = None
        prof_disabled = False
        prof_search_disabled = False
        prof_opts = prof_opts_all

    uni_opts_all = generate_university_dropdown_options(kw_val, prof_val_out)
    if uni_val:
        uni_val_out = uni_val
        uni_disabled = True
        uni_opts = [{"label": uni_val, "value": uni_val}]
    elif len(uni_opts_all) == 1:
        uni_val_out = uni_opts_all[0]["value"]
        uni_disabled = True
        uni_opts = uni_opts_all
    else:
        uni_val_out = None
        uni_disabled = False
        uni_opts = uni_opts_all

    kw_opts_all = generate_keyword_dropdown_options(prof_val_out, uni_val_out, kw_search)
    if kw_val:
        kw_val_out = kw_val
        kw_disabled = True
        kw_search_disabled = True
        kw_opts = [{"label": kw_val, "value": kw_val}]
    elif len(kw_opts_all) == 1:
        kw_val_out = kw_opts_all[0]["value"]
        kw_disabled = True
        kw_search_disabled = True
        kw_opts = kw_opts_all
    else:
        kw_val_out = None
        kw_disabled = False
        kw_search_disabled = False
        kw_opts = kw_opts_all

    if kw_val_out:
        kw_search_out = kw_val_out
    else:
        if kw_search:
            kw_search_out = kw_search
        else:
            kw_search_out = ""

    if prof_val_out:
        prof_search_out = prof_val_out
    else:
        if prof_search:
            prof_search_out = prof_search
        else:
            prof_search_out = ""

    return kw_opts, kw_disabled, kw_val_out, kw_search_out, kw_search_disabled, prof_opts, prof_disabled, prof_val_out, prof_search_out, prof_search_disabled, uni_opts, uni_disabled, uni_val_out



widget1.register_callbacks(app)
widget2.register_callbacks(app)
widget3.register_callbacks(app)
widget4.register_callbacks(app)
widget5.register_callbacks(app)
widget6.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)
