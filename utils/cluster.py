import pandas as pd
import numpy as np
import requests
from datetime import datetime
import plotly.figure_factory as ff
from matplotlib import pyplot as plt
import os 

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from .leg_api import find_close_votes

from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.cluster.hierarchy import fcluster

def scale_and_standardize(df):
    one_hot = pd.get_dummies(df, columns=df.columns)
    scaler = StandardScaler()
    scaled_df = scaler.fit_transform(one_hot)
    return scaled_df

def kmeans_cluster(df,n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(df)
    df['cluster'] = kmeans.labels_
    return kmeans

def hierarchical_cluster(df):
    Z = linkage(df, 'ward')
    return Z

def plot_denogram(Z,df):
    plt.figure(figsize=(25, 10))
    dendrogram(Z, labels=df.index, leaf_rotation=90)
    plt.title('Hierarchical Clustering Dendrogram')
    plt.xlabel('sample index')
    plt.ylabel('distance')
    dendrogram(Z, leaf_rotation=90., leaf_font_size=8.)
    plt.show()

def cluster(Z,df,threshold):
    df = df.copy()
    distance_threshold = threshold
    clusters = fcluster(Z, distance_threshold, criterion='distance')
    df['h_cluster'] = clusters
    return df

def merge_with_cluster(cm_df,cluster_df):
    master = pd.merge(cm_df, cluster_df, left_on='OfficeRecordFullName', right_on='VotePersonName', how='left')
    return master

def run_kmeans_on_click(df, n_clusters):
    close_votes = find_close_votes(df)
    scaled_df = scale_and_standardize(close_votes)
    kmeans = kmeans_cluster(scaled_df,n_clusters)
    return kmeans

def start_hierarchical(close_votes):
    scaled_df = scale_and_standardize(close_votes)
    Z = hierarchical_cluster(scaled_df)
    return Z

def make_base_map(df,CM_DATA,gdf):
    gdfe = gdf.to_crs(epsg=4326)
    df = df.reset_index()
    master = pd.merge(CM_DATA, df, left_on='OfficeRecordFullName', right_on='VotePersonName', how='left')
    master = master[['OfficeRecordFullName', 'District', 'h_cluster']].copy() 
    master_map = pd.merge(gdfe, master, left_on='CounDist', right_on='District', how='left')

    return master_map

def generate_colorscale(num_clusters, geojson_data):
    cmap = plt.get_cmap('tab20')
    colorscale = [
        "rgba({},{},{},{})".format(int(r * 255), int(g * 255), int(b * 255), a)
        for r, g, b, a in (cmap(i / num_clusters) for i in range(num_clusters))
    ]
    return colorscale

def create_dendrogram(Z):
    fig = ff.create_dendrogram(Z, orientation='bottom')
    fig.update_layout(
        height=600,
        title_text='NYC Council Voting Clusters Dendrogram', 
        title_x=0.5,  
        title_font=dict(size=24, family='Georgia, serif'),
        autosize=True,
        margin=dict(l=40, r=40, t=40, b=40)
    ) 


    fig.update_layout(
        template={
            'data': {
                'bar': [{'error_x': {'color': '#2a3f5f'}, 'error_y': {'color': '#2a3f5f'}, 'marker': {'line': {'color': '#E5ECF6', 'width': 0.5}}, 'type': 'bar'}],
                'pie': [{'automargin': True, 'type': 'pie'}],
                'table': [{'header': {'fill': {'color': '#C8D4E3'}, 'line': {'color': 'white'}, 'align': 'center', 'font': {'family': "Arial", 'size': 12, 'color': 'black'}}, 'cells': {'fill': {'color': '#EBF0F8'}, 'line': {'color': 'white'}, 'align': 'center', 'font': {'family': "Arial", 'size': 11, 'color': '#506784'}}}],
            },
            'layout': {
                'autosize': True,
                'font': {'color': '#2a3f5f'},
                'hovermode': 'closest',
                'margin': {'b': 40, 'l': 40, 'r': 40, 't': 40},
                'plot_bgcolor': 'white',
                'xaxis': {'automargin': True, 'gridcolor': 'white', 'linecolor': 'white', 'ticks': '', 'title': {'standoff': 15}, 'zerolinecolor': 'white', 'zerolinewidth': 2},
                'yaxis': {'automargin': True, 'gridcolor': 'white', 'linecolor': 'white', 'ticks': '', 'title': {'standoff': 15}, 'zerolinecolor': 'white', 'zerolinewidth': 2}
            }
        }
    )
    
    return fig