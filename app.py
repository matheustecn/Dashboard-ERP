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
server = app.server  # required for Railway / Render / Gunicorn

# ── DADOS MOCK ────────────────────────────────────────────────────────────────
MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

RECEITA = [142000,158000,135000,172000,189000,201000,178000,215000,198000,234000,221000,267000]
DESPESA = [ 98000,112000, 95000,118000,125000,131000,119000,142000,128000,151000,139000,168000]
LUCRO   = [r - d for r, d in zip(RECEITA, DESPESA)]

TRANSACOES_MOCK = [
    {"id":"#001","data":"15/12/2025","descricao":"Venda — Cliente Alpha S.A.",   "categoria":"Receita", "valor":"R$ 45.200","variacao":"+18%","status":"Confirmado"},
    {"id":"#002","data":"14/12/2025","descricao":"Folha de Pagamento Dez/25",    "categoria":"Despesa", "valor":"R$ 32.500","variacao":"—",   "status":"Processado"},
    {"id":"#003","data":"13/12/2025","descricao":"Venda — Beta Tecnologia Ltda", "categoria":"Receita", "valor":"R$ 18.750","variacao":"+5%", "status":"Confirmado"},
    {"id":"#004","data":"12/12/2025","descricao":"Aluguel Escritório — Dez",     "categoria":"Despesa", "valor":"R$  8.900","variacao":"—",   "status":"Processado"},
    {"id":"#005","data":"11/12/2025","descricao":"Serviços — Gamma Corp",        "categoria":"Receita", "valor":"R$ 29.100","variacao":"+9%", "status":"Pendente"},
    {"id":"#006","data":"10/12/2025","descricao":"Fornecedor Insumos Ltda",      "categoria":"Despesa", "valor":"R$ 14.320","variacao":"—",   "status":"Processado"},
    {"id":"#007","data":"09/12/2025","descricao":"Venda — Delta Indústria",      "categoria":"Receita", "valor":"R$ 67.400","variacao":"+22%","status":"Confirmado"},
    {"id":"#008","data":"08/12/2025","descricao":"Marketing Digital — Nov",      "categoria":"Despesa", "valor":"R$  5.600","variacao":"—",   "status":"Processado"},
    {"id":"#009","data":"07/12/2025","descricao":"Venda — Epsilon Global",       "categoria":"Receita", "valor":"R$ 38.900","variacao":"+11%","status":"Confirmado"},
    {"id":"#010","data":"06/12/2025","descricao":"Manutenção Infraestrutura",    "categoria":"Despesa", "valor":"R$  9.200","variacao":"—",   "status":"Processado"},
]

DRE_MOCK = [
    {"conta":"RECEITA BRUTA",             "jan":"267.000","fev":"242.000","mar":"198.000","total":"707.000","tipo":"receita_bruta"},
    {"conta":"  Vendas de Produtos",      "jan":"189.000","fev":"171.000","mar":"138.000","total":"498.000","tipo":"item"},
    {"conta":"  Prestação de Serviços",   "jan":" 78.000","fev":" 71.000","mar":" 60.000","total":"209.000","tipo":"item"},
    {"conta":"( - ) DEDUÇÕES",            "jan":"(32.000)","fev":"(29.000)","mar":"(23.000)","total":"(84.000)","tipo":"deducao"},
    {"conta":"  Impostos s/ Vendas",      "jan":"(21.000)","fev":"(19.000)","mar":"(15.000)","total":"(55.000)","tipo":"item"},
    {"conta":"  Devoluções",              "jan":"(11.000)","fev":"(10.000)","mar":" (8.000)","total":"(29.000)","tipo":"item"},
    {"conta":"RECEITA LÍQUIDA",           "jan":"235.000","fev":"213.000","mar":"175.000","total":"623.000","tipo":"subtotal"},
    {"conta":"( - ) CUSTO DAS VENDAS",    "jan":"(98.000)","fev":"(89.000)","mar":"(73.000)","total":"(260.000)","tipo":"deducao"},
    {"conta":"LUCRO BRUTO",               "jan":"137.000","fev":"124.000","mar":"102.000","total":"363.000","tipo":"subtotal"},
    {"conta":"( - ) DESPESAS OPERAC.",    "jan":"(69.000)","fev":"(63.000)","mar":"(51.000)","total":"(183.000)","tipo":"deducao"},
    {"conta":"  Despesas de Pessoal",     "jan":"(42.000)","fev":"(38.000)","mar":"(31.000)","total":"(111.000)","tipo":"item"},
    {"conta":"  Despesas Administrativas","jan":"(15.000)","fev":"(14.000)","mar":"(11.000)","total":"(40.000)","tipo":"item"},
    {"conta":"  Despesas de Marketing",   "jan":"( 8.000)","fev":"( 7.000)","mar":"( 5.000)","total":"(20.000)","tipo":"item"},
    {"conta":"  Outras Despesas",         "jan":"( 4.000)","fev":"( 4.000)","mar":"( 4.000)","total":"(12.000)","tipo":"item"},
    {"conta":"EBITDA",                    "jan":" 68.000","fev":" 61.000","mar":" 51.000","total":"180.000","tipo":"ebitda"},
    {"conta":"( - ) Depreciação/Amort.",  "jan":"( 5.200)","fev":"( 5.200)","mar":"( 5.200)","total":"(15.600)","tipo":"item"},
    {"conta":"EBIT",                      "jan":" 62.800","fev":" 55.800","mar":" 45.800","total":"164.400","tipo":"subtotal"},
    {"conta":"( - ) Resultado Financeiro","jan":"( 2.100)","fev":"( 1.900)","mar":"( 1.600)","total":"( 5.600)","tipo":"item"},
    {"conta":"LUCRO ANTES DO IR",         "jan":" 60.700","fev":" 53.900","mar":" 44.200","total":"158.800","tipo":"subtotal"},
    {"conta":"( - ) IRPJ/CSLL",           "jan":"(18.210)","fev":"(16.170)","mar":"(13.260)","total":"(47.640)","tipo":"deducao"},
    {"conta":"LUCRO LÍQUIDO",             "jan":" 42.490","fev":" 37.730","mar":" 30.940","total":"111.160","tipo":"lucro"},
]

# ── TEMA DOS GRÁFICOS ─────────────────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Sora, sans-serif', color='#8fa894', size=11),
    margin=dict(l=16, r=16, t=16, b=16),
    showlegend=True,
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8fa894', size=10),
                orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
    xaxis=dict(gridcolor='rgba(255,255,255,0.04)', zerolinecolor='rgba(255,255,255,0.06)',
               tickfont=dict(size=10), linecolor='rgba(255,255,255,0.06)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.04)', zerolinecolor='rgba(255,255,255,0.06)',
               tickfont=dict(size=10), linecolor='rgba(255,255,255,0.06)'),
    hoverlabel=dict(bgcolor='#1a1f1c', bordercolor='#2a3330',
                    font=dict(family='Space Mono', color='#e8ede9', size=11)),
)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def kpi_card(label, value, sub, badge_text, badge_cls, value_cls=""):
    return html.Div(className='kpi-card', children=[
        html.Div(className='kpi-top', children=[
            html.Div(label, className='kpi-label'),
            html.Div(badge_text, className=f'kpi-badge {badge_cls}'),
        ]),
        html.Div(value, className=f'kpi-value {value_cls}'),
        html.Div(sub, className='kpi-sub'),
        html.Div(className='kpi-bar'),
    ])

def chart_card(eyebrow, title, figure, height=300):
    return html.Div(style={
        'background':'#131714','border':'1px solid rgba(255,255,255,0.07)',
        'borderRadius':'10px','overflow':'hidden',
    }, children=[
        html.Div(style={
            'padding':'16px 22px 12px','borderBottom':'1px solid rgba(255,255,255,0.06)',
            'background':'#1a1f1c',
        }, children=[
            html.Div(eyebrow, style={
                'fontFamily':"'Space Mono',monospace",'fontSize':'9px',
                'color':'#3ddc84','textTransform':'uppercase','letterSpacing':'3px','marginBottom':'3px',
            }),
            html.Div(title, style={
                'fontFamily':"'Playfair Display',serif",'fontSize':'15px',
                'fontWeight':'700','color':'#e8ede9',
            }),
        ]),
        dcc.Graph(figure=figure, config={'displayModeBar':False}, style={'height':f'{height}px'}),
    ])

def stat_row(label, value, pct, up=True):
    color = '#3ddc84' if up else '#ff5c5c'
    arrow = '↑' if up else '↓'
    r,g,b = (61,220,132) if up else (255,92,92)
    return html.Div(style={
        'display':'flex','alignItems':'center','justifyContent':'space-between',
        'padding':'12px 0','borderBottom':'1px solid rgba(255,255,255,0.05)',
    }, children=[
        html.Div(label, style={'fontSize':'13px','color':'#8fa894'}),
        html.Div(style={'display':'flex','alignItems':'center','gap':'12px'}, children=[
            html.Div(value, style={'fontFamily':"'Space Mono',monospace",'fontSize':'12px','color':'#e8ede9'}),
            html.Div(f'{arrow} {pct}', style={
                'fontFamily':"'Space Mono',monospace",'fontSize':'10px','color':color,
                'background':f'rgba({r},{g},{b},0.1)','padding':'3px 8px','borderRadius':'4px',
            }),
        ]),
    ])

# ── FUNÇÃO DE GERAÇÃO DO EXCEL ────────────────────────────────────────────────
def gerar_excel():
    wb = openpyxl.Workbook()

    C_GREEN = "FF3DDC84"; C_DARK = "FF0D0F0E"; C_BG2 = "FF131714"
    C_BG3 = "FF1A1F1C"; C_TEXT = "FFE8EDE9"; C_GOLD = "FFC9A84C"
    C_RED = "FFFF5C5C"; C_MID = "FF8FA894"

    def hdr_font(bold=True, size=11, color=C_TEXT):
        return Font(name='Calibri', bold=bold, size=size, color=color)
    def fill(hex_color):
        return PatternFill("solid", fgColor=hex_color)
    def center():
        return Alignment(horizontal='center', vertical='center', wrap_text=True)
    def thin_border():
        s = Side(style='thin', color="FF2A3330")
        return Border(left=s, right=s, top=s, bottom=s)

    # ABA 1: DASHBOARD
    ws = wb.active
    ws.title = "Dashboard"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions['A'].width = 3

    ws.merge_cells('B2:H3')
    ws['B2'] = "GUAPO ERP · Dashboard Financeiro 2025"
    ws['B2'].font = Font(name='Calibri', bold=True, size=18, color=C_GREEN)
    ws['B2'].fill = fill(C_DARK)
    ws['B2'].alignment = Alignment(horizontal='left', vertical='center')
    ws.merge_cells('B4:H4')
    ws['B4'] = f"Gerado em {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}"
    ws['B4'].font = Font(name='Calibri', size=9, color=C_MID)
    ws['B4'].fill = fill(C_DARK)
    ws.row_dimensions[2].height = 36
    ws.row_dimensions[4].height = 16
    ws.row_dimensions[5].height = 10

    kpis = [
        ("Receita Total 2025", "R$ 2.310.000", C_GREEN, "+14% vs 2024"),
        ("Despesas Totais",    "R$ 1.526.000", C_RED,   "+9% vs 2024"),
        ("Lucro Líquido",      "R$   784.000", C_GOLD,  "+21% vs 2024"),
        ("Margem Líquida",     "33,9%",        C_TEXT,  "Meta: 30%  ✓"),
    ]
    for idx, (col, (lbl, val, val_color, sub)) in enumerate(zip(['B','D','F','H'], kpis)):
        nc = chr(ord(col)+1)
        for r in range(6, 10):
            ws.merge_cells(f'{col}{r}:{nc}{r}')
            ws[f'{col}{r}'].fill = fill(C_BG2)
        ws[f'{col}6'].value = "■ KPI"
        ws[f'{col}6'].font = Font(name='Calibri', size=8, color=C_MID, bold=True)
        ws[f'{col}6'].alignment = Alignment(horizontal='center', vertical='center')
        ws[f'{col}7'].value = lbl
        ws[f'{col}7'].font = Font(name='Calibri', size=9, color=C_MID)
        ws[f'{col}7'].alignment = Alignment(horizontal='center', vertical='center')
        ws[f'{col}8'].value = val
        ws[f'{col}8'].font = Font(name='Calibri', bold=True, size=16, color=val_color)
        ws[f'{col}8'].alignment = Alignment(horizontal='center', vertical='center')
        ws[f'{col}9'].value = sub
        ws[f'{col}9'].font = Font(name='Calibri', size=9, color=C_MID, italic=True)
        ws[f'{col}9'].alignment = Alignment(horizontal='center', vertical='center')
    for r in [6,7,8,9,10]:
        ws.row_dimensions[r].height = 22 if r==8 else 18

    ws.row_dimensions[11].height = 8
    ws.row_dimensions[12].height = 24
    headers_d = ["Mês","Receita","Despesa","Lucro","Margem %"]
    start_cols = [2,3,4,5,6]
    for ci, h in zip(start_cols, headers_d):
        cell = ws.cell(row=12, column=ci)
        cell.value = h
        cell.font = hdr_font(bold=True, size=10, color=C_DARK)
        cell.fill = fill(C_GREEN)
        cell.alignment = center()
        cell.border = thin_border()

    for i, (mes, rec, des, luc) in enumerate(zip(MESES, RECEITA, DESPESA, LUCRO)):
        row = 13 + i
        ws.row_dimensions[row].height = 18
        bg = C_BG3 if i % 2 == 0 else C_BG2
        margem = f"{(luc/rec*100):.1f}%"
        valores = [mes, f"R$ {rec:,.0f}", f"R$ {des:,.0f}", f"R$ {luc:,.0f}", margem]
        for ci, v in zip(start_cols, valores):
            cell = ws.cell(row=row, column=ci)
            cell.value = v
            cell.fill = fill(bg)
            cell.alignment = center()
            cell.border = thin_border()
            if ci == 5:
                cell.font = Font(name='Calibri', bold=True, size=10, color=C_GREEN if luc >= 0 else C_RED)
            elif ci == 6:
                cell.font = Font(name='Calibri', size=10, color=C_GOLD)
            else:
                cell.font = Font(name='Calibri', size=10, color=C_TEXT)

    for ci in start_cols:
        ws.column_dimensions[get_column_letter(ci)].width = 18

    # ABA 2: DRE
    ws2 = wb.create_sheet("DRE")
    ws2.sheet_view.showGridLines = False
    ws2.column_dimensions['A'].width = 3
    ws2.merge_cells('B2:G3')
    ws2['B2'] = "DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO — 2025"
    ws2['B2'].font = Font(name='Calibri', bold=True, size=14, color=C_GREEN)
    ws2['B2'].fill = fill(C_DARK)
    ws2['B2'].alignment = Alignment(horizontal='left', vertical='center')
    ws2.row_dimensions[2].height = 32

    cols_dre = ['B','C','D','E','F','G']
    hdrs_dre = ['Conta','Jan','Fev','Mar','Abr (est.)','Total Trim.']
    ws2.row_dimensions[5].height = 22
    for ci, h in zip(cols_dre, hdrs_dre):
        c = ws2[f'{ci}5']
        c.value = h
        c.font = hdr_font(bold=True, size=10, color=C_DARK)
        c.fill = fill(C_GREEN)
        c.alignment = center()
        c.border = thin_border()

    tipo_styles_xl = {
        'receita_bruta': (C_GREEN, C_BG2, True,  12),
        'deducao':       (C_RED,   C_BG3, False,  10),
        'subtotal':      (C_GOLD,  C_BG2, True,   11),
        'ebitda':        (C_GREEN, C_BG3, True,   12),
        'lucro':         (C_GREEN, C_DARK,True,   13),
        'item':          (C_TEXT,  C_BG3, False,  10),
    }
    for i, row_data in enumerate(DRE_MOCK):
        row = 6 + i
        ws2.row_dimensions[row].height = 18
        tipo = row_data['tipo']
        txt_color, bg_color, bold, size = tipo_styles_xl.get(tipo, (C_TEXT, C_BG3, False, 10))
        values = [row_data['conta'], row_data['jan'], row_data['fev'],
                  row_data['mar'], '—', row_data['total']]
        for ci, v in zip(cols_dre, values):
            c = ws2.cell(row=row, column=ord(ci)-64)
            c.value = v
            c.font = Font(name='Calibri', bold=bold, size=size, color=txt_color)
            c.fill = fill(bg_color)
            c.alignment = Alignment(horizontal='left' if ci=='B' else 'right', vertical='center')
            c.border = thin_border()
    ws2.column_dimensions['B'].width = 34
    for ci in ['C','D','E','F','G']:
        ws2.column_dimensions[ci].width = 16

    # ABA 3: TRANSAÇÕES
    ws3 = wb.create_sheet("Transações")
    ws3.sheet_view.showGridLines = False
    ws3.column_dimensions['A'].width = 3
    ws3.merge_cells('B2:H3')
    ws3['B2'] = "HISTÓRICO DE TRANSAÇÕES — DEZEMBRO 2025"
    ws3['B2'].font = Font(name='Calibri', bold=True, size=14, color=C_GREEN)
    ws3['B2'].fill = fill(C_DARK)
    ws3['B2'].alignment = Alignment(horizontal='left', vertical='center')
    ws3.row_dimensions[2].height = 32

    hdrs_txn = ['ID','Data','Descrição','Categoria','Valor','Variação','Status']
    cols_txn = ['B','C','D','E','F','G','H']
    ws3.row_dimensions[5].height = 22
    for ci, h in zip(cols_txn, hdrs_txn):
        c = ws3[f'{ci}5']
        c.value = h
        c.font = hdr_font(bold=True, size=10, color=C_DARK)
        c.fill = fill(C_GREEN)
        c.alignment = center()
        c.border = thin_border()

    for i, t in enumerate(TRANSACOES_MOCK):
        row = 6 + i
        ws3.row_dimensions[row].height = 18
        bg = C_BG3 if i % 2 == 0 else C_BG2
        vals = [t['id'],t['data'],t['descricao'],t['categoria'],t['valor'],t['variacao'],t['status']]
        for ci, v in zip(cols_txn, vals):
            c = ws3.cell(row=row, column=ord(ci)-64)
            c.value = v
            c.fill = fill(bg)
            c.border = thin_border()
            c.alignment = Alignment(horizontal='center', vertical='center')
            if ci == 'E':
                c.font = Font(name='Calibri', size=10, color=C_GREEN if v=='Receita' else C_RED)
            elif ci == 'F':
                c.font = Font(name='Calibri', size=10, bold=True, color=C_TEXT)
            elif ci == 'G':
                c.font = Font(name='Calibri', size=10, color=C_GOLD)
            elif ci == 'H':
                sc = {'Confirmado':C_GREEN,'Processado':C_GOLD,'Pendente':C_RED}.get(v, C_TEXT)
                c.font = Font(name='Calibri', size=10, color=sc)
            else:
                c.font = Font(name='Calibri', size=10, color=C_TEXT)

    widths_txn = [8,14,38,14,16,12,14]
    for ci, w in zip(cols_txn, widths_txn):
        ws3.column_dimensions[ci].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()

# ── INDEX STRING ──────────────────────────────────────────────────────────────
app.index_string = '''<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>GUAPO · ERPWeb</title>
        {%favicon%}
        {%css%}
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Sora:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
            :root{
                --bg:#0d0f0e;--bg2:#131714;--bg3:#1a1f1c;--bg4:#222720;
                --border:rgba(255,255,255,0.07);--border-lit:rgba(61,220,132,0.25);
                --green:#3ddc84;--green-dim:#2ab86a;--green-glow:rgba(61,220,132,0.15);
                --green-deep:rgba(61,220,132,0.06);--gold:#c9a84c;--gold-light:#e8c97a;
                --text:#e8ede9;--text-mid:#8fa894;--text-dim:#4d5e52;
                --red:#ff5c5c;--blue:#5c9eff;
                --shadow:0 0 0 1px rgba(255,255,255,0.04),0 8px 32px rgba(0,0,0,0.4);
                --shadow-lg:0 0 0 1px rgba(255,255,255,0.05),0 24px 64px rgba(0,0,0,0.6);
                --r:10px;--t:0.3s cubic-bezier(0.16,1,0.3,1);
            }
            html{scroll-behavior:smooth}
            body{font-family:'Sora',sans-serif;background:var(--bg);color:var(--text);-webkit-font-smoothing:antialiased;min-height:100vh}
            ::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:var(--bg2)}
            ::-webkit-scrollbar-thumb{background:var(--bg4);border-radius:3px}
            ::-webkit-scrollbar-thumb:hover{background:var(--green-dim)}

            /* LOGIN */
            .screen-login{min-height:100vh;display:flex;flex-direction:column;position:relative;overflow:hidden;background:var(--bg)}
            .screen-login::before{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(61,220,132,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(61,220,132,0.03) 1px,transparent 1px);background-size:48px 48px;animation:grid-drift 20s linear infinite;pointer-events:none}
            @keyframes grid-drift{0%{background-position:0 0}100%{background-position:48px 48px}}
            .screen-login::after{content:'';position:absolute;top:-30vh;right:-20vw;width:70vw;height:70vw;border-radius:50%;background:radial-gradient(circle,rgba(61,220,132,0.06) 0%,transparent 65%);pointer-events:none}
            .login-top-bar{position:relative;z-index:2;padding:18px 48px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
            .login-top-brand{font-family:'Playfair Display',serif;font-size:20px;font-weight:700;color:var(--green)}
            .login-top-tag{font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);text-transform:uppercase;letter-spacing:3px}
            .login-top-dot{width:8px;height:8px;border-radius:50%;background:var(--green);box-shadow:0 0 12px var(--green);animation:blink 2s ease-in-out infinite}
            @keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}
            .login-center{flex:1;display:flex;align-items:center;justify-content:center;position:relative;z-index:2;padding:40px 20px}
            .login-panel{width:440px;animation:panel-in 0.7s cubic-bezier(0.16,1,0.3,1) both}
            @keyframes panel-in{from{opacity:0;transform:translateY(32px) scale(0.97)}to{opacity:1;transform:translateY(0) scale(1)}}
            .login-eyebrow{font-family:'Space Mono',monospace;font-size:10px;color:var(--green);text-transform:uppercase;letter-spacing:4px;margin-bottom:16px;display:flex;align-items:center;gap:10px}
            .login-eyebrow::before{content:'';display:block;width:28px;height:1px;background:var(--green);opacity:0.5}
            .login-headline{font-family:'Playfair Display',serif;font-size:52px;font-weight:900;line-height:1;letter-spacing:-2px;margin-bottom:8px;color:var(--text)}
            .login-headline em{font-style:italic;color:var(--green)}
            .login-desc{font-size:13px;color:var(--text-mid);font-weight:300;margin-bottom:40px;letter-spacing:0.3px}
            .login-card{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:36px;box-shadow:var(--shadow-lg);position:relative;overflow:hidden}
            .login-card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,var(--green),transparent);opacity:0.4}
            .field-group{margin-bottom:20px}
            .field-label{font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;display:block}
            .input-field{width:100%!important;padding:14px 18px!important;border-radius:8px!important;border:1px solid var(--border)!important;font-family:'Sora',sans-serif!important;font-size:14px!important;color:var(--text)!important;background:var(--bg3)!important;outline:none!important;display:block!important;transition:border-color var(--t),box-shadow var(--t),background var(--t)!important}
            .input-field:focus{border-color:var(--green-dim)!important;background:var(--bg4)!important;box-shadow:0 0 0 3px var(--green-deep),0 0 20px rgba(61,220,132,0.05)!important}
            .input-field::placeholder{color:var(--text-dim)!important}
            .btn-login{width:100%;margin-top:8px;padding:16px 24px;background:var(--green);color:var(--bg);border:none;border-radius:8px;cursor:pointer;font-family:'Space Mono',monospace;font-weight:700;font-size:12px;letter-spacing:3px;text-transform:uppercase;transition:all var(--t)}
            .btn-login:hover{background:var(--gold-light);transform:translateY(-1px);box-shadow:0 8px 24px rgba(61,220,132,0.3)}
            .login-error{margin-top:16px;min-height:20px;font-family:'Space Mono',monospace;font-size:11px;color:var(--red);text-align:center;letter-spacing:1px}
            .login-footer-note{margin-top:20px;text-align:center;font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);letter-spacing:1px}

            /* DASHBOARD */
            .screen-dash{background:var(--bg);min-height:100vh}
            .dash-layout{display:flex}
            .sidebar{width:240px;flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;position:fixed;top:0;left:0;bottom:0;z-index:50;overflow-y:auto}
            .sidebar-brand{padding:28px 24px 22px;border-bottom:1px solid var(--border)}
            .sidebar-logo{font-family:'Playfair Display',serif;font-size:30px;font-weight:900;color:var(--text);letter-spacing:-1px;line-height:1}
            .sidebar-logo span{color:var(--green)}
            .sidebar-sub{font-family:'Space Mono',monospace;font-size:9px;color:var(--text-dim);text-transform:uppercase;letter-spacing:3px;margin-top:5px}
            .sidebar-section{padding:22px 14px 8px}
            .sidebar-section-label{font-family:'Space Mono',monospace;font-size:9px;color:var(--text-dim);text-transform:uppercase;letter-spacing:3px;padding:0 10px;margin-bottom:8px}
            .nav-item{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:8px;cursor:pointer;margin-bottom:2px;transition:background var(--t),color var(--t);font-size:13px;font-weight:500;color:var(--text-mid);border:1px solid transparent;user-select:none}
            .nav-item:hover{background:var(--bg3);color:var(--text)}
            .nav-item.active{background:var(--green-deep);border-color:var(--border-lit);color:var(--green)}
            .nav-icon{font-size:15px;width:20px;text-align:center}
            .sidebar-bottom{margin-top:auto;padding:18px 14px;border-top:1px solid var(--border)}
            .sidebar-user{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:8px;background:var(--bg3)}
            .user-avatar{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,var(--green-dim),var(--gold));display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:var(--bg);flex-shrink:0}
            .user-name{font-size:13px;font-weight:600;color:var(--text)}
            .user-role{font-family:'Space Mono',monospace;font-size:9px;color:var(--text-dim);text-transform:uppercase;letter-spacing:1px}
            .dash-main{margin-left:240px;flex:1;min-height:100vh}
            .topbar{height:64px;flex-shrink:0;border-bottom:1px solid var(--border);padding:0 40px;display:flex;align-items:center;justify-content:space-between;background:rgba(13,15,14,0.9);backdrop-filter:blur(16px);position:sticky;top:0;z-index:40}
            .topbar-title{font-size:15px;font-weight:600;color:var(--text)}
            .topbar-subtitle{font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);letter-spacing:1px;margin-top:2px}
            .topbar-actions{display:flex;align-items:center;gap:12px}
            .status-chip{display:flex;align-items:center;gap:8px;padding:7px 14px;border-radius:100px;background:var(--green-deep);border:1px solid var(--border-lit);font-family:'Space Mono',monospace;font-size:10px;color:var(--green);text-transform:uppercase;letter-spacing:2px}
            .status-dot{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 2s ease-in-out infinite}
            .topbar-date{font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);letter-spacing:1px}
            .main-content{padding:36px 40px;flex:1}
            .upload-area{border:1px dashed rgba(61,220,132,0.2);border-radius:var(--r);background:var(--green-deep);padding:18px 24px;cursor:pointer;margin-bottom:32px;transition:border-color var(--t),background var(--t);display:flex;align-items:center;justify-content:center;gap:12px}
            .upload-area:hover{border-color:rgba(61,220,132,0.4);background:rgba(61,220,132,0.08)}
            .upload-icon{font-size:18px}
            .upload-text{font-size:13px;color:var(--text-mid);font-weight:400}
            .upload-text strong{color:var(--green);font-weight:600}
            .section-header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:24px}
            .section-eyebrow{font-family:'Space Mono',monospace;font-size:9px;color:var(--green);text-transform:uppercase;letter-spacing:3px;margin-bottom:6px}
            .section-title{font-family:'Playfair Display',serif;font-size:24px;font-weight:700;color:var(--text);letter-spacing:-0.5px}
            .section-period{font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);letter-spacing:1px}
            .kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
            .kpi-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);padding:24px 22px;position:relative;overflow:hidden;transition:border-color var(--t),transform var(--t),box-shadow var(--t);cursor:default}
            .kpi-card:hover{border-color:var(--border-lit);transform:translateY(-2px);box-shadow:0 12px 32px rgba(0,0,0,0.3)}
            .kpi-card::after{content:'';position:absolute;top:0;right:0;width:48px;height:48px;background:radial-gradient(circle at top right,rgba(61,220,132,0.08),transparent 70%);pointer-events:none}
            .kpi-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
            .kpi-label{font-family:'Space Mono',monospace;font-size:9px;color:var(--text-dim);text-transform:uppercase;letter-spacing:2px}
            .kpi-badge{font-family:'Space Mono',monospace;font-size:9px;padding:3px 8px;border-radius:4px;font-weight:700;text-transform:uppercase;letter-spacing:1px}
            .kpi-badge.up{background:rgba(61,220,132,0.12);color:var(--green)}
            .kpi-badge.wait{background:rgba(201,168,76,0.12);color:var(--gold)}
            .kpi-badge.down{background:rgba(255,92,92,0.12);color:var(--red)}
            .kpi-value{font-family:'Playfair Display',serif;font-size:28px;font-weight:700;color:var(--text);line-height:1;letter-spacing:-0.5px}
            .kpi-value.green{color:var(--green)}
            .kpi-value.gold{color:var(--gold-light)}
            .kpi-value.red{color:var(--red)}
            .kpi-sub{font-family:'Space Mono',monospace;font-size:10px;color:var(--text-dim);margin-top:8px;letter-spacing:0.5px}
            .kpi-bar{position:absolute;bottom:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--green),transparent);opacity:0;transition:opacity var(--t)}
            .kpi-card:hover .kpi-bar{opacity:1}
            .divider{height:1px;background:var(--border);margin:28px 0}
            .charts-grid-2{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-bottom:24px}
            .dre-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
            .dre-card-header{padding:18px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:var(--bg3)}
            .dre-card-title{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--text-mid)}
            .dre-card-title span{color:var(--green)}
            .dre-pill{font-family:'Space Mono',monospace;font-size:9px;color:var(--gold);background:rgba(201,168,76,0.1);border:1px solid rgba(201,168,76,0.2);padding:4px 12px;border-radius:4px;text-transform:uppercase;letter-spacing:1px}
            .table-card{background:var(--bg2);border:1px solid var(--border);border-radius:var(--r);overflow:hidden}
            .table-header{padding:18px 24px;border-bottom:1px solid var(--border);background:var(--bg3);display:flex;align-items:center;justify-content:space-between}
            .table-header-title{font-family:'Space Mono',monospace;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:2px;color:var(--text-mid)}
            .btn-action{padding:8px 18px;border-radius:6px;border:1px solid var(--border-lit);background:var(--green-deep);color:var(--green);font-family:'Space Mono',monospace;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:2px;cursor:pointer;transition:all var(--t)}
            .btn-action:hover{background:var(--green-glow);border-color:var(--green);transform:translateY(-1px)}
            .btn-danger{padding:8px 18px;border-radius:6px;border:1px solid rgba(255,92,92,0.3);background:rgba(255,92,92,0.06);color:var(--red);font-family:'Space Mono',monospace;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:2px;cursor:pointer;transition:all var(--t)}
            .btn-danger:hover{background:rgba(255,92,92,0.12);transform:translateY(-1px)}
            .toast{position:fixed;bottom:28px;right:28px;background:var(--bg3);border:1px solid var(--border-lit);border-radius:10px;padding:14px 20px;display:flex;align-items:center;gap:12px;font-size:13px;color:var(--text);box-shadow:var(--shadow-lg);z-index:9999;animation:toast-in 0.4s cubic-bezier(0.16,1,0.3,1)}
            @keyframes toast-in{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
            .modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.75);backdrop-filter:blur(8px);z-index:200;display:flex;align-items:center;justify-content:center;animation:fade-in 0.2s ease}
            @keyframes fade-in{from{opacity:0}to{opacity:1}}
            .modal-box{background:var(--bg2);border:1px solid var(--border);border-radius:16px;padding:36px;width:500px;box-shadow:var(--shadow-lg);position:relative;animation:modal-in 0.35s cubic-bezier(0.16,1,0.3,1)}
            @keyframes modal-in{from{opacity:0;transform:scale(0.94)}to{opacity:1;transform:scale(1)}}
            .modal-title{font-family:'Playfair Display',serif;font-size:22px;font-weight:700;color:var(--text);margin-bottom:6px}
            .modal-sub{font-size:13px;color:var(--text-mid);margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--border)}
            .modal-close{position:absolute;top:18px;right:22px;background:none;border:none;color:var(--text-dim);cursor:pointer;font-size:20px;line-height:1;transition:color var(--t)}
            .modal-close:hover{color:var(--text)}
            .config-row{display:flex;align-items:center;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--border)}
            .config-row:last-child{border-bottom:none;padding-bottom:0}
            .config-label{font-size:13px;font-weight:500;color:var(--text)}
            .config-sub{font-size:11px;color:var(--text-dim);margin-top:2px}
            .toggle{width:42px;height:24px;border-radius:12px;border:none;cursor:pointer;position:relative;transition:background var(--t);flex-shrink:0}
            .toggle.on{background:var(--green)}
            .toggle.off{background:var(--bg4);border:1px solid var(--border)}
            .toggle::after{content:'';position:absolute;top:4px;width:16px;height:16px;border-radius:50%;background:white;transition:left 0.2s}
            .toggle.on::after{left:22px}
            .toggle.off::after{left:4px}
            tr:hover td{background:rgba(255,255,255,0.02)!important}
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>{%config%}{%scripts%}{%renderer%}</footer>
    </body>
</html>'''

# ── LAYOUT ─────────────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Store(id='auth-status', data=False),
    dcc.Store(id='csv-store',   data=None),
    dcc.Store(id='active-tab',  data='tab-ind'),
    dcc.Interval(id='clock-tick', interval=60_000, n_intervals=0),
    dcc.Download(id='download-excel'),

    # TOAST
    html.Div(id='toast', style={'display':'none'}),

    # MODAL CONFIGURAÇÕES
    html.Div(id='modal-config-overlay', style={'display':'none'}, children=[
        html.Div(className='modal-overlay', children=[
            html.Div(className='modal-box', children=[
                html.Button("✕", id='btn-modal-config-close', className='modal-close'),
                html.Div("Configurações", className='modal-title'),
                html.Div("Preferências do sistema GUAPO ERP", className='modal-sub'),
                html.Div([
                    html.Div(className='config-row', children=[
                        html.Div([html.Div("Notificações em Tempo Real", className='config-label'),
                                  html.Div("Alertas de variação e alertas críticos", className='config-sub')]),
                        html.Button(id='toggle-notif', className='toggle on'),
                    ]),
                    html.Div(className='config-row', children=[
                        html.Div([html.Div("Tema Escuro", className='config-label'),
                                  html.Div("Interface em modo dark (padrão)", className='config-sub')]),
                        html.Button(id='toggle-dark', className='toggle on'),
                    ]),
                    html.Div(className='config-row', children=[
                        html.Div([html.Div("Exportação Automática", className='config-label'),
                                  html.Div("Gerar Excel ao importar CSV", className='config-sub')]),
                        html.Button(id='toggle-autoexp', className='toggle off'),
                    ]),
                    html.Div(className='config-row', children=[
                        html.Div([html.Div("Atualização Automática", className='config-label'),
                                  html.Div("Recarregar dados a cada 5 minutos", className='config-sub')]),
                        html.Button(id='toggle-auto', className='toggle off'),
                    ]),
                ]),
                html.Div(style={'marginTop':'24px','display':'flex','justifyContent':'flex-end'}, children=[
                    html.Button("Fechar", id='btn-modal-config-close2', className='btn-action'),
                ]),
            ])
        ])
    ]),

    # LOGIN
    html.Div(id='screen-login', className='screen-login', children=[
        html.Div(className='login-top-bar', children=[
            html.Div("GUAPO", className='login-top-brand'),
            html.Div("Sistema de Gestão Estratégica", className='login-top-tag'),
            html.Div(className='login-top-dot'),
        ]),
        html.Div(className='login-center', children=[
            html.Div(className='login-panel', children=[
                html.Div(["ACESSO", html.Span(" SEGURO")], className='login-eyebrow'),
                html.Div(["Dashboard ", html.Em("Financeiro")], className='login-headline'),
                html.P("Gestão estratégica de resultados e indicadores de performance.",
                       className='login-desc'),
                html.Div(className='login-card', children=[
                    html.Div(className='field-group', children=[
                        html.Div("Identificação", className='field-label'),
                        dcc.Input(id="user", type="text", placeholder="Usuário do sistema",
                                  className="input-field", debounce=False),
                    ]),
                    html.Div(className='field-group', children=[
                        html.Div("Autenticação", className='field-label'),
                        dcc.Input(id="pass", type="password", placeholder="••••••••••••",
                                  className="input-field", debounce=False),
                    ]),
                    html.Button("ENTRAR NO SISTEMA →", id="btn-login", className="btn-login"),
                    html.Div(id="out-login", className="login-error"),
                ]),
                html.Div("Credenciais: admin / 123", className='login-footer-note'),
            ])
        ]),
    ]),

    # DASHBOARD
    html.Div(id='screen-dash', className='screen-dash', style={'display':'none'}, children=[
        html.Div(className='dash-layout', children=[

            # SIDEBAR
            html.Div(className='sidebar', children=[
                html.Div(className='sidebar-brand', children=[
                    html.Div(["GUAP", html.Span("O")], className='sidebar-logo'),
                    html.Div("ERP · Dashboard Financeiro", className='sidebar-sub'),
                ]),
                html.Div(className='sidebar-section', children=[
                    html.Div("Principal", className='sidebar-section-label'),
                    html.Div(id='nav-ind',    children=[html.Span("📊", className='nav-icon'), "Indicadores"],   className='nav-item active'),
                    html.Div(id='nav-charts', children=[html.Span("📈", className='nav-icon'), "Gráficos"],      className='nav-item'),
                    html.Div(id='nav-dre',    children=[html.Span("📋", className='nav-icon'), "DRE Completo"],  className='nav-item'),
                    html.Div(id='nav-txn',    children=[html.Span("💳", className='nav-icon'), "Transações"],    className='nav-item'),
                ]),
                html.Div(className='sidebar-section', children=[
                    html.Div("Ferramentas", className='sidebar-section-label'),
                    html.Div(id='nav-export', children=[html.Span("⬇️", className='nav-icon'), "Exportar Excel"], className='nav-item'),
                    html.Div(id='nav-config', children=[html.Span("⚙️", className='nav-icon'), "Configurações"],  className='nav-item'),
                    html.Div(id='nav-logout', children=[html.Span("🚪", className='nav-icon'), "Sair"],           className='nav-item'),
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
                html.Div(className='topbar', children=[
                    html.Div([
                        html.Div(id='topbar-title', children="Visão Geral Financeira", className='topbar-title'),
                        html.Div(id='topbar-subtitle', children="Exercício 2025 · Atualizado agora", className='topbar-subtitle'),
                    ]),
                    html.Div(className='topbar-actions', children=[
                        html.Div(id='topbar-date', className='topbar-date'),
                        html.Div([html.Div(className='status-dot'), "SISTEMA ATIVO"], className='status-chip'),
                    ]),
                ]),
                html.Div(id='main-content', className='main-content'),
            ]),
        ]),
    ]),
])

# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

# LOGIN
@app.callback(
    Output('screen-login','style'),
    Output('screen-dash','style'),
    Output('out-login','children'),
    Input('btn-login','n_clicks'),
    State('user','value'), State('pass','value'),
    prevent_initial_call=True,
)
def do_login(n, u, p):
    if u == 'admin' and p == '123':
        return {'display':'none'}, {'display':'block'}, ''
    return {'display':'flex'}, {'display':'none'}, '✕  Credenciais inválidas'

# LOGOUT
@app.callback(
    Output('screen-login','style', allow_duplicate=True),
    Output('screen-dash','style',  allow_duplicate=True),
    Input('nav-logout','n_clicks'),
    prevent_initial_call=True,
)
def do_logout(_):
    return {'display':'flex'}, {'display':'none'}

# RELÓGIO
@app.callback(
    Output('topbar-date','children'),
    Input('clock-tick','n_intervals'),
)
def update_clock(_):
    return datetime.datetime.now().strftime('%d/%m/%Y  %H:%M')

# NAVEGAÇÃO SIDEBAR
@app.callback(
    Output('active-tab','data'),
    Output('nav-ind','className'),
    Output('nav-charts','className'),
    Output('nav-dre','className'),
    Output('nav-txn','className'),
    Output('topbar-title','children'),
    Output('topbar-subtitle','children'),
    Input('nav-ind','n_clicks'),
    Input('nav-charts','n_clicks'),
    Input('nav-dre','n_clicks'),
    Input('nav-txn','n_clicks'),
    prevent_initial_call=True,
)
def nav_click(n1, n2, n3, n4):
    triggered = ctx.triggered_id
    tabs = {
        'nav-ind':    ('tab-ind',    'Indicadores & KPIs',  'Métricas estratégicas · Exercício 2025'),
        'nav-charts': ('tab-charts', 'Análise Gráfica',     'Visualização de dados financeiros'),
        'nav-dre':    ('tab-dre',    'DRE Completo',        'Demonstração do Resultado do Exercício'),
        'nav-txn':    ('tab-txn',    'Transações Recentes', 'Histórico de entradas e saídas'),
    }
    tab, title, sub = tabs.get(triggered, ('tab-ind','Dashboard',''))
    cls = {k: 'nav-item active' if k == triggered else 'nav-item' for k in tabs}
    return tab, cls['nav-ind'], cls['nav-charts'], cls['nav-dre'], cls['nav-txn'], title, sub

# MODAL CONFIGURAÇÕES
@app.callback(
    Output('modal-config-overlay','style'),
    Input('nav-config','n_clicks'),
    Input('btn-modal-config-close','n_clicks'),
    Input('btn-modal-config-close2','n_clicks'),
    prevent_initial_call=True,
)
def toggle_modal_config(*_):
    return {'display':'block'} if ctx.triggered_id == 'nav-config' else {'display':'none'}

# TOGGLES
@app.callback(Output('toggle-notif','className'), Input('toggle-notif','n_clicks'), State('toggle-notif','className'), prevent_initial_call=True)
def _t1(n, cls): return 'toggle off' if cls and 'on' in cls else 'toggle on'

@app.callback(Output('toggle-dark','className'), Input('toggle-dark','n_clicks'), State('toggle-dark','className'), prevent_initial_call=True)
def _t2(n, cls): return 'toggle off' if cls and 'on' in cls else 'toggle on'

@app.callback(Output('toggle-autoexp','className'), Input('toggle-autoexp','n_clicks'), State('toggle-autoexp','className'), prevent_initial_call=True)
def _t3(n, cls): return 'toggle off' if cls and 'on' in cls else 'toggle on'

@app.callback(Output('toggle-auto','className'), Input('toggle-auto','n_clicks'), State('toggle-auto','className'), prevent_initial_call=True)
def _t4(n, cls): return 'toggle off' if cls and 'on' in cls else 'toggle on'

# EXPORTAR EXCEL (sidebar) — só dispara com clique real em nav-export
@app.callback(
    Output('download-excel','data'),
    Output('toast','children'),
    Output('toast','style'),
    Input('nav-export','n_clicks'),
    prevent_initial_call=True,
)
def export_excel(n):
    if not n or n < 1:
        raise dash.exceptions.PreventUpdate
    data = gerar_excel()
    fname = f"GUAPO_ERP_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    toast = html.Div([
        html.Span("✓", style={'color':'#3ddc84','fontWeight':'700','fontSize':'16px'}),
        html.Span(f" Excel exportado — {fname}",
                  style={'fontFamily':"'Space Mono',monospace",'fontSize':'11px'}),
    ], className='toast')
    return dcc.send_bytes(data, fname), toast, {'display':'block'}

# HORAS EXTRAS — cálculo automático
@app.callback(
    Output('dre-he-result',        'children'),
    Output('dre-he-total-display', 'children'),
    Input('dre-he-qtd',   'value'),
    Input('dre-he-valor', 'value'),
    prevent_initial_call=False,
)
def calc_horas_extras(qtd, valor):
    if qtd and valor:
        total = float(qtd) * float(valor)
        fmt = f"R$ {total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return fmt, fmt
    return 'R$ —', 'R$ —'

# DRE — RECEITA TOTAL
@app.callback(
    Output('res-receita-total', 'children'),
    Input('dre-venda-vista','value'), Input('dre-venda-prazo','value'),
    Input('dre-or-juros','value'),    Input('dre-or-alug','value'),
    Input('dre-or-outras','value'),   Input('dre-or-fundos','value'),
    Input('dre-or-bonif','value'),
    prevent_initial_call=False,
)
def calc_receita_total(*vals):
    total = sum(float(v) for v in vals if v is not None)
    if total == 0: return 'R$ 0,00'
    return f"R$ {total:,.2f}".replace(',','X').replace('.', ',').replace('X','.')

# DRE — MARGEM DE CONTRIBUIÇÃO
@app.callback(
    Output('res-margem', 'children'),
    Input('dre-venda-vista','value'), Input('dre-venda-prazo','value'),
    Input('dre-or-juros','value'),    Input('dre-or-alug','value'),
    Input('dre-or-outras','value'),   Input('dre-or-fundos','value'),
    Input('dre-or-bonif','value'),
    Input('dre-c-bebidas','value'),   Input('dre-c-bolos','value'),
    Input('dre-c-carnes','value'),    Input('dre-c-cigarros','value'),
    Input('dre-c-conv','value'),      Input('dre-c-estcoz','value'),
    Input('dre-c-picoles','value'),   Input('dre-c-salgados','value'),
    Input('dre-c-insumos','value'),   Input('dre-c-embal','value'),
    Input('dre-c-recarga','value'),   Input('dre-c-bichos','value'),
    Input('dre-c-buffet','value'),
    prevent_initial_call=False,
)
def calc_margem(*vals):
    receita = sum(float(v) for v in vals[:7]  if v is not None)
    compras = sum(float(v) for v in vals[7:]  if v is not None)
    margem  = receita - compras
    if receita == 0 and compras == 0: return '—'
    return f"R$ {margem:,.2f}".replace(',','X').replace('.', ',').replace('X','.')

# DRE — LUCRO BRUTO / OPERACIONAL / LÍQUIDO
_REC_IDS  = ['dre-venda-vista','dre-venda-prazo','dre-or-juros','dre-or-alug',
             'dre-or-outras','dre-or-fundos','dre-or-bonif']
_COMP_IDS = ['dre-c-bebidas','dre-c-bolos','dre-c-carnes','dre-c-cigarros','dre-c-conv',
             'dre-c-estcoz','dre-c-picoles','dre-c-salgados','dre-c-insumos','dre-c-embal',
             'dre-c-recarga','dre-c-bichos','dre-c-buffet']
_CF_IDS   = ['dre-cf-energia','dre-cf-tel','dre-cf-agua','dre-cf-iptu','dre-cf-sal',
             'dre-cf-enc','dre-cf-imp','dre-cf-seg','dre-cf-diar']
_CV_IDS   = ['dre-cv-sist','dre-cv-terc','dre-cv-exped','dre-cv-honor','dre-cv-manut',
             'dre-cv-viag','dre-cv-taxas','dre-cv-unif','dre-cv-limp','dre-cv-alug',
             'dre-cv-caixa','dre-cv-mora','dre-cv-banco','dre-cv-cart','dre-cv-brindes',
             'dre-cv-utens','dre-cv-veic','dre-cv-segpred','dre-cv-gerais','dre-cv-gas',
             'dre-cv-estoque','dre-cv-comiss']

@app.callback(
    Output('res-lucro-bruto','children'),
    Output('res-operacional', 'children'),
    Output('res-liquido',     'children'),
    [Input(i,'value') for i in _REC_IDS + _COMP_IDS + _CF_IDS + _CV_IDS],
    prevent_initial_call=False,
)
def calc_resultados(*vals):
    nr = len(_REC_IDS); nc = len(_COMP_IDS); nf = len(_CF_IDS)
    receita     = sum(float(v) for v in vals[:nr]       if v is not None)
    compras     = sum(float(v) for v in vals[nr:nr+nc]  if v is not None)
    cf          = sum(float(v) for v in vals[nr+nc:nr+nc+nf] if v is not None)
    cv          = sum(float(v) for v in vals[nr+nc+nf:] if v is not None)
    lucro_bruto = (receita - compras) - cf
    operacional = lucro_bruto - cv
    liquido     = operacional
    def fmt(v):
        if receita == 0 and compras == 0 and cf == 0 and cv == 0: return '—'
        return f"R$ {v:,.2f}".replace(',','X').replace('.', ',').replace('X','.')
    return fmt(lucro_bruto), fmt(operacional), fmt(liquido)


# UPLOAD CSV
@app.callback(
    Output('csv-store','data'),
    Input('upload-data','contents'),
    State('upload-data','filename'),
    prevent_initial_call=True,
)
def parse_upload(contents, filename):
    if not contents:
        raise dash.exceptions.PreventUpdate
    _, content_string = contents.split(',')
    decoded = base64.b64decode(content_string).decode('utf-8')
    rows = [line.split(',') for line in decoded.strip().split('\n')]
    return {'filename': filename, 'rows': rows}

# ── FUNÇÕES DE GRÁFICOS ────────────────────────────────────────────────────────
def make_fig_main():
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Receita', x=MESES, y=RECEITA, marker_color='rgba(61,220,132,0.7)', marker_line_width=0))
    fig.add_trace(go.Bar(name='Despesa', x=MESES, y=DESPESA, marker_color='rgba(255,92,92,0.6)',  marker_line_width=0))
    fig.add_trace(go.Scatter(name='Lucro', x=MESES, y=LUCRO, mode='lines+markers',
                             line=dict(color='#e8c97a',width=2.5), marker=dict(size=6,color='#e8c97a')))
    fig.update_layout(**CHART_LAYOUT, barmode='group')
    return fig

def make_fig_bar():
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Receita', x=MESES, y=RECEITA, marker_color='rgba(61,220,132,0.75)', marker_line_width=0))
    fig.add_trace(go.Bar(name='Despesa', x=MESES, y=DESPESA, marker_color='rgba(255,92,92,0.65)',  marker_line_width=0))
    fig.update_layout(**CHART_LAYOUT, barmode='group')
    return fig

def make_fig_pie():
    labels = ['Pessoal','Administrativo','Marketing','Infraestrutura','Outros']
    values = [42, 15, 8, 9, 4]
    colors = ['#3ddc84','#c9a84c','#5c9eff','#e8ede9','#4d5e52']
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color='#0d0f0e',width=2)),
        textfont=dict(family='Space Mono', size=10, color='#0d0f0e')))
    fig.update_layout(**CHART_LAYOUT)
    return fig

def make_fig_margin():
    margens = [l/r*100 for l,r in zip(LUCRO,RECEITA)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=MESES, y=margens, mode='lines+markers',
        fill='tozeroy', fillcolor='rgba(61,220,132,0.07)',
        line=dict(color='#3ddc84',width=2.5), marker=dict(size=6,color='#3ddc84'), name='Margem %'))
    fig.add_hline(y=30, line_dash='dot', line_color='rgba(201,168,76,0.5)',
        annotation_text='Meta 30%', annotation_font=dict(color='#c9a84c',size=9))
    fig.update_layout(**CHART_LAYOUT)
    return fig

def make_fig_acum():
    acum, s = [], 0
    for l in LUCRO:
        s += l; acum.append(s)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=MESES, y=acum, mode='lines+markers',
        fill='tozeroy', fillcolor='rgba(201,168,76,0.07)',
        line=dict(color='#c9a84c',width=2.5), marker=dict(size=6,color='#c9a84c'), name='Lucro Acumulado'))
    fig.update_layout(**CHART_LAYOUT)
    return fig

# CONTEÚDO PRINCIPAL
@app.callback(
    Output('main-content','children'),
    Input('active-tab','data'),
    Input('csv-store','data'),
)
def render_content(tab, csv_data):

    upload_bar = dcc.Upload(
        id='upload-data',
        children=html.Div([
            html.Span("⬆", className='upload-icon'),
            html.Span(["Arraste ou clique para importar o ",
                       html.Strong("DRE (.csv)"),
                       " — dados atualizados automaticamente"], className='upload-text'),
        ]),
        className='upload-area',
    )

    # ── INDICADORES ────────────────────────────────────────────────────────────
    if tab in ('tab-ind', None):
        total_rec = sum(RECEITA)
        total_des = sum(DESPESA)
        total_luc = sum(LUCRO)
        margem    = total_luc / total_rec * 100
        return html.Div([
            upload_bar,
            html.Div(className='section-header', children=[
                html.Div([
                    html.Div("Resultados Consolidados", className='section-eyebrow'),
                    html.Div("Indicadores 2025", className='section-title'),
                ]),
                html.Div(style={'display':'flex','gap':'10px','alignItems':'flex-end'}, children=[
                    html.Div("Jan — Dez 2025", className='section-period'),
                ]),
            ]),
            html.Div(className='kpi-grid', children=[
                kpi_card("Receita Total",  f"R$ {total_rec/1e6:.2f}M", "Acumulado 2025",  "+14% a.a.", "up"),
                kpi_card("Despesas Totais",f"R$ {total_des/1e6:.2f}M", "Acumulado 2025",  "+9% a.a.",  "wait"),
                kpi_card("Lucro Líquido",  f"R$ {total_luc/1000:.0f}K","Resultado final", "+21% a.a.", "up", "green"),
                kpi_card("Margem Líquida", f"{margem:.1f}%",           "Meta: 30%  ✓",    "Excelente", "up", "gold"),
            ]),
            html.Div(className='kpi-grid', children=[
                kpi_card("Melhor Mês",    "Dez/25 · R$ 99K", "Lucro individual", "Recorde",     "up", "green"),
                kpi_card("Ticket Médio",  "R$ 37.400",       "Por transação",    "+6% m.a.",    "up"),
                kpi_card("EBITDA Médio",  "R$ 60K/mês",      "Geração de caixa", "Margem 26%",  "up", "gold"),
                kpi_card("Inadimplência", "2,3%",            "Sobre receita",    "Meta: <5%  ✓","up"),
            ]),
            html.Div(className='divider'),
            html.Div(className='section-header', children=[
                html.Div([
                    html.Div("Performance Mensal", className='section-eyebrow'),
                    html.Div("Evolução por Período", className='section-title'),
                ]),
            ]),
            html.Div(style={'display':'grid','gridTemplateColumns':'2fr 1fr','gap':'20px'}, children=[
                chart_card("Evolução Anual", "Receita vs Despesa vs Lucro", make_fig_main(), 280),
                html.Div(style={
                    'background':'#131714','border':'1px solid rgba(255,255,255,0.07)',
                    'borderRadius':'10px','padding':'22px',
                }, children=[
                    html.Div("Destaques", style={'fontFamily':"'Space Mono',monospace",'fontSize':'9px','color':'#3ddc84','textTransform':'uppercase','letterSpacing':'3px','marginBottom':'4px'}),
                    html.Div("Resumo Executivo", style={'fontFamily':"'Playfair Display',serif",'fontSize':'15px','fontWeight':'700','color':'#e8ede9','marginBottom':'16px','paddingBottom':'12px','borderBottom':'1px solid rgba(255,255,255,0.06)'}),
                    stat_row("Receita Dez/25", "R$ 267K", "+20% m/m"),
                    stat_row("Despesa Dez/25", "R$ 168K", "+21% m/m", up=False),
                    stat_row("Lucro Dez/25",   "R$ 99K",  "+18% m/m"),
                    stat_row("Margem Dez/25",  "37,1%",   "+0.5pp"),
                    stat_row("Crescimento AA", "+14,2%",  "+2.1pp"),
                ]),
            ]),
        ])

    # ── GRÁFICOS ───────────────────────────────────────────────────────────────
    elif tab == 'tab-charts':
        return html.Div([
            upload_bar,
            html.Div(className='section-header', children=[
                html.Div([
                    html.Div("Visualização de Dados", className='section-eyebrow'),
                    html.Div("Análise Gráfica 2025", className='section-title'),
                ]),
            ]),
            html.Div(className='charts-grid-2', children=[
                chart_card("Receita & Resultado", "Evolução Mensal Completa", make_fig_bar(), 300),
                chart_card("Composição de Despesas", "Por Categoria", make_fig_pie(), 300),
            ]),
            html.Div(className='charts-grid-2', children=[
                chart_card("Tendência de Margem", "Margem Líquida % por Mês", make_fig_margin(), 260),
                chart_card("Lucro Acumulado", "Acumulado do Exercício 2025", make_fig_acum(), 260),
            ]),
        ])

    # ── DRE ────────────────────────────────────────────────────────────────────
    elif tab == 'tab-dre':

        # helpers
        def campo(field_id, placeholder='0,00', width='140px'):
            return dcc.Input(
                id=field_id, type='number', placeholder=placeholder,
                debounce=True,
                style={
                    'width': width, 'padding': '7px 10px',
                    'background': '#0d0f0e', 'border': '1px solid rgba(255,255,255,0.1)',
                    'borderRadius': '6px', 'color': '#e8ede9',
                    'fontFamily': "'Space Mono',monospace", 'fontSize': '12px',
                    'textAlign': 'right', 'outline': 'none',
                }
            )

        def row_titulo(num, label, color='#3ddc84', bg='rgba(61,220,132,0.07)', size='14px'):
            return html.Tr(style={'background': bg, 'borderBottom': '1px solid rgba(255,255,255,0.08)'}, children=[
                html.Td(f'{num}. {label}', colSpan=2, style={
                    'padding': '13px 20px', 'fontWeight': '700',
                    'fontSize': size, 'color': color,
                    'fontFamily': "'Sora',sans-serif", 'letterSpacing': '0.3px',
                }),
            ])

        def row_sub(num, label, field_id):
            return html.Tr(style={'borderBottom': '1px solid rgba(255,255,255,0.04)'}, children=[
                html.Td(f'  {num}  {label}', style={
                    'padding': '10px 20px', 'fontSize': '13px',
                    'color': '#8fa894', 'fontFamily': "'Sora',sans-serif",
                }),
                html.Td(campo(field_id), style={'padding': '6px 20px 6px 0', 'textAlign': 'right'}),
            ])

        def row_resultado(label, result_id, color='#e8c97a', bg='rgba(201,168,76,0.06)'):
            return html.Tr(style={'background': bg, 'borderTop': '2px solid rgba(255,255,255,0.1)', 'borderBottom': '1px solid rgba(255,255,255,0.08)'}, children=[
                html.Td(label, style={
                    'padding': '13px 20px', 'fontWeight': '700',
                    'fontSize': '14px', 'color': color,
                    'fontFamily': "'Sora',sans-serif",
                }),
                html.Td(id=result_id, children='—', style={
                    'padding': '13px 20px', 'textAlign': 'right',
                    'fontWeight': '700', 'fontSize': '14px', 'color': color,
                    'fontFamily': "'Space Mono',monospace",
                }),
            ])

        return html.Div([
            upload_bar,
            html.Div(className='section-header', children=[
                html.Div([
                    html.Div("Demonstração do Resultado", className='section-eyebrow'),
                    html.Div("DRE — Lançamento de Dados", className='section-title'),
                ]),
                html.Div("Preencha os valores e os resultados serão calculados automaticamente",
                         style={'fontSize':'12px','color':'#4d5e52','fontFamily':"'Space Mono',monospace"}),
            ]),

            html.Div(className='dre-card', children=[
                html.Div(className='dre-card-header', children=[
                    html.Div(["DRE · ", html.Span("Entrada de Dados")], className='dre-card-title'),
                    html.Div("Valores em R$", className='dre-pill'),
                ]),

                html.Table(style={'width':'100%','borderCollapse':'collapse'}, children=[html.Tbody([

                    # ── 1. RECEITA TOTAL ──────────────────────────────────────
                    row_titulo('1', 'RECEITA TOTAL', color='#3ddc84', bg='rgba(61,220,132,0.1)'),

                    # ── 2. VENDAS DE MERCADORIAS ──────────────────────────────
                    row_titulo('2', 'RECEITA — VENDAS DE MERCADORIAS', bg='rgba(61,220,132,0.05)'),
                    row_sub('2.1', 'Vendas à Vista',  'dre-venda-vista'),
                    row_sub('2.2', 'Vendas a Prazo',  'dre-venda-prazo'),

                    # ── 3. VENDAS POR GRUPOS ──────────────────────────────────
                    row_titulo('3', 'VENDAS POR GRUPOS', bg='rgba(255,255,255,0.02)'),
                    row_sub('3.1',  'Bolos e Tortas',                'dre-g-bolos'),
                    row_sub('3.2',  'Buffet',                        'dre-g-buffet'),
                    row_sub('3.3',  'Cafés e Sucos',                 'dre-g-cafes'),
                    row_sub('3.4',  'Lanches',                       'dre-g-lanches'),
                    row_sub('3.5',  'Porções',                       'dre-g-porcoes'),
                    row_sub('3.6',  'Salgados Prontos',              'dre-g-salgados'),
                    row_sub('3.7',  'Drinks',                        'dre-g-drinks'),
                    row_sub('3.8',  'Conveniência',                  'dre-g-conv'),
                    row_sub('3.9',  'Cigarros',                      'dre-g-cigarros'),
                    row_sub('3.10', 'Bebidas',                       'dre-g-bebidas'),
                    row_sub('3.11', 'Picolé',                        'dre-g-picole'),
                    row_sub('3.12', 'Estoque Cozinha',               'dre-g-estcoz'),
                    row_sub('3.13', 'Bichos de Pelúcia e Brinquedos','dre-g-bichos'),
                    row_sub('3.14', 'Carnes',                        'dre-g-carnes'),

                    # ── 4. OUTRAS RECEITAS ────────────────────────────────────
                    row_titulo('4', 'OUTRAS RECEITAS OPERACIONAIS', bg='rgba(255,255,255,0.02)'),
                    row_sub('4.1', 'Juros Recebidos',                'dre-or-juros'),
                    row_sub('4.2', 'Aluguéis',                       'dre-or-alug'),
                    row_sub('4.4', 'Outras Receitas',                'dre-or-outras'),
                    row_sub('4.5', 'Rendimentos Fundos de Investimentos', 'dre-or-fundos'),
                    row_sub('4.6', 'Bonificações Recebidas',         'dre-or-bonif'),

                    # ── RESULTADO: RECEITA TOTAL ──────────────────────────────
                    row_resultado('1. RECEITA TOTAL', 'res-receita-total'),

                    # ── 5. COMPRAS DE MERCADORIAS ─────────────────────────────
                    row_titulo('5', 'TOTAL COMPRA DE MERCADORIAS', color='#ff5c5c', bg='rgba(255,92,92,0.05)'),
                    row_sub('5.1',  'Bebidas',                       'dre-c-bebidas'),
                    row_sub('5.2',  'Bolos e Tortas',                'dre-c-bolos'),
                    row_sub('5.3',  'Carnes',                        'dre-c-carnes'),
                    row_sub('5.4',  'Cigarros',                      'dre-c-cigarros'),
                    row_sub('5.5',  'Conveniência',                  'dre-c-conv'),
                    row_sub('5.6',  'Estoque Cozinha',               'dre-c-estcoz'),
                    row_sub('5.7',  'Picolés',                       'dre-c-picoles'),
                    row_sub('5.8',  'Salgados Prontos',              'dre-c-salgados'),
                    row_sub('5.9',  'Insumos',                       'dre-c-insumos'),
                    row_sub('5.10', 'Embalagens',                    'dre-c-embal'),
                    row_sub('5.11', 'Recarga Celular',               'dre-c-recarga'),
                    row_sub('5.12', 'Bichos de Pelúcia e Brinquedos','dre-c-bichos'),
                    row_sub('5.13', 'Buffet',                        'dre-c-buffet'),

                    # ── RESULTADO: MARGEM DE CONTRIBUIÇÃO ────────────────────
                    row_resultado('5. MARGEM DE CONTRIBUIÇÃO', 'res-margem', color='#3ddc84', bg='rgba(61,220,132,0.08)'),

                    # ── 6.1 CUSTOS FIXOS ──────────────────────────────────────
                    row_titulo('6', 'TOTAL CUSTOS FIXOS + VARIÁVEIS', color='#ff5c5c', bg='rgba(255,92,92,0.05)'),
                    row_titulo('6.1', 'Custos Fixos', color='#ff8080', bg='rgba(255,92,92,0.03)', size='13px'),
                    row_sub('6.1.1', 'Energia Elétrica',             'dre-cf-energia'),
                    row_sub('6.1.2', 'Telefone',                     'dre-cf-tel'),
                    row_sub('6.1.3', 'Água',                         'dre-cf-agua'),
                    row_sub('6.1.4', 'IPTU',                         'dre-cf-iptu'),
                    row_sub('6.1.5', 'Salários / Férias / Rescisões / 13º', 'dre-cf-sal'),
                    row_sub('6.1.6', 'Encargos Sociais',             'dre-cf-enc'),
                    row_sub('6.1.7', 'Impostos',                     'dre-cf-imp'),
                    row_sub('6.1.8', 'Seguro de Vida — Funcionários','dre-cf-seg'),
                    row_sub('6.1.9', 'Diárias',                      'dre-cf-diar'),

                    # ── 6.2 CUSTOS VARIÁVEIS ──────────────────────────────────
                    row_titulo('6.2', 'Custos Variáveis', color='#ff8080', bg='rgba(255,92,92,0.03)', size='13px'),
                    row_sub('6.2.1',  'Despesas com Sistemas',        'dre-cv-sist'),
                    row_sub('6.2.2',  'Serviços de Terceiros',        'dre-cv-terc'),
                    row_sub('6.2.3',  'Materiais de Expediente',      'dre-cv-exped'),
                    row_sub('6.2.4',  'Honorários Contábeis',         'dre-cv-honor'),
                    row_sub('6.2.5',  'Manutenção e Reposição',       'dre-cv-manut'),
                    row_sub('6.2.6',  'Viagens e Estadias',           'dre-cv-viag'),
                    row_sub('6.2.7',  'Taxas Diversas',               'dre-cv-taxas'),
                    row_sub('6.2.8',  'Uniformes',                    'dre-cv-unif'),
                    row_sub('6.2.9',  'Material de Limpeza',          'dre-cv-limp'),
                    row_sub('6.2.10', 'Aluguéis e Locações',          'dre-cv-alug'),
                    row_sub('6.2.11', 'Faltas e Sobras de Caixa',     'dre-cv-caixa'),
                    row_sub('6.2.12', 'Juros de Mora',                'dre-cv-mora'),
                    row_sub('6.2.13', 'Tarifas Bancárias',            'dre-cv-banco'),
                    row_sub('6.2.14', 'Tarifas Cartões',              'dre-cv-cart'),
                    row_sub('6.2.15', 'Brindes e Bonificações',       'dre-cv-brindes'),
                    row_sub('6.2.16', 'Utensílios',                   'dre-cv-utens'),
                    row_sub('6.2.17', 'Despesas com Veículos',        'dre-cv-veic'),
                    row_sub('6.2.18', 'Seguros Edificações',          'dre-cv-segpred'),
                    row_sub('6.2.19', 'Despesas Gerais',              'dre-cv-gerais'),
                    row_sub('6.2.20', 'Gás GLP',                      'dre-cv-gas'),
                    row_sub('6.2.21', 'Contagem Estoque',             'dre-cv-estoque'),
                    row_sub('6.2.22', 'Comissões sobre Vendas',       'dre-cv-comiss'),

                    # ── RESULTADOS FINAIS ─────────────────────────────────────
                    row_resultado('7. LUCRO BRUTO DA EMPRESA',        'res-lucro-bruto',   color='#3ddc84', bg='rgba(61,220,132,0.08)'),
                    row_resultado('8. RESULTADO OPERACIONAL',         'res-operacional',   color='#3ddc84', bg='rgba(61,220,132,0.06)'),
                    row_resultado('9. RESULTADO LÍQUIDO',             'res-liquido',       color='#3ddc84', bg='rgba(61,220,132,0.12)'),

                    # ── 10-12 FUNCIONÁRIOS / HORAS EXTRAS ────────────────────
                    row_titulo('10', 'FUNCIONÁRIOS & HORAS EXTRAS', color='#5c9eff', bg='rgba(92,158,255,0.06)'),

                    # 10. Total funcionários
                    html.Tr(style={'borderBottom':'1px solid rgba(255,255,255,0.04)'}, children=[
                        html.Td('  10.  Total de Funcionários', style={
                            'padding':'10px 20px','fontSize':'13px',
                            'color':'#8fa894','fontFamily':"'Sora',sans-serif",
                        }),
                        html.Td(campo('dre-func-total', placeholder='Nº funcionários', width='160px'),
                                style={'padding':'6px 20px 6px 0','textAlign':'right'}),
                    ]),

                    # 11 + 12. Horas extras com cálculo automático
                    html.Tr(style={'borderBottom':'1px solid rgba(255,255,255,0.04)', 'background':'rgba(92,158,255,0.03)'}, children=[
                        html.Td([
                            html.Div('  11.  Total de Horas Extras', style={
                                'fontSize':'13px','color':'#8fa894',
                                'fontFamily':"'Sora',sans-serif",'marginBottom':'4px',
                            }),
                            html.Div(style={'display':'flex','alignItems':'center','gap':'8px','paddingLeft':'8px','paddingBottom':'4px'}, children=[
                                html.Span('Horas:', style={'fontSize':'11px','color':'#4d5e52','fontFamily':"'Space Mono',monospace"}),
                                dcc.Input(id='dre-he-qtd', type='number', placeholder='Qtd. horas', debounce=True,
                                    style={'width':'110px','padding':'6px 10px','background':'#0d0f0e',
                                           'border':'1px solid rgba(92,158,255,0.3)','borderRadius':'6px',
                                           'color':'#5c9eff','fontFamily':"'Space Mono',monospace",'fontSize':'12px',
                                           'outline':'none','textAlign':'right'}),
                                html.Span('×  Valor/hora: R$', style={'fontSize':'11px','color':'#4d5e52','fontFamily':"'Space Mono',monospace"}),
                                dcc.Input(id='dre-he-valor', type='number', placeholder='0,00', debounce=True,
                                    style={'width':'110px','padding':'6px 10px','background':'#0d0f0e',
                                           'border':'1px solid rgba(92,158,255,0.3)','borderRadius':'6px',
                                           'color':'#5c9eff','fontFamily':"'Space Mono',monospace",'fontSize':'12px',
                                           'outline':'none','textAlign':'right'}),
                                html.Span('=', style={'fontSize':'13px','color':'#4d5e52'}),
                                html.Span(id='dre-he-result', children='R$ —', style={
                                    'fontSize':'13px','fontWeight':'700','color':'#5c9eff',
                                    'fontFamily':"'Space Mono',monospace",
                                    'background':'rgba(92,158,255,0.1)','padding':'4px 12px',
                                    'borderRadius':'6px','minWidth':'120px','textAlign':'right',
                                }),
                            ]),
                        ], style={'padding':'10px 20px'}),
                        html.Td('', style={'width':'160px'}),
                    ]),

                    # 12. Valor total horas extras (calculado)
                    html.Tr(style={'background':'rgba(92,158,255,0.05)','borderBottom':'2px solid rgba(92,158,255,0.15)'}, children=[
                        html.Td('  12.  Valor Total de Horas Extras', style={
                            'padding':'12px 20px','fontSize':'13px','fontWeight':'600',
                            'color':'#5c9eff','fontFamily':"'Sora',sans-serif",
                        }),
                        html.Td(id='dre-he-total-display', children='R$ —', style={
                            'padding':'12px 20px','textAlign':'right',
                            'fontWeight':'700','fontSize':'14px','color':'#5c9eff',
                            'fontFamily':"'Space Mono',monospace",
                        }),
                    ]),

                ])]),
            ]),
        ])

    # ── TRANSAÇÕES ─────────────────────────────────────────────────────────────
    elif tab == 'tab-txn':
        status_color = {'Confirmado':'#3ddc84','Processado':'#c9a84c','Pendente':'#ff5c5c'}
        cat_color    = {'Receita':'#3ddc84','Despesa':'#ff5c5c'}
        rows = []
        for t in TRANSACOES_MOCK:
            sc = status_color.get(t['status'], '#8fa894')
            cc = cat_color.get(t['categoria'], '#8fa894')
            r_rgb = '61,220,132' if cc == '#3ddc84' else '255,92,92'
            s_rgb = {'Confirmado':'61,220,132','Processado':'201,168,76','Pendente':'255,92,92'}.get(t['status'],'100,100,100')
            rows.append(html.Tr(style={'borderBottom':'1px solid rgba(255,255,255,0.04)'}, children=[
                html.Td(t['id'],       style={'padding':'13px 20px','fontFamily':"'Space Mono',monospace",'fontSize':'10px','color':'#4d5e52'}),
                html.Td(t['data'],     style={'padding':'13px 16px','fontFamily':"'Space Mono',monospace",'fontSize':'11px','color':'#8fa894'}),
                html.Td(t['descricao'],style={'padding':'13px 16px','fontSize':'13px','color':'#e8ede9'}),
                html.Td(html.Span(t['categoria'], style={
                    'padding':'3px 10px','borderRadius':'4px','fontSize':'11px',
                    'fontWeight':'700','color':cc,'background':f'rgba({r_rgb},0.1)',
                }), style={'padding':'13px 16px'}),
                html.Td(t['valor'],    style={'padding':'13px 16px','fontFamily':"'Space Mono',monospace",'fontSize':'12px','color':'#e8ede9','fontWeight':'600','textAlign':'right'}),
                html.Td(t['variacao'],style={'padding':'13px 16px','fontFamily':"'Space Mono',monospace",'fontSize':'11px','color':'#c9a84c','textAlign':'center'}),
                html.Td(html.Span(t['status'], style={
                    'padding':'3px 10px','borderRadius':'4px','fontSize':'10px',
                    'fontWeight':'700','color':sc,'background':f'rgba({s_rgb},0.1)',
                    'fontFamily':"'Space Mono',monospace",'letterSpacing':'1px',
                }), style={'padding':'13px 20px'}),
            ]))
        return html.Div([
            upload_bar,
            html.Div(className='section-header', children=[
                html.Div([
                    html.Div("Histórico Financeiro", className='section-eyebrow'),
                    html.Div("Transações Recentes", className='section-title'),
                ]),
            ]),
            html.Div(className='table-card', children=[
                html.Div(className='table-header', children=[
                    html.Div("Lançamentos — Dezembro 2025", className='table-header-title'),
                    html.Div(f"{len(TRANSACOES_MOCK)} registros",
                             style={'fontFamily':"'Space Mono',monospace",'fontSize':'10px','color':'#4d5e52'}),
                ]),
                html.Table(style={'width':'100%','borderCollapse':'collapse'}, children=[
                    html.Thead(children=[html.Tr(
                        style={'background':'#1a1f1c','borderBottom':'2px solid rgba(255,255,255,0.06)'},
                        children=[html.Th(h, style={
                            'padding':'11px 20px' if i in (0,6) else '11px 16px',
                            'textAlign':'right' if i==4 else 'left',
                            'fontFamily':"'Space Mono',monospace",'fontSize':'9px',
                            'color':'#4d5e52','letterSpacing':'2px','textTransform':'uppercase',
                        }) for i,h in enumerate(["ID","Data","Descrição","Categoria","Valor","Var.","Status"])]
                    )]),
                    html.Tbody(rows),
                ]),
            ]),
        ])

    return html.Div("Selecione uma aba.", style={'color':'#8fa894','padding':'40px'})


# ── INICIALIZAÇÃO ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(host='0.0.0.0', port=port, debug=False)