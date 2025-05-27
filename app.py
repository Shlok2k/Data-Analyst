import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Output, Input, State
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import copy
import plotly.graph_objects as go
import numpy as np
from dash.dependencies import Input, Output, State
import requests


# Load the data
url = "https://raw.githubusercontent.com/rohit951994/GenZ-Career-Aspirations-dataset/refs/heads/main/Career%20Aspirations%20survey%20of%20GenZ.csv"
df = pd.read_csv(url)

# Color schemes
COLORS = {
    'primary': px.colors.qualitative.Set3,
    'secondary': px.colors.qualitative.Pastel,
    'accent': px.colors.qualitative.Bold
}

# Common layout settings
COMMON_LAYOUT = {
    'font': {'family': 'Arial, sans-serif', 'size': 12},
    'title': {'font': {'size': 16, 'color': '#2c3e50'}},
    'paper_bgcolor': 'white',
    'plot_bgcolor': 'white',
    'margin': {'t': 40, 'b': 40, 'l': 40, 'r': 40},
    'height': 400,  # Set a fixed height for all charts
    'width': 500    # Set a fixed width for all charts
}

# Create visualizations
# 1. Demographics
fig_country = px.pie(
    df,
    names='Your Current Country.',
    title="Distribution of Current Country",
    color_discrete_sequence=COLORS['primary']
)
fig_country.update_layout(**COMMON_LAYOUT)
fig_country.update_traces(textposition='inside', textinfo='percent+label')

gender_counts = df['Your Gender'].value_counts().reset_index()
gender_counts.columns = ['Gender', 'Count']
frames = [
    go.Frame(
        data=[go.Bar(
            x=gender_counts['Gender'],
            y=[y if i <= k else 0 for i, y in enumerate(gender_counts['Count'])],
            marker_color=['#1da1f2' if i == k else '#b2bec3' for i in range(len(gender_counts))]
        )]
    )
    for k in range(len(gender_counts))
]

fig_gender = go.Figure(
    data=[go.Bar(
        x=gender_counts['Gender'],
        y=[0]*len(gender_counts),
        marker_color='#b2bec3'
    )],
    layout=go.Layout(
        title="Gender Distribution",
        xaxis=dict(title='Gender'),
        yaxis=dict(title='Count'),
        updatemenus=[{
            "type": "buttons",
            "buttons": [{
                "label": "Play",
                "method": "animate",
                "args": [None, {"frame": {"duration": 400, "redraw": True}, "fromcurrent": True}]
            }]
        }]
    ),
    frames=frames
)

# 2. Career Influences
fig_influence = px.pie(
    df,
    names='Which of the below factors influence the most about your career aspirations ?',
    title="Key Factors Influencing Career Aspirations (Donut)",
    hole=0.4,
    color_discrete_sequence=COLORS['accent']
)
fig_influence.update_layout(**COMMON_LAYOUT)
fig_influence.update_traces(textposition='inside', textinfo='percent+label', pull=[0.1 if i == 0 else 0 for i in range(len(fig_influence.data[0]['labels']))])

education_counts = df['Would you definitely pursue a Higher Education / Post Graduation outside of India ? If only you have to self sponsor it.'].value_counts().reset_index()
education_counts.columns = ['Response', 'Count']
fig_education = px.bar(
    education_counts,
    y='Response',
    x='Count',
    orientation='h',
    title="Pursue Higher Education Abroad (Self Sponsored)?",
    color='Count',
    color_continuous_scale=px.colors.sequential.Viridis
)
fig_education.update_layout(**COMMON_LAYOUT)
fig_education.update_traces(texttemplate='%{x}', textposition='outside')

# 3. Employer Preferences
employer_duration = df['How likely is that you will work for one employer for 3 years or more ?'].value_counts().reset_index()
employer_duration.columns = ['Response', 'Count']
# Map responses to shorter labels if needed
short_response_map = {
    "No way, 3 years with one employer is crazy": "No way",
    "I will work for 3 years or more": "Yes, 3+ years",
    "This will be hard to do, but if it is the right company I will": "If right company"
}
employer_duration['ShortResponse'] = employer_duration['Response'].map(lambda x: short_response_map.get(x, x))
fig_employer_duration = px.bar(
    employer_duration,
    x='ShortResponse',
    y='Count',
    title="Likelihood to Work for One Employer (3+ Years)",
    color='ShortResponse',
    color_discrete_sequence=px.colors.qualitative.Pastel2,
    labels={'ShortResponse': 'Response', 'Count': 'Number of People'}
)
fig_employer_duration.update_layout(**COMMON_LAYOUT)
fig_employer_duration.update_traces(texttemplate='%{y}', textposition='outside')
fig_employer_duration.update_xaxes(title_text='Response')
fig_employer_duration.update_yaxes(title_text='Number of People')

mission_counts = df['Would you work for a company whose mission is not clearly defined and publicly posted.'].value_counts().reset_index()
mission_counts.columns = ['Mission', 'Count']
# For the pie chart, map long values to short labels
short_mission_map = {
    'Yes': 'Yes',
    'No': 'No',
    'Maybe': 'Maybe',
    'Not Sure': 'Not Sure',
}
mission_counts['ShortMission'] = mission_counts['Mission'].map(lambda x: short_mission_map.get(x, x))
fig_mission = px.pie(
    mission_counts,
    names='ShortMission',
    values='Count',
    title="Work for Company with Undefined Mission (Pie)",
    color_discrete_sequence=px.colors.qualitative.Pastel1,
    labels={'ShortMission': 'Response', 'Count': 'Number of People'}
)
fig_mission.update_layout(**COMMON_LAYOUT)
fig_mission.update_traces(textposition='inside', textinfo='percent+label')

# 4. Work Environment
learning_counts = df['Which type of learning environment that you are most likely to work in ?'].value_counts().reset_index()
learning_counts.columns = ['Environment', 'Count']
learning_table = dash_table.DataTable(
    columns=[{"name": i, "id": i} for i in learning_counts.columns],
    data=learning_counts.to_dict('records'),
    style_table={'height': '400px', 'overflowY': 'auto', 'width': '100%'},
    style_cell={'fontFamily': 'Arial', 'fontSize': 12, 'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
)

employer_counts = df['Which of the below Employers would you work with.'].value_counts().reset_index()
employer_counts.columns = ['Employer', 'Count']
df['EmployerFull'] = df['Which of the below Employers would you work with.'].astype(str)

# Prepare data for animation
employer_counts_sorted = employer_counts.sort_values('Count', ascending=True)
frames = [
    go.Frame(
        data=[go.Bar(
            x=employer_counts_sorted['Count'][:k+1],
            y=employer_counts_sorted['Employer'][:k+1],
            orientation='h',
            marker_color=px.colors.sequential.Plasma,
            customdata=employer_counts_sorted['Employer'][:k+1]
        )]
    )
    for k in range(len(employer_counts_sorted))
]

fig_employers = go.Figure(
    data=[go.Bar(
        x=[0]*len(employer_counts_sorted),
        y=employer_counts_sorted['Employer'],
        orientation='h',
        marker_color=px.colors.sequential.Plasma,
        customdata=employer_counts_sorted['Employer']
    )],
    layout=go.Layout(
        title="Preferred Employers (Horizontal Bar)",
        xaxis=dict(title='Count'),
        yaxis=dict(title='Employer', automargin=True, tickfont=dict(size=11)),
        height=420,
        width=600,
        margin=dict(t=40, b=40, l=120, r=40),
        updatemenus=[{
            "type": "buttons",
            "buttons": [{
                "label": "Play",
                "method": "animate",
                "args": [None, {"frame": {"duration": 300, "redraw": True}, "fromcurrent": True}]
            }]
        }]
    ),
    frames=frames
)
fig_employers.update_traces(
    texttemplate='%{x}',
    textposition='outside',
    hovertemplate='<b>%{customdata}</b><br>Count: %{x}<extra></extra>'
)

# 5. Career Aspirations
# Add a new column for full text
df['AspirationalJob'] = df['Which of the below careers looks close to your Aspirational job ?'].astype(str)
df['AspirationalJob'] = df['AspirationalJob'].apply(lambda x: '<br>'.join([x[i:i+40] for i in range(0, len(x), 40)]))

fig_career = px.treemap(
    df,
    path=['AspirationalJob'],
    title="Aspirational Career (Treemap)",
    color_discrete_sequence=px.colors.qualitative.Set2,
    custom_data=['AspirationalJob']
)
fig_career.update_layout(**COMMON_LAYOUT)
fig_career.update_traces(
    hovertemplate='<b>%{customdata[0]}</b><br>Count: %{value}<extra></extra>',
    textinfo='none'
)

fig_manager = px.sunburst(
    df,
    path=['What type of Manager would you work without looking into your watch ?'],
    title="Preferred Manager Type (Sunburst)",
    color_discrete_sequence=px.colors.qualitative.Dark2
)
fig_manager.update_layout(**COMMON_LAYOUT)

# Create the Dash app
app = Dash(__name__)
server = app.server  # Add this line for Render deployment

app.layout = html.Div([
    html.H1("GenZ Career Aspirations Dashboard", 
            style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#2c3e50', 'fontFamily': 'Arial, sans-serif', 'fontSize': '24px'}),
    
    # Demographics Section
    html.H2("1. Demographics", style={'color': '#2c3e50', 'fontFamily': 'Arial, sans-serif', 'fontSize': '18px'}),
    html.Div([
        html.Div(dcc.Graph(figure=fig_country), 
                style={'width': '48%', 'display': 'inline-block', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'}),
        html.Div(dcc.Graph(figure=fig_gender), 
                style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'})
    ], style={'marginBottom': '20px'}),
    
    # Career Influences Section
    html.H2("2. Career Influences & Education", style={'color': '#2c3e50', 'fontFamily': 'Arial, sans-serif', 'fontSize': '18px'}),
    html.Div([
        html.Div(dcc.Graph(figure=fig_influence), 
                style={'width': '48%', 'display': 'inline-block', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'}),
        html.Div(dcc.Graph(figure=fig_education), 
                style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'})
    ], style={'marginBottom': '20px'}),
    
    # Employer Preferences Section
    html.H2("3. Employer Preferences", style={'color': '#2c3e50', 'fontFamily': 'Arial, sans-serif', 'fontSize': '18px'}),
    html.Div([
        html.Div([
            html.Div([
                dcc.Graph(figure=fig_employer_duration, id='employer-duration-chart'),
                html.Button("ℹ️", id="info-btn-employer", style={
                    "position": "absolute",
                    "top": "15px",
                    "right": "15px",
                    "width": "40px",
                    "height": "40px",
                    "borderRadius": "50%",
                    "backgroundColor": "#ffb300",
                    "color": "white",
                    "fontSize": "22px",
                    "boxShadow": "0 2px 4px 0 rgba(0,0,0,0.15)",
                    "border": "none",
                    "zIndex": 10,
                    "padding": "0"
                }),
                html.Div(
                    id="info-box-employer",
                    children="This chart shows how likely GenZ is to stay with one employer for 3+ years. Most prefer flexibility, but some value stability if the company is right.",
                    style={
                        "display": "none",
                        "position": "absolute",
                        "top": "60px",
                        "right": "15px",
                        "backgroundColor": "white",
                        "padding": "12px",
                        "borderRadius": "8px",
                        "boxShadow": "0 2px 8px 0 rgba(0,0,0,0.15)",
                        "width": "260px",
                        "fontSize": "13px",
                        "color": "#333",
                        "zIndex": 20
                    }
                )
            ], style={"position": "relative", "width": "100%"})
        ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'}),
        html.Div(dcc.Graph(figure=fig_mission),
                style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'})
    ], style={'marginBottom': '20px', 'display': 'flex', 'flexWrap': 'wrap'}),
    
    # Work Environment Section
    html.H2("4. Work Environment", style={'color': '#2c3e50', 'fontFamily': 'Arial, sans-serif', 'fontSize': '18px'}),
    html.Div([
        html.Div(learning_table, 
                style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)', 'backgroundColor': 'white', 'padding': '10px'}),
        html.Div(dcc.Graph(figure=fig_employers), 
                style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'})
    ], style={'marginBottom': '20px'}),
    
    # Career Aspirations Section
    html.H2("5. Career Aspirations", style={'color': '#2c3e50', 'fontFamily': 'Arial, sans-serif', 'fontSize': '18px'}),
    html.Div([
        html.Div(dcc.Graph(figure=fig_career), 
                style={'width': '48%', 'display': 'inline-block', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'}),
        html.Div(dcc.Graph(figure=fig_manager), 
                style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%', 'boxShadow': '0 4px 8px 0 rgba(0,0,0,0.1)'})
    ], style={'marginBottom': '20px'}),
    html.Button(
        children=html.Span("⟨⟩"),  # or use an icon image
        id="toggle-table-btn",
        style={
            "position": "fixed",
            "bottom": "40px",
            "right": "40px",
            "width": "60px",
            "height": "60px",
            "borderRadius": "50%",
            "backgroundColor": "#1da1f2",
            "color": "white",
            "fontSize": "32px",
            "boxShadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
            "border": "none",
            "zIndex": 1000,
        }
    ),
    html.Div(id="table-container", style={"display": "none"}),
    html.Button(
        children=html.Span("ℹ️"),
        id="toggle-explanation-btn",
        style={
            "position": "fixed",
            "bottom": "120px",
            "right": "40px",
            "width": "60px",
            "height": "60px",
            "borderRadius": "50%",
            "backgroundColor": "#ffb300",
            "color": "white",
            "fontSize": "32px",
            "boxShadow": "0 4px 8px 0 rgba(0,0,0,0.2)",
            "border": "none",
            "zIndex": 1000,
        }
    ),
    html.Div(
        id="explanation-container",
        children="This chart shows how likely GenZ is to stay with one employer for 3+ years. Most prefer flexibility, but some value stability if the company is right.",
        style={"display": "none", "position": "fixed", "bottom": "190px", "right": "40px", "backgroundColor": "white", "padding": "15px", "borderRadius": "8px", "boxShadow": "0 4px 8px 0 rgba(0,0,0,0.2)", "width": "300px"}
    ),
    html.Button(
        children=html.Span("ℹ️"),
        id="info-btn-workenv",
        style={
            "position": "absolute",
            "top": "15px",
            "right": "15px",
            "width": "40px",
            "height": "40px",
            "borderRadius": "50%",
            "backgroundColor": "#ffb300",
            "color": "white",
            "fontSize": "22px",
            "boxShadow": "0 2px 4px 0 rgba(0,0,0,0.15)",
            "border": "none",
            "zIndex": 10,
            "padding": "0"
        }
    ),
    html.Div(
        id="info-box-workenv",
        children="This section shows the preferred work environments and employer types for GenZ. The data reveals their preferences for learning environments and potential employers.",
        style={
            "display": "none",
            "position": "absolute",
            "top": "60px",
            "right": "15px",
            "backgroundColor": "white",
            "padding": "12px",
            "borderRadius": "8px",
            "boxShadow": "0 2px 8px 0 rgba(0,0,0,0.15)",
            "width": "260px",
            "fontSize": "13px",
            "color": "#333",
            "zIndex": 20
        }
    )
], style={'width': '90%', 'margin': 'auto', 'backgroundColor': '#f8f9fa', 'padding': '15px'})

def toggle_display(n, style):
    # If never clicked, or style is None, or display is not set, show the box
    if n is None or not style or style.get("display") != "block":
        return {"display": "block"}
    else:
        return {"display": "none"}

@app.callback(
    Output("table-container", "style"),
    Input("toggle-table-btn", "n_clicks"),
    State("table-container", "style"),
    prevent_initial_call=True
)
def toggle_table(n, style):
    print(f"Button clicked! n={n}, style={style}")
    return toggle_display(n, style)

@app.callback(
    Output("explanation-container", "style"),
    Input("toggle-explanation-btn", "n_clicks"),
    State("explanation-container", "style"),
    prevent_initial_call=True
)
def toggle_explanation(n, style):
    print(f"Button clicked! n={n}, style={style}")
    return toggle_display(n, style)

@app.callback(
    Output("info-box-employer", "style"),
    Input("info-btn-employer", "n_clicks"),
    State("info-box-employer", "style"),
    prevent_initial_call=True
)
def toggle_info(n, style):
    print(f"Button clicked! n={n}, style={style}")
    return toggle_display(n, style)

@app.callback(
    Output("info-box-workenv", "style"),
    Input("info-btn-workenv", "n_clicks"),
    State("info-box-workenv", "style"),
    prevent_initial_call=True
)
def toggle_info_workenv(n, style):
    print(f"Button clicked! n={n}, style={style}")
    return toggle_display(n, style)
# This is for Gunicorn
application = app.server

# This is for local development
if __name__ == "__main__":
    from waitress import serve
    print("Starting production server...")
    print("Server will be available at:")
    print("http://127.0.0.1:8050")
    print("http://192.168.29.243:8050")
    print("Press CTRL+C to stop the server")
    serve(application, host='0.0.0.0', port=8050, threads=4)
# finished

