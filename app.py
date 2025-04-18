import dash
from dash import dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash import State
import os

url = "https://raw.githubusercontent.com/leonism/sample-superstore/master/data/superstore.csv"
df = pd.read_csv(url)

df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Month'] = df['Order Date'].dt.to_period('M').astype(str)

#first we initialise the app

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Inventory Management"

app.layout = html.Div([
    html.H1("Inventory Management Dashboard", style= {'textAlign': 'center'}),

    html.Div([
        html.Div([
            html.Label('Category'),
            dcc.Dropdown(df['Category'].unique(), id='category-filter', multi=True)
        ], style={'width': '30%', 'display': 'inline-block', "marginLeft": '2%'}),

    html.Div([
        html.Label('Region'),
        dcc.Dropdown(df['Region'].unique(), id='region-filter', multi=True)
    ], style={'width': '30%', 'display':'inline-block', 'margin': '2%'}),

    html.Div([
        html.Label('Sub-Category'),
        dcc.Dropdown(df['Sub-Category'].unique(), id='subcat-filter', multi=True)
    ], style= {'width': "30%", 'display': 'inline-block', 'marginLeft': '2%'})
    ], style= {'padding': '20px', 'margin': '20px'}),

    html.Hr(),

    html.Div([
        html.Div(id="kpi-cards", style={'padding': '10px'}),

        html.H3('Filtered Inventory Data', style= {'marginTop': '20px'}),
        dash_table.DataTable(
            id='inventory-table',
            page_size= 10,
            style_header= {
                'backgroundColor' : '#1f1f1f',
                'color' : 'white',
                'fontWeight' : 'bold',
                'border' : '1px solid #444'
            },
            style_data = {
                'backgroundColor' : '1e1e1e',
                'color' : 'black',
                'border' : '1px solid #444'
            },
            style_table= {'over-flowX': 'auto'},
            style_data_conditional= []
        )
    ]),

    html.Div([
        html.Label('Selected Metrics', style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='metric-toggle',
            options= [
                {'label': 'Sales', 'value': 'Sales'},
                {'label' : 'Quantity', 'value': 'Quantity'}
            ],
            value='Sales',
            clearable=False,
            style={
                'backgroundColor': '#1f1f1f',    # Background of the selected item
                'color': 'white',                # Selected text color
                'padding': '5px'},
            className= 'custom-dropdown'
        )
    ], style = {'marginBottom' : '10px', 'color' : 'white', 'fontWeight': 'bold', 'background': '1e1e1e'}),

    html.Div([
        html.Div([
            dcc.Graph(id='bar-chart',  className='dash-graph')
        ], style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='pie-chart',  className='dash-graph')
        ], style={'width': '49%', 'display': 'inline-block'})
    ]),

    html.Div([
        html.H3('Waterfall Chart - Sales Contribution',style={'fontWeight': 'bold', 'textAlign': 'center', 'marginTop': '20px', 'marginBottom': '0px'}),
        dcc.Graph(id='waterfall-chart',  className='dash-graph', style={'marginTop':'5px'})
    ], style= {'marginTop': '0px'}),

    html.Div([
        html.H3("Montly Sales Trend", style={'marginBottom': '20px', 'textAlign': 'center', 'fontWeight': 'bold'}),
        dcc.Graph(id='time-chart',  className='dash-graph')
    ], style={'marginTop': '30px'}),

    html.Div([
        html.Button('Download CSV', id='download-button'),
        dcc.Download(id = 'download-dataframe-csv')
    ], style={'marginTop': '30px'})
])

@app.callback(
    Output('inventory-table', 'data'),
    Output('inventory-table', 'columns'),
    Output('kpi-cards', 'children'),
    Output('bar-chart', 'figure'),
    Output('pie-chart', 'figure'),
    Output('inventory-table', 'style_data_conditional'),
    Output('waterfall-chart', 'figure'),
    Output('time-chart', 'figure'),
    Input('category-filter', 'value'),
    Input('region-filter', 'value'),
    Input('subcat-filter', 'value'),
    Input('metric-toggle', 'value')
)
def update_dashboard(selected_cat, selected_region, selected_subcat, selected_metrics):
    filter_df = df.copy()
    filter_df['Month'] = filter_df['Order Date'].dt.to_period('M').astype(str)

    if selected_cat:
        filter_df = filter_df[filter_df['Category'].isin(selected_cat)]
    if selected_region:
        filter_df = filter_df[filter_df['Region'].isin(selected_region)]
    if selected_subcat:
        filter_df = filter_df[filter_df['Sub-Category'].isin(selected_subcat)]

    total_sales = round(filter_df['Sales'].sum(), 2)
    total_quantity = round(filter_df['Quantity'].sum(), 2)
    avg_discount = round(filter_df['Discount'].mean()*100, 2) if not filter_df.empty else 0

    kpis = html.Div([
        html.Div([
            html.H4('Total Sales'),
            html.H2(f"${total_sales}")
        ], className= 'kpi-card', style= {'width': "30%", 'display': 'inline-block'}),

        html.Div([
            html.H4('Total Quantity'),
            html.H2(f'{total_quantity}')
        ], className= 'kpi-card', style = {'width': '30%', 'display': 'inline-block'}),

        html.Div([
            html.H4('Average Discount'),
            html.H2(f'{avg_discount}')
        ], className= 'kpi-card', style={'width': '30%', 'display': 'inline-block'})
    ])

    table_data = filter_df.to_dict('records')
    table_columns = [{'name': i, "id": i} for i in filter_df.columns]

    bar_df = filter_df.groupby('Sub-Category', as_index=False)[selected_metrics].sum().sort_values(by=selected_metrics, ascending=False)
    bar_chart = px.bar(
        bar_df,
        x = 'Sub-Category',
        y= selected_metrics,
        title = 'Sales by Sub-Category',
        text_auto = '.2s',
    )

    bar_chart.update_layout(
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='white'
    )

    pie_df = filter_df.groupby('Region', as_index=False)['Quantity'].sum()
    pie_chart = px.pie(
        pie_df,
        values = 'Quantity',
        names = 'Region',
        title= 'Quantity Distribution by Region',
        hole = 0.4,
        template= 'seaborn'
    )
    pie_chart.update_layout(template='plotly_dark', plot_bgcolor='#121212', paper_bgcolor='#121212', font_color='white')

    style_conditions = []

    if not filter_df.empty:
        style_conditions = [
            {
                'if': {
                    'filter_query' : '{Quantity} < 10',
                    'column_id' : 'Quantity'
                },
                'backgroundColor' : '#ffcccc',
                'color' : 'black'
            },
            {
                'if' : {
                    'filter_query' : '{Discount} > 0.2',
                    'column_id' : 'Discount'
                },
                'backgroundColor' : '#ffedcc',
                'color' : 'black'
            }
        ]

    water_df = filter_df.groupby('Sub-Category', as_index=False)['Sales'].sum().sort_values(by='Sales', ascending=False)
    water_chart = go.Figure(go.Waterfall(
        name="Sales Flow",
        orientation="v",
        measure=["relative", "relative", "total"],
        x=["Product A", "Product B", "Total"],
        y=[300, -150, 0],  # Total is auto-calculated
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))

    water_chart.update_layout(template='plotly_dark', plot_bgcolor='#121212', paper_bgcolor='#121212',
                              font_color='white')

    monthly_df = filter_df.groupby('Month', as_index=False)[selected_metrics].sum().sort_values(by='Month')
    time_chart = px.line(
        monthly_df,
        x='Month',
        y= selected_metrics,
        title= f'Montly {selected_metrics} Trend',
        markers= True,
        template= 'plotly_dark'
    )

    return table_data, table_columns, kpis, bar_chart, pie_chart, style_conditions, water_chart, time_chart

@app.callback(
    Output('download-dataframe-csv', 'data'),
    Input('download-button', 'n_clicks'),
    State('category-filter', 'value'),
    State('region-filter', 'value'),
    State('subcat-filter', 'value'),
    prevent_initial_call=True
)
def download_filtered_data(n_clicks, category, region, subcat):
    temp_df = df.copy()

    if category:
        temp_df = temp_df[temp_df['Category'].isin(category)]

    if region:
        temp_df = temp_df[temp_df['Region'].isin(region)]

    if subcat:
        temp_df = temp_df[temp_df['Sub-Category'].isin(subcat)]


    return dcc.send_data_frame(temp_df.to_csv, 'filtered_inventory.csv', index=False)


if __name__ == "__main__":
    app.run(debug=False,
            host= "0.0.0.0",
            port = int(os.environ.get('PORT', 8050))
            )
