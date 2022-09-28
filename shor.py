# -*- coding: utf-8 -*-
"""
Created on Fri Sep 23 09:28:37 2022

@author: daniela.castillo
"""
import pandas as pd 
import geopy.distance
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
import numpy as np
import googlemaps


cabeceras=pd.read_excel("GEOCENTROS.xlsx", converters={'COD_DANE':str})
aerop=pd.read_excel("AEROPUERTOS_COL.xlsx", converters={'CODDANE_MP':str})

gmaps = googlemaps.Client(key='your key')

mun_aerop=list(aerop["CODDANE_MP"])

cabeceras.sort_values(by=["COD_DANE"], inplace=True)


def google_distances(df): 
    time_list = []
    distance_list = []
    origin_id_list = []
    destination_id_list = []
    for i in range(0, df.shape[0]):
        global result
        LatOrigin = df.iloc[i,4]
        LongOrigin = df.iloc[i,3]
        origin = (LatOrigin, LongOrigin)
        origin_id = df.iloc[i,2]
        for j in range(0, df.shape[0]):
            if df.iloc[i,0]==df.iloc[j,0]: 
                time_list.append(0)
                distance_list.append(0)
                origin_id_list.append(origin_id)
                destination_id_list.append(origin_id)
            else: 
                LatDestination = df.iloc[i,4]
                LongDestination = df.iloc[j,3]
                destination_id = df.iloc[j,2]
                destination = (LatDestination, LongDestination)
                try:
                    result = gmaps.distance_matrix(origin, destination, mode = 'driving')
                    result_distance = result["rows"][0]["elements"][0]["distance"]["value"]
                    result_time = result["rows"][0]["elements"][0]["duration"]["value"]
                except: 
                    result_distance = np.nan
                    result_time = np.nan
                else: 
                    result = gmaps.distance_matrix(origin, destination, mode = 'driving', units = 'metric')
                    result_distance = result["rows"][0]["elements"][0]["distance"]["value"]
                    result_time = result["rows"][0]["elements"][0]["duration"]["value"]
                time_list.append(result_time)
                distance_list.append(result_distance)
                origin_id_list.append(origin_id)
                destination_id_list.append(destination_id)
        
    output = pd.DataFrame(distance_list, columns = ['Distance in meter'])
    output['duration in seconds'] = time_list
    output['origin_id'] = origin_id_list
    output['destination_id'] = destination_id_list
    return output

municipios_a_visitar=["52838", "52835"]
cabeceras_cortadas=cabeceras[cabeceras["COD_DANE"].isin(municipios_a_visitar)==True]
out=google_distances(cabeceras_cortadas)


def llenar_edges(municipios_visitar_ed):
    we_edges=[]
    cabeceras_cortadas=cabeceras[cabeceras["COD_DANE"].isin(municipios_visitar_ed)==True]
    for i in range(0, cabeceras_cortadas.shape[0]):
        for j in range(0, cabeceras_cortadas.shape[0]): 
            we_edges.append([cabeceras_cortadas.iloc[i,1], cabeceras_cortadas.iloc[j,1], 
                             geopy.distance.geodesic((cabeceras_cortadas.iloc[i,3], 
                                                      cabeceras_cortadas.iloc[i,4]), (cabeceras_cortadas.iloc[j,3], cabeceras_cortadas.iloc[j,4])).km])
    return we_edges


def ruta_mas_corta(municipios_visitar):
    we_edge=llenar_edges(municipios_visitar)
    graph=[]
    for i in municipios_visitar:
        line=[]
        for j in municipios_visitar:
            for k in we_edge: 
                if k[0]==i and k[1]==j: 
                    line.append(k[2])
        graph.append(line)

    return graph

def aeropuerto_mas_cercano(municipio_origen_1):
    coord_municipio_origen=(cabeceras.loc[cabeceras['COD_DANE'] == municipio_origen_1, 'POINT_Y'].iloc[0], 
                            cabeceras.loc[cabeceras['COD_DANE'] == municipio_origen_1, 'POINT_X'].iloc[0])
    dist_aerop_min=9999999
    nombre_aero_min="nan"
    
    for j in range(0, aerop.shape[0]):
        coordenada_aeropuerto=(aerop.iloc[j,1], aerop.iloc[j,2])
        nombre_aeropuerto=aerop.iloc[j,0]
        distancia= geopy.distance.geodesic(coordenada_aeropuerto, coord_municipio_origen).km
        if distancia<dist_aerop_min: 
            dist_aerop_min=round(distancia)
            nombre_aero_min=nombre_aeropuerto
            
    print("El aeropuerto más cercano al punto de origen es: ", nombre_aero_min, " a una distancia de: ", str(dist_aerop_min), " km.")
    return 


def path(municipio_origen, municipios_visitar_1):
    graph=ruta_mas_corta(municipios_visitar_1)
    graph_01 = csr_matrix(graph)    
    dist_matrix, predecessors  =shortest_path(csgraph=graph_01, directed=False, return_predecessors=True, method='FW')
    
    i = municipios_visitar_1.index(municipio_origen)
    path = [i]
    path_codigos_mun=[municipios_visitar_1[path[0]]]
    path_nombres_mun=[cabeceras.loc[cabeceras['COD_DANE'] == path_codigos_mun[0], 'MUNICIPIO'].iloc[0]]
    
    while len(path) != predecessors.shape[0]:
        current_node=path[-1]
        current_distances=dist_matrix[current_node]
        for h in path:
            current_distances[h]=0    
        distance_closer_node=current_distances[current_distances != 0].min()
        next_node=np.where(current_distances == distance_closer_node)[0][0]
        path.append(next_node)
        path_codigos_mun.append(municipios_visitar_1[path[len(path)-1]])
        path_nombres_mun.append(cabeceras.loc[cabeceras['COD_DANE'] == path_codigos_mun[len(path)-1], 'MUNICIPIO'].iloc[0])
    
    aeropuerto_mas_cercano(municipio_origen)
    return path, path_codigos_mun, path_nombres_mun


municipios_a_visitar=["52835","52260", "52405","52540", "52079", "52418", "52520", "52256", "52621"]
ruta_nodos, ruta_cod_dane, ruta_municipios= path("52835", municipios_a_visitar)
print("La ruta a seguir es: ", ruta_municipios)





