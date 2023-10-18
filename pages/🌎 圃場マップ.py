import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.figure import Figure

#解析##########################################################################################################################
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import savgol_filter
from tqdm import tqdm
import datetime as dt
import math
from scipy import interpolate #補完

import folium
from folium import plugins
import geopandas as gpd
from streamlit_folium import st_folium
from streamlit_folium import folium_static
import branca
from PIL import Image

# ページ情報、基本的なレイアウト
st.set_page_config(
    page_title="北海道リモセンPJ",
    page_icon="🧅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("圃場マップ🌎")

#土壌診断結果
st.markdown("""土壌診断データを選択してください。""")
soil_data =  st.file_uploader("file_upload", type="csv")  #pd.read_csv(R"C:\Users\220127\Desktop\remo_sen\Scripts\富良野土壌診断.csv", encoding = "shift-jis")

if soil_data:
    
        #土壌診断データの取り込み
        soil_data = pd.read_csv(soil_data, encoding = "shift-jis")
        soil_data['推移'] = soil_data.iloc[:, 1:len(soil_data)].values.tolist()
        st.markdown("""※デモとして中富良野町だけデータ入れています。""")

        #区域表示
        kuiki_on = st.checkbox("区域を表示する）",value = True)
    
        # 地図表示する際の中心座標を指定
        map = folium.Map(location=[43.342009,142.383147], zoom_start=6)
        
        # ピンを立てる位置を設定
        point_names = ["上富良野町","中富良野町","富良野市"]
        point_locations = [[43.455649,142.467082],[43.405529,142.425041],[43.342009,142.383147]]
        point_info = ['<a href="https://www.example.com" target="_blank">Visit Example.com</a>','<a href="https://www.example.com" target="_blank">Visit Example.com</a>','<a href="https://www.example.com" target="_blank">Visit Example.com</a>']
        
        
        #ピン立て開始
        for i,j in enumerate(point_names):
            folium.Marker(
                location=point_locations[i],
                #popup=point_info[i],
                tooltip=point_names[i],
            ).add_to(map)
            
        # ヒートマップ層を地図に追加
        folium.plugins.HeatMap(
            data=point_locations, # 注意！ ２次元にして渡す
            radius=35, #サイズ
            blur=30, #ぼかし
        ).add_to(map)

        if kuiki_on==True:
            # 日本地図を読み込み
            japan = gpd.GeoDataFrame.from_file("japan_ver84/japan_ver84.shp")
    
            # 北海道を抽出
            ken = japan[japan["KEN"]=="北海道"]
            
            # shpファイルをGeoJSON化
            gjson = ken.to_json()
            
            # GeoJSONをマップに追加
            folium.features.GeoJson(gjson, name="北海道").add_to(map)
   
        # 地図出力
        output = st_folium(map, width=1200, height=500)
        #output = st.components.v1.html(folium.Figure().add_child(map).render(), height=500)
        
        
        #st.write(output["last_object_clicked_tooltip"])
        if output["last_object_clicked_tooltip"] is not None:
            
                st.title("＠"+output["last_object_clicked_tooltip"])
                #st.experimental_rerun()
        
        #画像の表示
        if output["last_object_clicked_tooltip"]=="中富良野町":
            # 2列で表示、8分割して1が1つ分、2が1つ分
            col1, col2 = st.columns([2,4])    
            col1.subheader("🚀衛星分析結果")
            image = Image.open('中富良野町.png')
            col1.image(image, caption='中富良野町',use_column_width=True)
            col2.subheader("🌱土壌分析結果")
            col2.dataframe(soil_data,
                            column_config={
                                "ID": "分析項目",
                                "推移": st.column_config.LineChartColumn( #LineChartColumn   #BarChartColumn
                                    "推移",width="medium")
                            },
                            width = 700,
                            height=450,
                            hide_index=True,)
        
            st.write("コメント")
            st.write("-------------------")
            st.write("✔ 玉の肥大に重要な可給態リン酸は十分量蓄積しています(250mg/土壌100g)。")
            st.write("✔ 例年比、NDVIの立ち上がりが遅い傾向です。〇〇液肥の追肥を推奨します。")
            
        st.write("-------------------")
        st.button('Data Download(仮)')

