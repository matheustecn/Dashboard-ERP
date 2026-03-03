import base64
import io
import datetime
import dash
from dash import dcc, html, dash_table, Input, Output, State, ctx
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

app = dash.Dash(__name__, suppress_callback_exceptions=True)

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

            /* ══════════════════════════════════════════
               LOGIN
            ══════════════════════════════════════════ */
            .screen-login {
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                position: relative;
                overflow: hidden;
                background: var(--bg);
            }

            /* Animated background grid */
            .screen-login::before {
                content: '';
                position: absolute; inset: 0;
                background-image:
                    linear-gradient(rgba(61,220,132,0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(61,220,132,0.03) 1px, transparent 1px);
                background-size: 48px 48px;
                animation: grid-drift 20s linear infinite;
                pointer-events: none;
            }
            @keyframes grid-drift {
                0%   { background-position: 0 0; }
                100% { background-position: 48px 48px; }
            }

            /* Glowing orb */
            .screen-login::after {
                content: '';
                position: absolute;
                top: -30vh; right: -20vw;
                width: 70vw; height: 70vw;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(61,220,132,0.06) 0%, transparent 65%);
                pointer-events: none;
            }

            .login-top-bar {
                position: relative; z-index: 2;
                padding: 18px 48px;
                display: flex; align-items: center; justify-content: space-between;
                border-bottom: 1px solid var(--border);
            }
            .login-top-brand {
                font-family: 'Playfair Display', serif;
                font-size: 20px; font-weight: 700;
                color: var(--green);
                letter-spacing: 0.5px;
            }
            .login-top-tag {
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--text-dim);
                text-transform: uppercase; letter-spacing: 3px;
            }
            .login-top-dot {
                width: 8px; height: 8px; border-radius: 50%;
                background: var(--green);
                box-shadow: 0 0 12px var(--green);
                animation: blink 2s ease-in-out infinite;
            }
            @keyframes blink {
                0%,100% { opacity: 1; }
                50%      { opacity: 0.3; }
            }

            .login-center {
                flex: 1; display: flex;
                align-items: center; justify-content: center;
                position: relative; z-index: 2;
                padding: 40px 20px;
            }

            .login-panel {
                width: 440px;
                animation: panel-in 0.7s cubic-bezier(0.16,1,0.3,1) both;
            }
            @keyframes panel-in {
                from { opacity: 0; transform: translateY(32px) scale(0.97); }
                to   { opacity: 1; transform: translateY(0)    scale(1);    }
            }

            .login-eyebrow {
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--green);
                text-transform: uppercase; letter-spacing: 4px;
                margin-bottom: 16px;
                display: flex; align-items: center; gap: 10px;
            }
            .login-eyebrow::before {
                content: '';
                display: block; width: 28px; height: 1px;
                background: var(--green); opacity: 0.5;
            }

            .login-headline {
                font-family: 'Playfair Display', serif;
                font-size: 52px; font-weight: 900;
                line-height: 1; letter-spacing: -2px;
                margin-bottom: 6px;
                color: var(--text);
            }
            .login-headline em {
                font-style: italic;
                color: var(--green);
            }
            .login-desc {
                font-size: 13px; color: var(--text-mid);
                font-weight: 300; margin-bottom: 40px;
                letter-spacing: 0.3px;
            }

            .login-card {
                background: var(--bg2);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 36px;
                box-shadow: var(--shadow-lg);
                position: relative;
                overflow: hidden;
            }
            .login-card::before {
                content: '';
                position: absolute; top: 0; left: 0; right: 0; height: 1px;
                background: linear-gradient(90deg, transparent, var(--green), transparent);
                opacity: 0.4;
            }

            .field-group { margin-bottom: 20px; }
            .field-label {
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--text-dim);
                text-transform: uppercase; letter-spacing: 2px;
                margin-bottom: 8px; display: block;
            }
            .input-field {
                width: 100% !important;
                padding: 14px 18px !important;
                border-radius: 8px !important;
                border: 1px solid var(--border) !important;
                font-family: 'Sora', sans-serif !important;
                font-size: 14px !important;
                color: var(--text) !important;
                background: var(--bg3) !important;
                outline: none !important;
                display: block !important;
                transition: border-color var(--t), box-shadow var(--t), background var(--t) !important;
            }
            .input-field:focus {
                border-color: var(--green-dim) !important;
                background: var(--bg4) !important;
                box-shadow: 0 0 0 3px var(--green-deep), 0 0 20px rgba(61,220,132,0.05) !important;
            }
            .input-field::placeholder { color: var(--text-dim) !important; }

            .btn-login {
                width: 100%; margin-top: 8px;
                padding: 16px 24px;
                background: var(--green);
                color: var(--bg);
                border: none; border-radius: 8px;
                cursor: pointer;
                font-family: 'Space Mono', monospace;
                font-weight: 700; font-size: 12px;
                letter-spacing: 3px; text-transform: uppercase;
                transition: all var(--t);
                position: relative; overflow: hidden;
            }
            .btn-login::after {
                content: '';
                position: absolute; inset: 0;
                background: linear-gradient(135deg, rgba(255,255,255,0.15), transparent);
                opacity: 0; transition: opacity var(--t);
            }
            .btn-login:hover {
                background: var(--gold-light);
                transform: translateY(-1px);
                box-shadow: 0 8px 24px rgba(61,220,132,0.3);
            }
            .btn-login:hover::after { opacity: 1; }
            .btn-login:active { transform: translateY(0); }

            .login-error {
                margin-top: 16px; min-height: 20px;
                font-family: 'Space Mono', monospace;
                font-size: 11px; color: var(--red);
                text-align: center; letter-spacing: 1px;
            }

            .login-footer-note {
                margin-top: 20px; text-align: center;
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--text-dim);
                letter-spacing: 1px;
            }

            /* ══════════════════════════════════════════
               DASHBOARD
            ══════════════════════════════════════════ */
            .screen-dash {
                background: var(--bg);
                min-height: 100vh;
                display: flex; flex-direction: column;
            }

            /* Sidebar */
            .dash-layout {
                display: flex;
                flex: 1;
            }

            .sidebar {
                width: 240px; flex-shrink: 0;
                background: var(--bg2);
                border-right: 1px solid var(--border);
                display: flex; flex-direction: column;
                position: fixed; top: 0; left: 0; bottom: 0;
                z-index: 50;
                padding: 0;
            }

            .sidebar-brand {
                padding: 28px 28px 24px;
                border-bottom: 1px solid var(--border);
            }
            .sidebar-logo {
                font-family: 'Playfair Display', serif;
                font-size: 32px; font-weight: 900;
                color: var(--text); letter-spacing: -1px;
                line-height: 1;
            }
            .sidebar-logo span { color: var(--green); }
            .sidebar-sub {
                font-family: 'Space Mono', monospace;
                font-size: 9px; color: var(--text-dim);
                text-transform: uppercase; letter-spacing: 3px;
                margin-top: 5px;
            }

            .sidebar-section {
                padding: 24px 16px 8px;
            }
            .sidebar-section-label {
                font-family: 'Space Mono', monospace;
                font-size: 9px; color: var(--text-dim);
                text-transform: uppercase; letter-spacing: 3px;
                padding: 0 12px; margin-bottom: 8px;
            }

            .nav-item {
                display: flex; align-items: center; gap: 12px;
                padding: 11px 14px; border-radius: 8px;
                cursor: pointer; margin-bottom: 2px;
                transition: background var(--t), color var(--t);
                font-size: 13px; font-weight: 500; color: var(--text-mid);
                border: 1px solid transparent;
            }
            .nav-item:hover { background: var(--bg3); color: var(--text); }
            .nav-item.active {
                background: var(--green-deep);
                border-color: var(--border-lit);
                color: var(--green);
            }
            .nav-icon { font-size: 15px; width: 20px; text-align: center; }

            .sidebar-bottom {
                margin-top: auto;
                padding: 20px 16px;
                border-top: 1px solid var(--border);
            }
            .sidebar-user {
                display: flex; align-items: center; gap: 12px;
                padding: 10px 12px; border-radius: 8px;
                background: var(--bg3);
            }
            .user-avatar {
                width: 32px; height: 32px; border-radius: 50%;
                background: linear-gradient(135deg, var(--green-dim), var(--gold));
                display: flex; align-items: center; justify-content: center;
                font-size: 13px; font-weight: 700; color: var(--bg);
                flex-shrink: 0;
            }
            .user-name { font-size: 13px; font-weight: 600; color: var(--text); }
            .user-role { font-family: 'Space Mono', monospace; font-size: 9px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }

            /* Main area */
            .dash-main {
                margin-left: 240px;
                flex: 1;
                display: flex; flex-direction: column;
            }

            .topbar {
                height: 64px; flex-shrink: 0;
                border-bottom: 1px solid var(--border);
                padding: 0 40px;
                display: flex; align-items: center; justify-content: space-between;
                background: rgba(13,15,14,0.85);
                backdrop-filter: blur(16px);
                position: sticky; top: 0; z-index: 40;
            }
            .topbar-title {
                font-size: 15px; font-weight: 600; color: var(--text);
            }
            .topbar-subtitle {
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--text-dim);
                letter-spacing: 1px; margin-top: 2px;
            }
            .topbar-actions { display: flex; align-items: center; gap: 12px; }
            .status-chip {
                display: flex; align-items: center; gap: 8px;
                padding: 7px 14px; border-radius: 100px;
                background: var(--green-deep);
                border: 1px solid var(--border-lit);
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--green);
                text-transform: uppercase; letter-spacing: 2px;
            }
            .status-dot {
                width: 6px; height: 6px; border-radius: 50%;
                background: var(--green);
                box-shadow: 0 0 8px var(--green);
                animation: blink 2s ease-in-out infinite;
            }
            .topbar-date {
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--text-dim);
                letter-spacing: 1px;
            }

            .main-content {
                padding: 36px 40px;
                flex: 1;
            }

            /* Upload */
            .upload-area {
                border: 1px dashed rgba(61,220,132,0.2);
                border-radius: var(--r);
                background: var(--green-deep);
                padding: 20px;
                text-align: center;
                cursor: pointer;
                margin-bottom: 36px;
                transition: border-color var(--t), background var(--t);
                display: flex; align-items: center; justify-content: center; gap: 12px;
            }
            .upload-area:hover {
                border-color: rgba(61,220,132,0.4);
                background: rgba(61,220,132,0.08);
            }
            .upload-icon { font-size: 18px; }
            .upload-text { font-size: 13px; color: var(--text-mid); font-weight: 400; }
            .upload-text strong { color: var(--green); font-weight: 600; }

            /* Section header */
            .section-header {
                display: flex; align-items: flex-end;
                justify-content: space-between;
                margin-bottom: 24px;
            }
            .section-title {
                font-family: 'Playfair Display', serif;
                font-size: 26px; font-weight: 700;
                color: var(--text); letter-spacing: -0.5px;
            }
            .section-eyebrow {
                font-family: 'Space Mono', monospace;
                font-size: 9px; color: var(--green);
                text-transform: uppercase; letter-spacing: 3px;
                margin-bottom: 6px;
            }
            .section-period {
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--text-dim);
                letter-spacing: 1px;
            }

            /* KPI Cards */
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 32px;
            }
            .kpi-card {
                background: var(--bg2);
                border: 1px solid var(--border);
                border-radius: var(--r);
                padding: 24px 22px;
                position: relative; overflow: hidden;
                transition: border-color var(--t), transform var(--t), box-shadow var(--t);
                cursor: default;
            }
            .kpi-card:hover {
                border-color: var(--border-lit);
                transform: translateY(-2px);
                box-shadow: 0 12px 32px rgba(0,0,0,0.3), 0 0 0 1px var(--border-lit);
            }
            /* Corner accent */
            .kpi-card::after {
                content: '';
                position: absolute; top: 0; right: 0;
                width: 48px; height: 48px;
                background: radial-gradient(circle at top right, rgba(61,220,132,0.08), transparent 70%);
                pointer-events: none;
            }
            .kpi-top {
                display: flex; align-items: center;
                justify-content: space-between;
                margin-bottom: 16px;
            }
            .kpi-label {
                font-family: 'Space Mono', monospace;
                font-size: 9px; color: var(--text-dim);
                text-transform: uppercase; letter-spacing: 2px;
            }
            .kpi-badge {
                font-family: 'Space Mono', monospace;
                font-size: 9px; padding: 3px 8px;
                border-radius: 4px; font-weight: 700;
                text-transform: uppercase; letter-spacing: 1px;
            }
            .kpi-badge.up   { background: rgba(61,220,132,0.12); color: var(--green); }
            .kpi-badge.wait { background: rgba(201,168,76,0.12); color: var(--gold); }
            .kpi-value {
                font-family: 'Playfair Display', serif;
                font-size: 30px; font-weight: 700;
                color: var(--text); line-height: 1;
                letter-spacing: -1px;
            }
            .kpi-value.green { color: var(--green); }
            .kpi-value.gold  { color: var(--gold-light); }
            .kpi-value.red   { color: var(--red); }
            .kpi-sub {
                font-family: 'Space Mono', monospace;
                font-size: 10px; color: var(--text-dim);
                margin-top: 8px; letter-spacing: 0.5px;
            }
            /* Thin colored bottom border */
            .kpi-bar {
                position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
                background: linear-gradient(90deg, var(--green), transparent);
                opacity: 0;
                transition: opacity var(--t);
            }
            .kpi-card:hover .kpi-bar { opacity: 1; }

            /* Divider */
            .divider {
                height: 1px; background: var(--border);
                margin: 32px 0;
            }

            /* Tabs */
            .custom-tabs {
                border-bottom: 1px solid var(--border) !important;
                margin-bottom: 28px;
            }
            .custom-tab {
                background: transparent !important;
                color: var(--text-dim) !important;
                border: none !important;
                border-bottom: 2px solid transparent !important;
                padding: 12px 0 !important;
                margin-right: 36px !important;
                font-family: 'Space Mono', monospace !important;
                font-size: 10px !important; font-weight: 700 !important;
                text-transform: uppercase !important; letter-spacing: 2px !important;
                transition: color var(--t) !important;
            }
            .custom-tab:hover { color: var(--text-mid) !important; }
            .custom-tab--selected {
                color: var(--green) !important;
                border-bottom: 2px solid var(--green) !important;
            }

            /* DRE Table */
            .dre-card {
                background: var(--bg2);
                border: 1px solid var(--border);
                border-radius: var(--r);
                overflow: hidden;
            }
            .dre-card-header {
                padding: 20px 28px;
                border-bottom: 1px solid var(--border);
                display: flex; align-items: center; justify-content: space-between;
                background: var(--bg3);
            }
            .dre-card-title {
                font-family: 'Space Mono', monospace;
                font-size: 11px; font-weight: 700;
                text-transform: uppercase; letter-spacing: 2px;
                color: var(--text-mid);
            }
            .dre-card-title span { color: var(--green); }
            .dre-pill {
                font-family: 'Space Mono', monospace;
                font-size: 9px; color: var(--gold);
                background: rgba(201,168,76,0.1);
                border: 1px solid rgba(201,168,76,0.2);
                padding: 4px 12px; border-radius: 4px;
                text-transform: uppercase; letter-spacing: 1px;
            }

            /* Robot */
            .robo-container {
                position: fixed; bottom: 28px; right: 28px;
                width: 100px; z-index: 9999;
                animation: float 4s ease-in-out infinite;
                filter: drop-shadow(0 8px 20px rgba(61,220,132,0.25));
                cursor: pointer;
            }
            .robo-container:hover {
                animation-play-state: paused;
                filter: drop-shadow(0 12px 28px rgba(61,220,132,0.5));
            }
            @keyframes float {
                0%,100% { transform: translateY(0); }
                50%      { transform: translateY(-10px); }
            }

            /* Decorative line element */
            .geo-line {
                position: absolute; 
                width: 1px;
                background: linear-gradient(to bottom, transparent, var(--green-dim), transparent);
                opacity: 0.2;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>
'''

# ── LAYOUT ────────────────────────────────────────────────────────────────────

app.layout = html.Div([
    dcc.Store(id='auth-status', data=False),
    dcc.Store(id='csv-store', data=None),

    # ── LOGIN ──────────────────────────────────────────────────────────────────
    html.Div(id='screen-login', className='screen-login', children=[

        html.Div(className='login-top-bar', children=[
            html.Div("GUAPO", className='login-top-brand'),
            html.Div("Sistema de Gestão Estratégica", className='login-top-tag'),
            html.Div(className='login-top-dot'),
        ]),

        html.Div(className='login-center', children=[
            html.Div(className='login-panel', children=[

                html.Div(["ACESSO", html.Span(" SEGURO")], className='login-eyebrow'),
                html.Div([
                    "Dashboard ",
                    html.Em("Financeiro"),
                ], className='login-headline'),
                html.P("Gestão estratégica de resultados e indicadores de performance.", className='login-desc'),

                html.Div(className='login-card', children=[
                    html.Div(className='field-group', children=[
                        html.Div("Identificação", className='field-label'),
                        dcc.Input(id="user", type="text",
                                  placeholder="Usuário do sistema",
                                  className="input-field", debounce=False),
                    ]),
                    html.Div(className='field-group', children=[
                        html.Div("Autenticação", className='field-label'),
                        dcc.Input(id="pass", type="password",
                                  placeholder="••••••••••••",
                                  className="input-field", debounce=False),
                    ]),
                    html.Button("ENTRAR NO SISTEMA →", id="btn-login", className="btn-login"),
                    html.Div(id="out-login", className="login-error"),
                ]),

                html.Div("Credenciais: admin / 123", className='login-footer-note'),
            ])
        ]),
    ]),

    # ── DASHBOARD ──────────────────────────────────────────────────────────────
    html.Div(id='screen-dash', className='screen-dash', style={'display': 'none'}, children=[
        html.Div(className='dash-layout', children=[

            # SIDEBAR
            html.Div(className='sidebar', children=[
                html.Div(className='sidebar-brand', children=[
                    html.Div([
                        "GUAP",
                        html.Span("O"),
                    ], className='sidebar-logo'),
                    html.Div("ERP · Dashboard", className='sidebar-sub'),
                ]),

                html.Div(className='sidebar-section', children=[
                    html.Div("Principal", className='sidebar-section-label'),
                    html.Div([html.Span("📊", className='nav-icon'), "Indicadores"],   className='nav-item active'),
                    html.Div([html.Span("📁", className='nav-icon'), "DRE Detalhado"], className='nav-item'),
                    html.Div([html.Span("📈", className='nav-icon'), "Gráficos"],      className='nav-item'),
                ]),

                html.Div(className='sidebar-section', children=[
                    html.Div("Sistema", className='sidebar-section-label'),
                    html.Div([html.Span("⚙️", className='nav-icon'), "Configurações"], className='nav-item'),
                    html.Div([html.Span("📤", className='nav-icon'), "Exportar"], id='btn-exportar', className='nav-item'),
                    dcc.Download(id='download-excel'),
                ]),

                html.Div(className='sidebar-bottom', children=[
                    html.Div(className='sidebar-user', children=[
                        html.Div("A", className='user-avatar'),
                        html.Div([
                            html.Div("Administrador", className='user-name'),
                            html.Div("Acesso Total", className='user-role'),
                        ]),
                    ])
                ]),
            ]),

            # MAIN
            html.Div(className='dash-main', children=[

                # Top bar
                html.Div(className='topbar', children=[
                    html.Div([
                        html.Div("Visão Geral Financeira", className='topbar-title'),
                        html.Div(id='topbar-fiscal', className='topbar-subtitle'),
                    ]),
                    html.Div(className='topbar-actions', children=[
                        html.Div(id='topbar-date', className='topbar-date'),
                        html.Div([
                            html.Div(className='status-dot'),
                            "SISTEMA ATIVO",
                        ], className='status-chip'),
                    ]),
                ]),

                # Content
                html.Div(className='main-content', children=[

                    # Upload
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            html.Span("↑", className='upload-icon'),
                            html.Span([
                                "Arraste ou clique para importar o ",
                                html.Strong("DRE (.csv)"),
                                " — os dados serão processados automaticamente"
                            ], className='upload-text'),
                        ]),
                        className="upload-area", style={},
                    ),

                    # Section header
                    html.Div(className='section-header', children=[
                        html.Div([
                            html.Div("INDICADORES", className='section-eyebrow'),
                            html.Div("Resumo Executivo", className='section-title'),
                        ]),
                        html.Div("Período: Jan–Dez 2025", className='section-period'),
                    ]),

                    # Tabs + content
                    dcc.Tabs(id="tabs-nav", value='tab-ind', className="custom-tabs", children=[
                        dcc.Tab(label='KPIs & Indicadores', value='tab-ind',
                                className="custom-tab", selected_className="custom-tab--selected"),
                        dcc.Tab(label='DRE Detalhado',      value='tab-dre',
                                className="custom-tab", selected_className="custom-tab--selected"),
                    ]),
                    html.Div(id='tabs-content-area'),
                ]),
            ]),
        ]),

        # Robot
        html.Div(className="robo-container", children=[
            html.Img(src='/assets/robot.gif', style={"width":"100%","height":"auto"})
        ]),
    ]),
])

# ── CALLBACKS ────────────────────────────────────────────────────────────────

@app.callback(
    [Output('auth-status', 'data'), Output('out-login', 'children')],
    Input('btn-login', 'n_clicks'),
    [State('user', 'value'), State('pass', 'value')],
    prevent_initial_call=True,
)
def handle_login(n, u, p):
    if u == "admin" and p == "123":
        return True, ""
    return False, "// CREDENCIAIS INVÁLIDAS — tente novamente"


@app.callback(
    [Output('screen-login', 'style'), Output('screen-dash', 'style')],
    Input('auth-status', 'data'),
)
def toggle_screens(is_logged):
    if is_logged:
        return {'display': 'none'}, {'display': 'flex', 'flexDirection': 'column'}
    return {}, {'display': 'none'}


@app.callback(
    Output('csv-store', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True,
)
def store_csv(contents, filename):
    if contents is None:
        return None
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        # Try common encodings used in Brazilian systems
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                text = decoded.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        lines = [l for l in text.strip().splitlines() if l.strip()]
        # Detect separator
        sep = ';' if lines[0].count(';') > lines[0].count(',') else ','
        rows = []
        for line in lines[1:]:  # skip header
            parts = line.split(sep)
            if len(parts) >= 2:
                rows.append({
                    'categoria': parts[0].strip(),
                    'valor':     parts[1].strip(),
                    'tipo':      parts[2].strip() if len(parts) > 2 else '',
                })
        return rows
    except Exception as e:
        return []


@app.callback(
    [Output('topbar-date', 'children'),
     Output('topbar-fiscal', 'children')],
    Input('auth-status', 'data'),
)
def update_topbar_date(_):
    now = datetime.datetime.now()
    months_pt = ['JAN','FEV','MAR','ABR','MAI','JUN',
                 'JUL','AGO','SET','OUT','NOV','DEZ']
    month_str = months_pt[now.month - 1]
    return (
        f"{month_str} {now.year}",
        f"EXERCÍCIO FISCAL · {now.year}",
    )



@app.callback(
    Output('tabs-content-area', 'children'),
    Input('tabs-nav', 'value'),
    Input('csv-store', 'data'),
)
def render_tab_content(tab, csv_data):

    def fmt_brl(val_str):
        try:
            v = float(str(val_str).replace(',', '.'))
            prefix = "R$ " if v >= 0 else "−R$ "
            return prefix + f"{abs(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return str(val_str)

    def get_val(csv_data, tipo):
        if not csv_data:
            return None
        for row in csv_data:
            if row.get('tipo', '').strip() == tipo:
                try:
                    return float(str(row['valor']).replace(',', '.'))
                except:
                    pass
        return None

    # ── DRE TAB ──────────────────────────────────────────────────────────────
    if tab == 'tab-dre':
        if csv_data:
            table_data = [{"desc": r['categoria'], "val": fmt_brl(r['valor'])} for r in csv_data]
            pill_text  = f"{len(csv_data)} linhas carregadas"
            pill_style = {'background': 'rgba(61,220,132,0.12)', 'color': '#3ddc84',
                          'border': '1px solid rgba(61,220,132,0.25)'}
        else:
            table_data = [{"desc": "Nenhum arquivo importado ainda.", "val": "—"}]
            pill_text  = "Aguardando CSV"
            pill_style = {}

        # Row styling based on Tipo
        cond_styles = [
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#0f1310'},
        ]
        if csv_data:
            for i, row in enumerate(csv_data):
                t = row.get('tipo', '')
                if t == 'Total_Final':
                    cond_styles.append({'if': {'row_index': i},
                        'backgroundColor': 'rgba(61,220,132,0.08)',
                        'color': '#3ddc84', 'fontWeight': '700'})
                elif t == 'Total':
                    cond_styles.append({'if': {'row_index': i},
                        'backgroundColor': 'rgba(61,220,132,0.04)',
                        'color': '#8fa894', 'fontWeight': '600'})
                elif t == 'Destaque':
                    cond_styles.append({'if': {'row_index': i},
                        'color': '#c9a84c', 'fontWeight': '600'})

        return html.Div(className="dre-card", children=[
            html.Div(className="dre-card-header", children=[
                html.Div([html.Span("DRE"), " — Demonstrativo de Resultado do Exercício"],
                         className="dre-card-title"),
                html.Div(pill_text, className="dre-pill", style=pill_style),
            ]),
            dash_table.DataTable(
                id='table-dre',
                columns=[{"name": "DISCRIMINAÇÃO", "id": "desc"}, {"name": "VALOR (R$)", "id": "val"}],
                data=table_data,
                style_header={
                    'backgroundColor': '#1a1f1c', 'color': '#4d5e52', 'fontWeight': '700',
                    'textAlign': 'left', 'padding': '14px 28px', 'fontSize': '9px',
                    'textTransform': 'uppercase', 'letterSpacing': '3px',
                    'fontFamily': "'Space Mono', monospace", 'border': 'none',
                    'borderBottom': '1px solid rgba(255,255,255,0.06)',
                },
                style_cell={
                    'textAlign': 'left', 'padding': '14px 28px', 'fontSize': '13px',
                    'color': '#8fa894', 'border': 'none',
                    'borderBottom': '1px solid rgba(255,255,255,0.04)',
                    'fontFamily': "'Sora', sans-serif", 'backgroundColor': '#131714',
                },
                style_data_conditional=cond_styles,
                style_table={'border': 'none', 'overflowX': 'auto', 'borderRadius': '0 0 10px 10px'},
            )
        ])

    # ── KPI TAB ───────────────────────────────────────────────────────────────
    receita  = get_val(csv_data, 'Total')
    lucro    = get_val(csv_data, 'Total_Final')
    margem   = (lucro / receita * 100) if receita and lucro else None
    has_data = csv_data and len(csv_data) > 0

    def kpi_val_receita():
        return fmt_brl(receita) if receita is not None else "R$ 0,00"
    def kpi_val_lucro():
        return fmt_brl(lucro) if lucro is not None else "R$ 0,00"
    def kpi_val_margem():
        return f"{margem:.2f}%".replace('.', ',') if margem is not None else "0,00%"

    status_val   = "Operacional" if has_data else "Aguardando"
    status_badge = "up" if has_data else "wait"
    status_sub   = f"{len(csv_data)} registros importados" if has_data else "Importar DRE para iniciar"

    lucro_neg = lucro is not None and lucro < 0
    lucro_cls = "kpi-value red" if lucro_neg else "kpi-value green"

    kpis_rendered = [
        html.Div(className="kpi-card", children=[
            html.Div(className="kpi-top", children=[
                html.Div("Receita Total",  className="kpi-label"),
                html.Div("BRUTO", className="kpi-badge up"),
            ]),
            html.Div(kpi_val_receita(), className="kpi-value green"),
            html.Div("Receita bruta acumulada", className="kpi-sub"),
            html.Div(className="kpi-bar"),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div(className="kpi-top", children=[
                html.Div("Lucro Líquido", className="kpi-label"),
                html.Div("LÍQUIDO", className=f"kpi-badge {'up' if not lucro_neg else 'wait'}"),
            ]),
            html.Div(kpi_val_lucro(), className=lucro_cls),
            html.Div("Após todas as deduções", className="kpi-sub"),
            html.Div(className="kpi-bar"),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div(className="kpi-top", children=[
                html.Div("Margem Líquida", className="kpi-label"),
                html.Div("MARGEM", className="kpi-badge up"),
            ]),
            html.Div(kpi_val_margem(), className="kpi-value gold"),
            html.Div("Sobre receita bruta", className="kpi-sub"),
            html.Div(className="kpi-bar"),
        ]),
        html.Div(className="kpi-card", children=[
            html.Div(className="kpi-top", children=[
                html.Div("Status", className="kpi-label"),
                html.Div(status_badge.upper(), className=f"kpi-badge {status_badge}"),
            ]),
            html.Div(status_val, className="kpi-value gold"),
            html.Div(status_sub, className="kpi-sub"),
            html.Div(className="kpi-bar"),
        ]),
    ]
    return html.Div(className="kpi-grid", children=kpis_rendered)


@app.callback(
    Output('download-excel', 'data'),
    Input('btn-exportar', 'n_clicks'),
    State('csv-store', 'data'),
    prevent_initial_call=True,
)
def export_excel(n_clicks, csv_data):
    if not n_clicks or not csv_data:
        return None

    now = datetime.datetime.now()
    months_pt = ['JAN','FEV','MAR','ABR','MAI','JUN',
                 'JUL','AGO','SET','OUT','NOV','DEZ']

    # ── Build workbook ────────────────────────────────────────────────────────
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DRE"

    # Color palette
    C_BG_TITLE  = "0D0F0E"
    C_GREEN     = "3DDC84"
    C_GOLD      = "C9A84C"
    C_HEADER_BG = "1A1F1C"
    C_TOTAL_BG  = "162218"
    C_DEST_BG   = "1C1A10"
    C_ALT_BG    = "0F1310"
    C_WHITE     = "E8EDE9"
    C_DIM       = "4D5E52"
    C_MID       = "8FA894"

    def fill(hex_color):
        return PatternFill("solid", fgColor=hex_color)

    def font(hex_color, bold=False, size=11, italic=False):
        return Font(color=hex_color, bold=bold, size=size,
                    name="Segoe UI", italic=italic)

    def border_bottom(hex_color="2A3330"):
        side = Side(style="thin", color=hex_color)
        return Border(bottom=side)

    def money(val_str):
        try:
            v = float(str(val_str).replace(',', '.'))
            return v
        except:
            return val_str

    ws.column_dimensions['A'].width = 42
    ws.column_dimensions['B'].width = 20
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 22

    # ── Row 1: Title block ────────────────────────────────────────────────────
    ws.row_dimensions[1].height = 18
    ws.row_dimensions[2].height = 36
    ws.row_dimensions[3].height = 16
    ws.row_dimensions[4].height = 14

    for col in range(1, 5):
        for row in range(1, 5):
            ws.cell(row=row, column=col).fill = fill(C_BG_TITLE)

    ws.merge_cells('A2:D2')
    title_cell = ws['A2']
    title_cell.value = "GUAPO · Demonstrativo de Resultado do Exercício"
    title_cell.font  = Font(color=C_GREEN, bold=True, size=16, name="Segoe UI")
    title_cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)

    ws.merge_cells('A3:D3')
    sub_cell = ws['A3']
    sub_cell.value = f"Exportado em {now.strftime('%d/%m/%Y')} · {months_pt[now.month-1]} {now.year}"
    sub_cell.font  = Font(color=C_DIM, size=9, name="Segoe UI")
    sub_cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)

    # ── Row 5: Column headers ─────────────────────────────────────────────────
    ws.row_dimensions[5].height = 28
    headers = ["DISCRIMINAÇÃO", "VALOR (R$)", "TIPO", ""]
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=5, column=col_idx, value=h)
        cell.fill = fill(C_HEADER_BG)
        cell.font = Font(color=C_DIM, bold=True, size=9, name="Segoe UI")
        cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)

    # ── Data rows ─────────────────────────────────────────────────────────────
    for i, row in enumerate(csv_data):
        r = i + 6
        ws.row_dimensions[r].height = 22
        tipo = row.get('tipo', '')

        raw_val = money(row['valor'])
        is_num  = isinstance(raw_val, float)

        # Categoria cell
        cat_cell = ws.cell(row=r, column=1, value=row['categoria'])
        cat_cell.alignment = Alignment(horizontal='left', vertical='center', indent=2)

        # Value cell
        val_cell = ws.cell(row=r, column=2, value=raw_val if is_num else row['valor'])
        if is_num:
            val_cell.number_format = 'R$ #,##0.00;[RED]-R$ #,##0.00'
        val_cell.alignment = Alignment(horizontal='right', vertical='center', indent=1)

        # Tipo cell
        tipo_cell = ws.cell(row=r, column=3, value=tipo)
        tipo_cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)

        # Style by type
        if tipo == 'Total_Final':
            for col in range(1, 5):
                ws.cell(row=r, column=col).fill = fill(C_TOTAL_BG)
            cat_cell.font = Font(color=C_GREEN, bold=True, size=11, name="Segoe UI")
            val_cell.font = Font(color=C_GREEN, bold=True, size=11, name="Segoe UI")
            tipo_cell.font = Font(color=C_DIM, size=9, name="Segoe UI")
        elif tipo == 'Total':
            for col in range(1, 5):
                ws.cell(row=r, column=col).fill = fill("131714")
            cat_cell.font = Font(color=C_WHITE, bold=True, size=11, name="Segoe UI")
            val_cell.font = Font(color=C_WHITE, bold=True, size=11, name="Segoe UI")
            tipo_cell.font = Font(color=C_DIM, size=9, name="Segoe UI")
        elif tipo == 'Destaque':
            for col in range(1, 5):
                ws.cell(row=r, column=col).fill = fill(C_DEST_BG)
            cat_cell.font = Font(color=C_GOLD, bold=False, size=11, name="Segoe UI")
            val_cell.font = Font(color=C_GOLD, bold=False, size=11, name="Segoe UI")
            tipo_cell.font = Font(color=C_DIM, size=9, name="Segoe UI")
        elif tipo == 'Sub':
            bg = C_ALT_BG if i % 2 == 1 else "111512"
            for col in range(1, 5):
                ws.cell(row=r, column=col).fill = fill(bg)
            cat_cell.font = Font(color=C_MID, size=11, name="Segoe UI")
            val_val = raw_val if is_num else 0
            val_color = "FF5C5C" if isinstance(val_val, float) and val_val < 0 else C_MID
            val_cell.font = Font(color=val_color, size=11, name="Segoe UI")
            tipo_cell.font = Font(color=C_DIM, size=9, name="Segoe UI")
        else:
            for col in range(1, 5):
                ws.cell(row=r, column=col).fill = fill("111512")
            cat_cell.font = Font(color=C_MID, size=11, name="Segoe UI")
            val_cell.font = Font(color=C_MID, size=11, name="Segoe UI")
            tipo_cell.font = Font(color=C_DIM, size=9, name="Segoe UI")

        # Bottom border on every row
        for col in range(1, 5):
            ws.cell(row=r, column=col).border = border_bottom()

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_row = len(csv_data) + 7
    ws.row_dimensions[footer_row].height = 20
    ws.merge_cells(f'A{footer_row}:D{footer_row}')
    fc = ws.cell(row=footer_row, column=1,
                 value="GUAPO ERPWeb · Gestão Financeira Estratégica")
    fc.fill = fill(C_BG_TITLE)
    fc.font = Font(color=C_DIM, size=9, italic=True, name="Segoe UI")
    fc.alignment = Alignment(horizontal='center', vertical='center')

    # Tab color
    ws.sheet_properties.tabColor = C_GREEN

    # ── Serialize and send ────────────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"GUAPO_DRE_{now.strftime('%Y%m%d_%H%M')}.xlsx"

    return dcc.send_bytes(buf.read(), filename)


if __name__ == "__main__":
    app.run(debug=True)