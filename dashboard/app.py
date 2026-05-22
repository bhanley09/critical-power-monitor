import sqlite3
import os
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "telemetry.db")

app = dash.Dash(__name__)
app.title = "Critical Power Fleet HUD"


def query(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def latest_for_generator(generator_id):
    rows = query("""
        SELECT * FROM telemetry
        WHERE generator_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (generator_id,))
    return rows[0] if rows else None


def get_history(generator_id, limit=40):
    rows = query("""
        SELECT timestamp, battery_voltage, coolant_temp, oil_pressure, total_kw,
               l1_amps, l2_amps, l3_amps
        FROM telemetry
        WHERE generator_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (generator_id, limit))
    return list(reversed(rows))


def card(title, value, unit="", color="#00e5ff"):
    return html.Div(
        [
            html.Div(title, style={
                "fontSize": "12px",
                "color": "#8fdfff",
                "letterSpacing": "1px"
            }),
            html.Div(
                [
                    html.Span(str(value)),
                    html.Span(unit, style={"fontSize": "14px", "marginLeft": "4px"})
                ],
                style={
                    "fontSize": "22px",
                    "fontWeight": "bold",
                    "color": color,
                    "wordWrap": "break-word",
                    "whiteSpace": "normal"
                }
            )
        ],
        style={
            "background": "linear-gradient(145deg, #071521, #0b2638)",
            "border": f"1px solid {color}",
            "boxShadow": f"0 0 12px {color}55",
            "borderRadius": "14px",
            "padding": "14px",
            "textAlign": "center",
            "minHeight": "110px"
        }
    )


def section(title, children):
    return html.Div(
        [
            html.H2(title, style={"marginTop": "0", "color": "#dff8ff"}),
            children
        ],
        style={
            "backgroundColor": "#071521",
            "border": "1px solid #1e90ff",
            "borderRadius": "18px",
            "padding": "18px",
            "boxShadow": "0 0 18px #1e90ff44",
            "marginTop": "18px"
        }
    )


def gauge(title, value, min_v, max_v, suffix):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": suffix},
        title={"text": title},
        gauge={
            "axis": {"range": [min_v, max_v]},
            "bar": {"color": "#00e5ff"},
            "bgcolor": "#061018",
            "borderwidth": 1,
            "bordercolor": "#1e90ff",
        }
    ))

    fig.update_layout(
        paper_bgcolor="#061018",
        plot_bgcolor="#061018",
        font={"color": "#dff8ff"},
        height=240,
        margin=dict(l=10, r=10, t=45, b=10)
    )
    return fig


def mimic(row):
    (
        timestamp, gen_id, engine_running, engine_state, battery, coolant, oil_pressure,
        rpm, runtime_hours, frequency, total_kw, total_kva, pf,
        l1_amps, l2_amps, l3_amps,
        v_l1_l2, v_l2_l3, v_l3_l1,
        v_l1_n, v_l2_n, v_l3_n, alarm
    ) = row

    energized = engine_running and total_kw > 0
    line_color = "#00ff88" if energized else "#425563"
    gen_color = "#00ff88" if engine_running else "#8aa0ad"
    alarm_color = "#00ff88" if alarm == "None" else "#ff3355"

    return html.Div([
        html.Div(
            [
                card("ENGINE", engine_state, color=gen_color),
                card("OUTPUT", "ENERGIZED" if energized else "OFFLINE", color=line_color),
                card("LOAD", total_kw, "kW"),
                card("ALARM", alarm.upper(), color=alarm_color),
            ],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(150px, 1fr))",
                "gap": "12px"
            }
        )
    ])


app.layout = html.Div(
    style={
        "background": "radial-gradient(circle at top, #12324a 0%, #03070c 70%)",
        "minHeight": "100vh",
        "color": "#dff8ff",
        "fontFamily": "Arial",
        "padding": "12px"
    },
    children=[
        dcc.Interval(id="interval", interval=3000, n_intervals=0),

        html.Div([
            html.H1(
                "CRITICAL POWER FLEET HUD",
                style={
                    "textAlign": "center",
                    "letterSpacing": "3px",
                    "color": "#00e5ff",
                    "textShadow": "0 0 12px #00e5ff"
                }
            ),

            dcc.Dropdown(
                id="generator-select",
                options=[{"label": f"GEN-{i}", "value": f"GEN-{i}"} for i in range(1, 9)],
                value="GEN-1",
                clearable=False,
                style={
                    "color": "black",
                    "maxWidth": "300px",
                    "margin": "auto"
                }
            )
        ]),

        dcc.Tabs(
            id="tabs",
            value="overview",
            children=[
                dcc.Tab(label="OVERVIEW", value="overview"),
                dcc.Tab(label="ENGINE", value="engine"),
                dcc.Tab(label="GENERATOR", value="generator"),
                dcc.Tab(label="TRENDS", value="trends"),
            ],
            style={"marginTop": "18px"},
            colors={
                "border": "#1e90ff",
                "primary": "#00e5ff",
                "background": "#071521"
            }
        ),

        html.Div(id="page-content")
    ]
)


@app.callback(
    Output("page-content", "children"),
    Input("interval", "n_intervals"),
    Input("tabs", "value"),
    Input("generator-select", "value")
)
def update_dashboard(n, tab, generator_id):
    row = latest_for_generator(generator_id)

    if row is None:
        return html.Div("No telemetry data found.")

    (
        timestamp, gen_id, engine_running, engine_state, battery, coolant, oil_pressure,
        rpm, runtime_hours, frequency, total_kw, total_kva, pf,
        l1_amps, l2_amps, l3_amps,
        v_l1_l2, v_l2_l3, v_l3_l1,
        v_l1_n, v_l2_n, v_l3_n, alarm
    ) = row

    if tab == "overview":
        return html.Div([
            section("SYSTEM OVERVIEW", mimic(row)),
            section("PRIMARY GAUGES", html.Div([
                dcc.Graph(figure=gauge("Battery Voltage", battery, 10, 15, " V"), config={"displayModeBar": False}),
                dcc.Graph(figure=gauge("Coolant Temp", coolant, 80, 230, " °F"), config={"displayModeBar": False}),
                dcc.Graph(figure=gauge("Total kW", total_kw, 0, 500, " kW"), config={"displayModeBar": False}),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(260px, 1fr))",
                "gap": "14px"
            }))
        ])

    elif tab == "engine":
        return section("ENGINE READOUTS", html.Div([
            card("ENGINE STATE", engine_state),
            card("RPM", rpm),
            card("RUNTIME", runtime_hours, "hrs"),
            card("BATTERY", battery, "V"),
            card("COOLANT", coolant, "°F"),
            card("OIL PRESSURE", oil_pressure, "PSI"),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(170px, 1fr))",
            "gap": "12px"
        }))

    elif tab == "generator":
        return html.Div([
            section("GENERATOR OUTPUT", html.Div([
                card("FREQUENCY", frequency, "Hz"),
                card("TOTAL kW", total_kw, "kW"),
                card("TOTAL kVA", total_kva, "kVA"),
                card("POWER FACTOR", pf),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(170px, 1fr))",
                "gap": "12px"
            })),

            section("PHASE CURRENT", html.Div([
                card("L1 AMPS", l1_amps, "A"),
                card("L2 AMPS", l2_amps, "A"),
                card("L3 AMPS", l3_amps, "A"),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(170px, 1fr))",
                "gap": "12px"
            })),

            section("LINE-TO-LINE VOLTAGE", html.Div([
                card("L1-L2", v_l1_l2, "V"),
                card("L2-L3", v_l2_l3, "V"),
                card("L3-L1", v_l3_l1, "V"),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(170px, 1fr))",
                "gap": "12px"
            })),

            section("LINE-TO-NEUTRAL VOLTAGE", html.Div([
                card("L1-N", v_l1_n, "V"),
                card("L2-N", v_l2_n, "V"),
                card("L3-N", v_l3_n, "V"),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(170px, 1fr))",
                "gap": "12px"
            }))
        ])

    elif tab == "trends":
        history = get_history(generator_id)

        times = [r[0] for r in history]
        batteries = [r[1] for r in history]
        coolants = [r[2] for r in history]
        kws = [r[4] for r in history]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=batteries, mode="lines", name="Battery"))
        fig.add_trace(go.Scatter(x=times, y=coolants, mode="lines", name="Coolant"))
        fig.add_trace(go.Scatter(x=times, y=kws, mode="lines", name="kW"))

        fig.update_layout(
            title=f"{generator_id} Trend Tracking",
            paper_bgcolor="#061018",
            plot_bgcolor="#061018",
            font={"color": "#dff8ff"},
            height=500
        )

        return section("TREND TRACKING", dcc.Graph(
            figure=fig,
            config={"displayModeBar": False}
        ))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)