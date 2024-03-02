import pandas as pd
import geopandas as gpd
from flask import Blueprint, render_template,current_app
from app.utils.db import get_db_connection
from app.utils.cluster import start_hierarchical,create_dendrogram,cluster,make_base_map
from app.utils.leg_api import find_close_votes
from app.utils.style import generate_colorscale,style_handle
from plotly.offline import plot 
from dash import Dash, html, dcc, Input, Output
import dash_leaflet as dl
import json
import os
from . import vote_bp

current_file_path = os.path.abspath(__file__)
app_root_path = os.path.join(current_file_path, '..', '..', '..', '..')
shapefile_directory = os.path.join(app_root_path, 'app', 'data', 'nycc_22a')


vote_bp = Blueprint('vote', __name__, template_folder='templates')

def get_table_df(table):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table};')  
    raw = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    df = pd.DataFrame(raw, columns=columns)
    return df

@vote_bp.route('/')
def vote():
    df_vote = get_table_df('vote')
    close_votes = find_close_votes(df_vote)
    Z = start_hierarchical(close_votes)
    dendrogram = create_dendrogram(Z)
    dendrogram_div = plot(dendrogram, output_type='div', include_plotlyjs=False)
    return render_template('vote.html', dendrogram=dendrogram_div)

def create_dash_app(app):
    gdf = gpd.read_file(shapefile_directory)
    df_vote = get_table_df('vote')
    cc_df = get_table_df('members')
    close_votes = find_close_votes(df_vote)
    Z = start_hierarchical(close_votes)

    initial_threshold = 40  
    clusters = cluster(Z, close_votes, initial_threshold)
    clusters_coords = make_base_map(clusters, cc_df, gdf)
    geojson_data = json.loads(clusters_coords.to_json())
    num_clusters = 5
    colorscale = generate_colorscale(num_clusters, geojson_data)
    style = dict(weight=2, opacity=1, color='white', dashArray='3', fillOpacity=0.7)

    centroid = clusters_coords.geometry.centroid
    mean_lat, mean_lon = centroid.y.mean(), centroid.x.mean()

    dash_app = Dash(__name__, server=app, url_base_pathname='/vote/map/')

    hover_info = html.Div(
        id="hover-info",
        style={
            "position": "absolute",
            "top": "10px",
            "right": "10px",
            "zIndex": "1000",
            "background-color": "white", 
            "padding": "10px",  
            "border": "1px solid #ccc", 
            "border-radius": "5px",  
            "box-shadow": "0 0 5px rgba(0, 0, 0, 0.2)" 
        }
    )
    
    dash_app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content'),
        html.Div([
        html.H2("Cluster Map", style={'font-family': 'Georgia','padding': '10px','textAlign': 'center'}),
        html.P("The numbers on the slider correspond to the numbers on the y-axis above. As you move the slider the map will change to display the new number of clusters. Hover over the map to see the district number, the council member's name, and the cluster number."), 
    ]),
    dcc.Slider(
        id='cluster-threshold-slider',
        min=0,
        max=100,  
        step=1,
        value=40,  
        marks={i: str(i) for i in range(0, 101, 10)},  
    ),
    html.Div(id='slider-output-container'),  
    html.Div([
        dl.Map(center=[mean_lat, mean_lon], zoom=12, children=[
            dl.TileLayer(),
            dl.GeoJSON(data=geojson_data,  
                         style=style_handle,  
                         hideout=dict(colorscale=colorscale, num_clusters=num_clusters, style=style),
                         id="geojson")
        ], style={'width': '100%', 'height': '75vh', 'padding-bottom': '20px', 'margin-bottom': '50px'}),

        hover_info  
    ], style={'position': 'relative'}),
    ])

    @dash_app.callback(
        Output("geojson", "data"),
        [Input("cluster-threshold-slider", "value")]
    )
    def update_output(value):
        clusters = cluster(Z, close_votes, value)
        num_clusters = clusters['h_cluster'].nunique()
        clusters_coords = make_base_map(clusters, cc_df, gdf)
        new_geojson_data = json.loads(clusters_coords.to_json())
        colorscale = generate_colorscale(num_clusters, new_geojson_data)
        return new_geojson_data

    @dash_app.callback(
        Output("hover-info", "children"),
        Input("geojson", "hoverData")
    )
    def update_hover_info(hover_data):
        if hover_data is not None:
            properties = hover_data["properties"]
            office_name = properties.get("OfficeRecordFullName", "N/A") 
            district = properties.get("District", "N/A") 
            cluster_number = properties.get("h_cluster", "N/A") 

            return [
                html.H4("District Information"),
                html.P(f"Council Member: {office_name}"),
                html.P(f"District: {district}"),
                html.P(f"Cluster: {cluster_number}")
            ]
        return []


    @dash_app.callback(
        Output('geojson', 'hideout'), 
        [Input("cluster-threshold-slider", "value")]
    )
    def update_hideout(value):

        clusters = cluster(Z, close_votes,value)
        num_clusters = clusters['h_cluster'].nunique()
        clusters_coords = make_base_map(clusters, cc_df, gdf)
        new_geojson_data = json.loads(clusters_coords.to_json())
        colorscale = generate_colorscale(num_clusters, new_geojson_data)
    
        new_hideout = {
            'colorscale': colorscale,
            'num_clusters': num_clusters,
            'style' : style
        }


        return new_hideout



    return dash_app
