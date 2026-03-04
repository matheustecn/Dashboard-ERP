import base64
import io
import datetime
import os
import dash
from dash import dcc, html, dash_table, Input, Output, State, ctx
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import plotly.graph_objects as go
import plotly.express as px

# ── CONFIGURAÇÃO DO APP ──────────────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Esta linha é crucial para o Railway identificar o servidor Flask subjacente
server = app.server 

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>GUAPO · ERPWeb</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Sora:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

            :root {
                --bg:          #0d0f0e;
                --bg2:         #131714;
                --bg3:         #1a1f1c;
                --bg4:         #222720;
                --border:      rgba(255,255,255,0.07);
                --border-lit:  rgba(80,220,120,0.25);
                --green:       #3ddc84;
                --green-dim:   #2ab86a;
                --green-glow:  rgba(61,220,132,0.15);
                --green-deep:  rgba(61,220,132,0.06);
                --gold:        #c9a84c;
                --gold-light:  #e8c97a;
                --text:        #e8ede9;
                --text-mid:    #8fa894;
                --text-dim:    #4d5e52;
                --red:         #ff5c5c;
                --shadow:      0 0 0 1px rgba(255,255,255,0.04), 0 8px 32px rgba(0,0,0,0.4);
                --shadow-lg:   0 0 0 1px rgba(255,255,255,0.05), 0 24px 64px rgba(0,0,0,0.6);
                --r:           10px;
                --t:           0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }

            html { scroll-behavior: smooth; }
            body {
                font-family: 'Sora', sans-serif;
                background: var(--bg);
                color: var(--text);
                -webkit-font-smoothing: antialiased;
                min-height: 100vh;
            }

            /* ── SCROLLBAR ───────────────────────────── */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: var(--bg2); }
            ::-webkit-scrollbar-thumb { background: var(--bg4); border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: var(--green-dim); }

            /* LOGIN E DASHBOARD ESTILOS */
            .screen-login { min-height: 100vh; display: flex; flex-direction: column; position: relative; overflow: hidden; background: var(--bg); }
            .screen-login::before { content: ''; position: absolute; inset: 0; background-image: linear-gradient(rgba(61,220,132,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(61,220,132,0.03) 1px, transparent 1px); background-size: 48px 48px; animation: grid-drift 20s linear infinite; pointer-events: none; }
            @keyframes grid-drift { 0% { background-position: 0 0; } 100% { background-position: 48px 48px; } }
            .login-top-bar { position: relative; z-index: 2; padding: 18px 48px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border); }
            .login-top-brand { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: var(--green); letter-spacing: 0.5px; }
            .login-center { flex: 1; display: flex; align-items: center; justify-content: center; position: relative; z-index: 2; padding: 40px 20px; }
            .login-panel { width: 440px; animation: panel-in 0.7s cubic-bezier(0.16,1,0.3,1) both; }
            @keyframes panel-in { from { opacity: 0; transform: translateY(32px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }
            .login-headline { font-family: 'Playfair Display', serif; font-size: 52px; font-weight: 900; line-height: 1; letter-spacing: -2px; margin-bottom: 6px; color: var(--text); }
            .login-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 16px; padding: 36px; box-shadow: var(--shadow-lg); position: relative; overflow: hidden; }
            .input-field { width: 100% !important; padding: 14px 18px !important; border-radius: 8px !important; border: 1px solid var(--border) !important; background: var(--bg3) !important; color: var(--text) !important; margin-bottom: 15px; }
            .btn-login { width: 100%; padding: 16px 24px; background: var(--green); color: var(--bg); border: none; border-radius: 8px; cursor: pointer; font-weight: 700; letter-spacing: 2px; }
            
            /* DASHBOARD LAYOUT */
            .screen-dash { background: var(--bg); min-height: 100vh; display: flex; flex-direction: column; }
            .sidebar { width: 240px; background: var(--bg2); border-right: 1px solid var(--border); position: fixed; top: 0; left: 0; bottom: 0; }
            .dash-main { margin-left: 240px; flex: 1; }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
'''

# ── LAYOUT DO APP ─────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id='auth-status', data=False),
    
    # Tela de Login
    html.Div(id='screen-login', className='screen-login', children=[
        html.Div(className='login-top-bar', children=[
            html.Div("GUAPO", className='login-top-brand'),
        ]),
        html.Div(className='login-center', children=[
            html.Div(className='login-panel', children=[
                html.Div("Dashboard Financeiro", className='login-headline'),
                html.Div(className='login-card', children=[
                    dcc.Input(id="user", type="text", placeholder="Usuário", className="input-field"),
                    dcc.Input(id="pass", type="password", placeholder="Senha", className="input-field"),
                    html.Button("ENTRAR", id="btn-login", className="btn-login"),
                    html.Div(id="out-login", style={'marginTop':'10px', 'color':'red'})
                ]),
            ])
        ]),
    ]),

    # Tela do Dashboard (Invisível até login)
    html.Div(id='screen-dash', className='screen-dash', style={'display': 'none'}, children=[
        html.Div(className='sidebar', children=[
            html.Div("GUAPO ERP", style={'padding':'20px', 'color':'#3ddc84', 'fontWeight':'bold'})
        ]),
        html.Div(className='dash-main', children=[
            html.H1("Bem-vindo ao Dashboard", style={'padding':'40px', 'color':'white'})
        ])
    ])
])

# ── CALLBACKS SIMPLES PARA TESTE ──────────────────────────────────────────────
@app.callback(
    [Output('screen-login', 'style'), Output('screen-dash', 'style'), Output('out-login', 'children')],
    [Input('btn-login', 'n_clicks')],
    [State('user', 'value'), State('pass', 'value')]
)
def login(n, u, p):
    if n:
        if u == "admin" and p == "123":
            return {'display': 'none'}, {'display': 'block'}, ""
        return {'display': 'flex'}, {'display': 'none'}, "Credenciais inválidas"
    return {'display': 'flex'}, {'display': 'none'}, ""

# ── INICIALIZAÇÃO PARA O RAILWAY (O MAIS IMPORTANTE) ─────────────────────────

if __name__ == "__main__":
    # O Railway usa a variável de ambiente PORT. Caso não exista, usa 8050 localmente.
    port = int(os.environ.get("PORT", 8050))
    
    # host='0.0.0.0' é obrigatório para que o Railway consiga acessar o app
    app.run_server(host='0.0.0.0', port=port, debug=False)