from utils import html, dcc, Input, Output, callback_context, dash_exceptions, NEO4J_URL, AUTH, HEADERS
import plotly.graph_objs as go
import math
from dash.exceptions import PreventUpdate
import requests

PREFIX = "w5"
prev_prof = -1

def layout():
    return html.Div(
        id=f"{PREFIX}-box",
        className="widget",
        children=[
            html.H3("Publication–Keyword Graph", className="widget-title"),
            html.Div(id=f"{PREFIX}-filters", className="widget-filter"),
            dcc.Graph(id=f"{PREFIX}-graph", config={"displayModeBar": False}, style={"flex": "1"})
        ]
    )

def register_callbacks(app):
    @app.callback(
        Output(f"{PREFIX}-graph", "figure"),
        Input("prof-dd", "value"),
        prevent_initial_call=False
    )
    def draw_graph(professor):
        global prev_prof
        if prev_prof == professor: raise PreventUpdate
        prev_prof = professor
        def placeholder(msg):
            fig = go.Figure()
            fig.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff",
                annotations=[{'text': msg, 'xref': 'paper', 'yref': 'paper', 'showarrow': False, 'font': {'size': 16}}],
                xaxis={'visible': False}, yaxis={'visible': False}, margin={'l':0,'r':0,'t':30,'b':0})
            return fig
        if not professor:
            return placeholder("Select a faculty member to view their publication network")
        stmt_pub = ("MATCH (f:FACULTY {name:$prof})-[:PUBLISH]->(p:PUBLICATION) "
                    "RETURN p.id AS id, p.title AS title, p.numCitations AS cites "
                    "ORDER BY cites DESC LIMIT 5")
        payload = {"statements": [{"statement": stmt_pub, "parameters": {'prof': professor}}]}
        res = requests.post(NEO4J_URL, auth=AUTH, headers=HEADERS, json=payload)
        res.raise_for_status()
        pubs_data = res.json()['results'][0]['data']
        if not pubs_data: return placeholder("No publications found for this professor.")
        pubs = [row['row'] for row in pubs_data]
        n = len(pubs)
        angle_step = 2 * math.pi / n
        pub_pos = {}
        for i, (pid, title, cites) in enumerate(pubs):
            theta = i * angle_step
            x, y = math.cos(theta), math.sin(theta)
            pub_pos[pid] = (x, y, title, cites)
        kw_pos, kw_edges = {}, []
        for pid, title, cites in pubs:
            stmt_kw = ("MATCH (p:PUBLICATION {id:$pid})-[r:LABEL_BY]->(k:KEYWORD) "
                       "RETURN k.name AS kw, r.score AS score ORDER BY score DESC LIMIT 3")
            payload_kw = {"statements": [{"statement": stmt_kw, "parameters": {'pid': pid}}]}
            res_kw = requests.post(NEO4J_URL, auth=AUTH, headers=HEADERS, json=payload_kw)
            res_kw.raise_for_status()
            kws = res_kw.json()['results'][0]['data']
            m = len(kws)
            if m == 0: continue
            angle_pub = math.atan2(pub_pos[pid][1], pub_pos[pid][0])
            step2 = math.pi * 2 / m
            for j, row in enumerate(kws):
                kw, score = row['row']
                theta2 = angle_pub + (j - (m-1)/2) * step2
                x2 = pub_pos[pid][0] + 0.2 * math.cos(theta2)
                y2 = pub_pos[pid][1] + 0.2 * math.sin(theta2)
                kw_pos[(pid, kw)] = (x2, y2, kw, score)
                kw_edges.append((pid, (pid, kw)))
        fig = go.Figure()
        for pid, (x, y, title, cites) in pub_pos.items():
            fig.add_trace(go.Scatter(x=[0, x, None], y=[0, y, None], mode='lines', line={'width': max(1, cites/100), 'color':'grey'}, hoverinfo='none'))
        for pid, key in kw_edges:
            x1, y1, _, _ = pub_pos[pid]
            x2, y2, _, _ = kw_pos[key]
            fig.add_trace(go.Scatter(x=[x1, x2, None], y=[y1, y2, None], mode='lines', line={'width':1, 'color':'lightgrey'}, hoverinfo='none'))
        fig.add_trace(go.Scatter(x=[v[0] for v in kw_pos.values()], y=[v[1] for v in kw_pos.values()],
            mode='markers', marker={'size':12,'color':'lightgreen'}, hovertext=[f"{v[2]} (score: {v[3]:.1f})" for v in kw_pos.values()], hoverinfo='text'))
        fig.add_trace(go.Scatter(x=[v[0] for v in pub_pos.values()], y=[v[1] for v in pub_pos.values()],
            mode='markers', marker={'size':20,'color':'skyblue'}, hovertext=[f"{v[2]} ({v[3]} cites)" for v in pub_pos.values()], hoverinfo='text'))
        fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers+text',
            marker={'size':30,'color':'orange'}, text=[professor], textposition='bottom center', hoverinfo='none'))
        fig.update_layout(plot_bgcolor="#fff", paper_bgcolor="#fff", showlegend=False,
            xaxis={'visible': False}, yaxis={'visible': False}, margin={'l':20,'r':20,'t':10,'b':20})
        return fig
