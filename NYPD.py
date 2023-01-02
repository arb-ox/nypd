# import libraries
import pandas as pd
import plotly.express as px
from dash import dash, html, dcc
from dash.dependencies import Input, Output
import datetime
import requests
import io
import config

# import dataset
url = "https://raw.githubusercontent.com/arb-ox/nypd/main/NYPD_Arrest_Data__Year_to_Date_.csv"
download = requests.get(url).content
df = pd.read_csv(io.StringIO(download.decode('utf-8')))

# drop unnecessary columns to speed up processes
df.drop(["ARREST_KEY", "PD_CD", "PD_DESC", "KY_CD", "LAW_CODE", "LAW_CAT_CD", "ARREST_PRECINCT", "JURISDICTION_CODE", "X_COORD_CD", "Y_COORD_CD", "New Georeferenced Column"], axis=1, inplace=True)
df.drop(df[df["OFNS_DESC"] == "(null)"].index, inplace=True)

# change datatypes to reduce memory usage and set date/time column
df["ARREST_DATE"] = pd.to_datetime(df["ARREST_DATE"])
df = df.astype({"OFNS_DESC": "category", "ARREST_BORO": "category", "AGE_GROUP": "category", "PERP_SEX": "category", "PERP_RACE": "category"})

# transform columns for usage in visualization part
df["OFNS_DESC"] = df["OFNS_DESC"].str.title()
df["ARREST_BORO"].replace(to_replace=dict(K="Brooklyn", Q="Queens", B="Bronx", S="Staten Island", M="Manhattan"), inplace=True)
top_10 = df["OFNS_DESC"].value_counts()[:10]
df = df[df["OFNS_DESC"].isin(top_10.index)]

# define variables and set mapbox accesstoken
mapbox_accesstoken = config.mapbox_accesstoken
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September"]

# run app
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
app.title = "NYPD 2022 Arrests"
server = app.server

# app layout, further styling through .css files in "assets" folder
app.layout = html.Div([
    html.Div(
        className="row",
        children=[
            html.Div(
                className="three columns div-user-controls",
                children=[
                    html.A(
                        html.Img(
                            className="logo",
                            src=app.get_asset_url("NYPD_logo.png"),
                        ),
                        href="https://de.wikipedia.org/wiki/New_York_City_Police_Department"
                    ),
                    html.H2("NYPD Criminal Reports App with DASH"),
                    html.P(
                        """This is a breakdown of every arrest effected by the NYPD in the ten most common offenses in NYC during 2022.
                        Each record represents an arrest effected by the NYPD and includes information about
                        the type of crime, the location of enforcement as well as gender and age-group of the arrested."""
                    ),
                    html.Div(
                        className="div-for-dropdown",
                        children=[
                            dcc.Dropdown(
                                        id="date-picker",
                                        options=months,
                                        placeholder= "Select a Month",
                                        value="January"
                            )
                        ]
                    ),
                    html.Div(
                        className="row",
                        children=[
                            html.Div(
                                className="div-for-dropdown",
                                children=[
                                    dcc.Dropdown(
                                        id="graph-select",
                                        options=["Per Offense Types", "Per Boroughs"],
                                        placeholder= "Select a Plot",
                                        value="Per Offense Types"
                                    )
                                ]
                            )
                        ]
                    )]
                    ),
    html.Div(
        className="nine columns div-for-charts bg-grey",
        children=[
            dcc.Graph(id="scattermapbox"),
            dcc.Graph(id="plots")
        ])
    ])
]
)

# create callbacks
@app.callback(
    Output("scattermapbox", "figure"),
    Input("date-picker", "value")
)
def update_scattermapbox(selection):
    month = datetime.datetime.strptime(selection, '%B').month
    df_temp = df[df["ARREST_DATE"].dt.month == month]
    
    fig = px.scatter_mapbox(df_temp, lat="Latitude", lon="Longitude", color="OFNS_DESC", 
                            size_max=15, zoom=10,
                            hover_data=[df_temp["AGE_GROUP"], df_temp["PERP_SEX"]])
    
    fig.update_layout(autosize=True, margin={"l": 0, "r": 20, "t": 0, "b": 0},
                      mapbox={"accesstoken": mapbox_accesstoken,
                              "style": "dark",
                              "bearing": 0,
                              "zoom": 12},
                      legend={"title": "Type of Offense",
                              "bgcolor": "#31302F",
                              "y": 0.95},
                      legend_font_color="#d8d8d8")
   
    return fig


@app.callback(
    Output("plots", "figure"),
    Input("date-picker", "value"),
    Input("graph-select", "value")
)
def update_graph(selection, plot):
    month = datetime.datetime.strptime(selection, '%B').month
    df_temp = df[df["ARREST_DATE"].dt.month == month]
    
    if plot == "Per Offense Types":
        fig = px.histogram(x=df_temp["OFNS_DESC"], color=df_temp["OFNS_DESC"], text_auto=".2s", height=355)
        
        fig.update_layout(showlegend=False, plot_bgcolor= "#31302F", paper_bgcolor= "#31302F",
                          yaxis_visible=False, yaxis_showticklabels=False,
                          xaxis_visible=False, xaxis_showticklabels=False,
                          margin={"l": 0,
                                  "r": 0,
                                  "t": 10,
                                  "b": 0})
                       
        fig.update_traces(textfont_size=14, textangle=0, textposition="outside", cliponaxis=False, textfont_color="#d8d8d8")
        
        return fig

    elif plot == "Per Boroughs":
        fig = px.histogram(x=df_temp["ARREST_BORO"], color=df_temp["ARREST_BORO"], text_auto=".2s", height=355,
                           color_discrete_map={"Bronx": "#33FFFB",
                                               "Brooklyn": "#33DDFF",
                                               "Manhattan": "#33B9FF",
                                               "Queens": "#3392FF",
                                               "Staten Island": "#3362FF"})
        
        fig.update_layout(showlegend=False, plot_bgcolor= "#31302F", paper_bgcolor= "#31302F",
                          yaxis_visible=False, yaxis_showticklabels=False,
                          xaxis_visible=True, xaxis_showticklabels=True,
                          margin={"l": 0,
                                  "r": 0,
                                  "t": 10,
                                  "b": 0},
                        xaxis={"title": None,
                               "color": "#d8d8d8",
                               "tickvals": df_temp["ARREST_BORO"].unique(),
                               "categoryorder": "category ascending"})
        
        fig.update_traces(textfont_size=14, textangle=0, textposition="outside", cliponaxis=False, textfont_color="#d8d8d8")
        
        return fig

## run app
if __name__ == "__main__":
    app.run_server(debug=False)
