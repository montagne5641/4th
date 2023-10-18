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


st.title("生育ステージ解析(NDVI) 🌳")
st.markdown("""
圃場NDVIの推移から、生育ステージを解析します。
""")


### 【リンク】
#- [つくば分析センター](https://www.katakuraco-op.com/site_tsukuba/)： こちらで土壌の受託分析を行っています。

# ファイルアップロードして表示
data = st.file_uploader("file_upload", type="csv") 
#data=1 #適当に入れる

if data: #True
        dat =  pd.read_csv(data, encoding = "shift-jis")
        #dat = pd.read_csv(R"C:\Users\220127\Desktop\SpaceAgri_Download_Data_2023.csv", encoding = "shift-jis") 
        dat2 =  dat
        data_disp = st.checkbox('データベース表示')
        make_fig = st.checkbox("グラフを出力する（圃場数≦200の場合のみ）",value = False)
        if data_disp == True :
            st.dataframe(dat2,height=200,width=2000)
        
        # サイドバー
        st.sidebar.title("NDVI解析条件")
        dev_key = st.sidebar.selectbox("キー", ("統括ID","生産圃"))
        
        st.sidebar.write("-------------------")
        

        #品種別
        hinsyu = st.sidebar.multiselect(label="品種（任意）",options=dat2["品種"].unique())
         # "すべて選択" チェックボックス
        select_all_hinsyu = st.sidebar.checkbox("全ての圃場を選択")    

        # チェックボックスの状態に応じてMultiselectウィジェットを制御
        if select_all_hinsyu: #全て選択ボタンが押されている場合
            if hinsyu:
                ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID（必須）",options=dat2.query('品種 in @hinsyu')[dev_key].unique(),default=dat2.query('品種 in @hinsyu')[dev_key].unique())
            else:
                ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID（必須）",options=dat2[dev_key].unique(),default=dat2[dev_key].unique())
        else: #すべて選択が押されていない場合
            if hinsyu:
                ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID（必須）",options=dat2.query('品種 in @hinsyu')[dev_key].unique())
            else:
                ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID（必須）",options=dat2[dev_key].unique())
 

        #生産者別
        #st.sidebar.write("-------------------")
        
        if not hinsyu:
            dev_key2 = st.sidebar.multiselect(label="生産者（任意）",options=dat2["生産者"].unique())

            # "すべて選択" チェックボックス
            select_all = st.sidebar.checkbox("全ての圃場を選択する")
        
            # チェックボックスの状態に応じてMultiselectウィジェットを制御
            if select_all: #全て選択ボタンが押されている場合
                if dev_key2:
                    ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID2（必須）",options=dat2.query('生産者 in @dev_key2')[dev_key].unique(),default=dat2.query('生産者 in @dev_key2')[dev_key].unique())
                else:
                    ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID2（必須）",options=dat2[dev_key].unique(),default=dat2[dev_key].unique())
            else: #すべて選択が押されていない場合
                if dev_key2:
                    ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID2（必須）",options=dat2.query('生産者 in @dev_key2')[dev_key].unique())
                else:
                    ind_dev_key_stocks = st.sidebar.multiselect(label="圃場ID2（必須）",options=dat2[dev_key].unique())



        #st.sidebar.write("-------------------")

        # "グラフを出力する" チェックボックス
        st.sidebar.write("解析対象の圃場数："+str(len(ind_dev_key_stocks)))
        st.sidebar.write("-------------------")

        if len(ind_dev_key_stocks) > 200:
            make_fig =False
    
        if ind_dev_key_stocks:
                min_date = dt.date(2023, 4, 1)
                max_date = dt.date(2023, 9, 30)
                time_course = st.sidebar.slider("解析期間", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                isyoku_to_syukaku = st.sidebar.checkbox("移植日～収穫日に限定する")
                ndvi_pre_cutoff = st.sidebar.slider("NDVI_pre_cutoff", min_value=0.00, max_value=1.00,value=0.10, step=0.05)
                ndvi_cutoff = st.sidebar.slider("NDVI_growth_cutoff", min_value=0.10, max_value=1.00,value=0.50, step=0.05)
                hampel_MAD_cutoff = st.sidebar.slider("hampel_MAD_cutoff", min_value=0.0, max_value=10.0,value=1.0, step=0.5)
                hampel_window_size = st.sidebar.slider("hampel_window_size", min_value=1, max_value=100,value=2, step=1)
                sg_window_size  = st.sidebar.slider("sg_window_size", min_value=3, max_value=101,value=15, step=2)
                sg_polyorder = st.sidebar.slider("sg_polyoder", min_value=1, max_value=20,value=10, step=1)    #sgの多項式近似
                spline_k = st.sidebar.slider("spline_k", min_value=1, max_value=5,value=5, step=1)    #スプラインの多項式、デフォルト3
                spline_s = st.sidebar.slider("spline_s", min_value=0.00, max_value=1.00,value=0.03, step=0.01)    #スプラインのs
                
                # input_num =st.sidebar.number_input('強さ：',0,100,0)
                # input_text =st.sidebar.text_input('国を入力', 'Japan')
                # select_num =st.sidebar.number_input('年(1952~5年おき)',1952,2007,1952,step=5)
                
                #hampel filterを定義#####################################################################################
                import numpy as np
                # '''
                # * Input
                #     * x       input data
                #     * k       half window size (full 2*k+1)          
                #     * thr     threshold (defaut 3), optional
                 
                # * Output
                #     * output_x    filtered data
                #     * output_Idx indices of outliers
                # '''
                def Hampel(x, k, thr=3):
                    arraySize = len(x)
                    idx = np.arange(arraySize)
                    output_x = x.copy()
                    output_Idx = np.zeros_like(x)
                 
                    for i in range(arraySize):
                        mask1 = np.where( idx >= (idx[i] - k) ,True, False)
                        mask2 = np.where( idx <= (idx[i] + k) ,True, False)
                        kernel = np.logical_and(mask1, mask2)
                        median = np.median(x[kernel])
                        std = 1.4826 * np.median(np.abs(x[kernel] - median))
                
                        if np.abs(x[i] - median) > thr * std:
                            output_Idx[i] = 1
                            output_x[i] = median
                 
                    # return output_x, output_Idx.astype(bool)
                    return output_x, output_Idx
                
                
                
                #データベースファイル(csv)を規定########################################################################################
                dat["Date"] = pd.to_datetime(dat["Date"]) #Dateを日付型で定義
                dat =dat.query('Date >= @time_course[0] and Date <= @time_course[1]') #クエリで日付条件抽出
                
                if isyoku_to_syukaku: 
                    if not pd.isna(dat["移植日"][0]):
                       dat =dat.query('Date >= @dat["移植日"][0] and Date <= @dat["収穫日"][0]')  #クエリで日付条件抽出 
                    else:
                        dat=dat
            
                #処理条件を設定########################################################################################################
                dtk = "PB"  #利用するNDVI_meanのDataTypeキー。                       #★★★★★★★★★★★★
                dat_dtk = dat[dat.DataType == dtk] #DataTypeがtarget_keyの行のみ抽出。ほかにPTとかもある。
                dat_dtk = dat_dtk[dat_dtk.NDVI_mean >= ndvi_pre_cutoff] 
                
                #グラフ用リスト作成####################################################################################################
                r=list()
                c=list()
                dev_by = ind_dev_key_stocks  #dat_dtk[dev_key].unique() #分割基準とするカラム名
                
                for j in range(1,abs(len(dev_by)//2)+2): 
                    for jj in[1,2]:
                        c.append(jj) #行リスト作成       
                jjj=[1,1]
                for j in range(1,abs(len(dev_by)//2)+2):
                    for jj in[j,j]:
                        r.append(jj) #列リスト作成
                        jjj=jjj+[1,1]
                        
                #グラフ描写###########################################################################################################
                whole_res = pd.DataFrame()
                whole_hokan = pd.DataFrame()
                fig = make_subplots(rows=max(r), cols=max(c),subplot_titles=dev_by)
                for i,n in enumerate(tqdm(dev_by)):
                    
                    #Hampel filerで異常値検出##########################################################################################
                    sg=pd.DataFrame()
                    sg = Hampel(dat_dtk[dat_dtk[dev_key] == n]["NDVI_mean"].to_numpy(), hampel_window_size, thr=hampel_MAD_cutoff)[0]
                    sg_err = pd.DataFrame(Hampel(dat_dtk[dat_dtk[dev_key] == n]["NDVI_mean"].to_numpy(), hampel_window_size, thr=hampel_MAD_cutoff)[1]*dat_dtk[dat_dtk[dev_key] == n]["NDVI_mean"])
                    sg_err["Date"] = dat_dtk[dat_dtk[dev_key] == n]["Date"].tolist()
                    sg_err["NDVI_mean"] = sg_err["NDVI_mean"].replace(0,"NA")
                    
                    #異常値処理後のポイントから平滑化トレンドラインを作る#################################################################
                    temp_sg = savgol_filter(sg, #元データ
                                       sg_window_size, #window数(正の奇数の整数で指定）
                                       polyorder = sg_polyorder, #多項式の次数
                                       deriv = 0)
                    
                    #解析条件、結果の集計###############################################################################################
                    res = pd.DataFrame()
                    res[dev_key]= [dev_key]*len(sg)
                    res["dev_name"]= [n]*len(sg)
                    res["type_key"] = [dtk]*len(sg)
                    res["Date"] = dat_dtk[dat_dtk[dev_key] == n]["Date"].tolist()
                    res["ndvi_pre_cutoff"] = [ndvi_pre_cutoff]*len(sg)
                    res["raw"] =  dat_dtk[dat_dtk[dev_key] == n]["NDVI_mean"].tolist()
                    res["trend"] = temp_sg
                    res["outlier"] = Hampel(dat_dtk[dat_dtk[dev_key] == n]["NDVI_mean"].to_numpy(), hampel_window_size, thr=hampel_MAD_cutoff)[1]
                    res["higher"] = np.where(res['raw']>res["trend"], res['raw'],res["trend"])
                    res["raw-trend"] = (res['raw'] >= res["trend"]) #rawのほうがtrendによるトレンドよりも大きい　→outlier認定されていてもrawを採用する
                    res["raw-trend"] = [1 if q ==False else 0 for q in res["raw-trend"]]
                    res["outlier"] = res["outlier"] * res["raw-trend"]
                    res = res.drop("raw-trend", axis=1)
                    res["NDVI_cutoff"] =[ndvi_cutoff] *len(sg)
                    res["hampel_MAD_cutoff"] =[hampel_MAD_cutoff] *len(sg)
                    res["hampel_window_size"] =[hampel_window_size] *len(sg)
                    res["sg_window"] =[sg_window_size]*len(sg)
                    res["sg_polyorder"] =[sg_polyorder]*len(sg)
                    res["移植日"] = dat_dtk[dat_dtk[dev_key] == n]["移植日"].tolist()
                    res["倒伏期（70％）"] = dat_dtk[dat_dtk[dev_key] == n]["倒伏期（70％）"].tolist()
                    res["根切日"] = dat_dtk[dat_dtk[dev_key] == n]["根切日"].tolist()
                    res["収穫日"] = dat_dtk[dat_dtk[dev_key] == n]["収穫日"].tolist()

                                 
                    #補間行列を作る
                    hokan_res = res.loc[res.groupby('Date')['higher'].idxmax()].sort_index() #同日に2点以上のプロットがある場合は、最大値を残す
                    x_observed = pd.to_datetime(hokan_res["Date"]).values.astype(float) #一度float形に変換する
                    y_observed = hokan_res["higher"].tolist()
                    new_x = pd.to_datetime(pd.date_range(start=pd.to_datetime(x_observed.min()), end=pd.to_datetime(x_observed.max()), freq='D')).values.astype(float) #float形で連続xを作る
                    fitted_curve = interpolate.UnivariateSpline(x_observed, y_observed,w=hokan_res["higher"],k=spline_k,s=spline_s) #5次曲線で補完、ただし値が高いほど重みを大きくする
                    
                    hokan = pd.DataFrame()
                    hokan["dev_name"]= [n]*len(new_x)
                    hokan["Date"] = pd.to_datetime(new_x)
                    hokan["predict"] = fitted_curve(new_x) 

                    res2=pd.DataFrame()
                    hokan2=pd.DataFrame()
                    
                    if isyoku_to_syukaku:
                        if not pd.isna(res["移植日"][0]):
                            res2 =res.query('Date >= @res["移植日"][0] and Date <= @res["収穫日"][0]') #クエリで日付条件抽出
                            hokan2 =hokan.query('Date >= @res["移植日"][0] and Date <= @res["収穫日"][0]') #クエリで日付条件抽出
                        else:
                            res2 = res
                            hokan2 = hokan                            
                    else:
                        res2 = res
                        hokan2 = hokan


                    
                    if make_fig==True:
                            #トレンドラインを描写（黒）#############################################################################
                            fig.add_trace(go.Scatter(x=hokan2["Date"].tolist(),
                                          y=hokan2["predict"].tolist(),      #高NDVIも低NDVIも異常値とみなす場合
                                          mode='lines',
                                          opacity=1,
                                          showlegend=False,
                                          visible=True,
                                          marker_color ="gray",
                                          line_width=3,
                                          #line_dash ="dot",
                                          name='trend_line',
                                          xaxis="x"+str(i+1),yaxis="y"+str(i+1)),
                                          row=r[i], col=c[i])
                        
                            #異常値を描写（灰）#######################################################################################
                            fig.add_trace(go.Scatter(x=res2[res2["outlier"] != 0]["Date"].tolist(),
                                          y=res2[res2["outlier"] != 0]["raw"].tolist(),
                                          mode='markers',
                                          opacity=0.1,
                                          showlegend=False,              
                                          visible=True,
                                          marker_symbol= 'x',
                                          marker_color="black", 
                                          name="outlier",
                                          xaxis="x"+str(i+1),yaxis="y"+str(i+1)),
                                          row=r[i], col=c[i])  
                            
                            #≧ndvi_cutoffとなる期間を描写（赤）#############################################################################
                            fig.add_trace(go.Scatter(x=hokan2[hokan2["predict"] >= ndvi_cutoff]['Date'].tolist(),
                                          y=[1]*len(hokan2[hokan2["predict"] >= ndvi_cutoff]['Date']),      #高NDVIも低NDVIも異常値とみなす場合
                                          mode='lines',
                                          opacity=1,
                                          showlegend=False,
                                          visible=True,
                                          marker_color ="#d91e1e",
                                          line_width=10,
                                          name="NDVI >="+ str(ndvi_cutoff),
                                          xaxis="x"+str(i+1),yaxis="y"+str(i+1)),
                                          row=r[i], col=c[i])
                            
                            #正常値を描写（カラー）#######################################################################################
                            fig.add_trace(go.Scatter(x=res2[res2["outlier"] != 1]['Date'].tolist(),
                                          y=res2[res2["outlier"] != 1]["raw"].tolist(),
                                          mode='markers',
                                          opacity=1,
                                          showlegend=False,              
                                          visible=True,
                                          marker=dict(
                                                symbol="circle",
                                                size=10,
                                                color=res2[res2["outlier"] != 1]["raw"].tolist(),
                                                colorscale='portland', #https://www.self-study-blog.com/dokugaku/python-plotly-color-sequence-scales/
                                                cmin=0,  # Set the color scale limits
                                                cmax=ndvi_cutoff+0.1,
                                                showscale=False,
                                                line_width=1
                                            ),
                                          name="raw",
                                          xaxis="x"+str(i+1),yaxis="y"+str(i+1)),
                                          row=r[i], col=c[i])   

                            #移植日、収穫日#######################################################################################  
                            def fig_date(date_event,symbol,color,size,y_pos,mytext,text_size):
                                       fig.add_trace(go.Scatter(x=pd.to_datetime(res2[res2["outlier"] != 1][date_event]),
                                                  y=[y_pos],
                                                  mode='markers+text',
                                                  opacity=1,
                                                  showlegend=False,              
                                                  visible=True,
                                                  marker=dict(
                                                        symbol=symbol,
                                                        size=size,
                                                        color=color,
                                                        line_width=1,
                                                        opacity=0,
                                                    ),
                                                  name=date_event,
                                                  textfont=dict(
                                                        size=text_size,
                                                        color="black"
                                                    ),
                                                  text =mytext,
                                                  textposition="top center",
                                                  xaxis="x"+str(i+1),yaxis="y"+str(i+1)),
                                                  row=r[i], col=c[i]) 
                                       
                                        #ラインを入れる
                                       fig.add_trace(go.Scatter(x=[pd.to_datetime(res2[res2["outlier"] != 1][date_event].values[0]),pd.to_datetime(res2[res2["outlier"] != 1][date_event].values[0])],
                                                  y=[0.05,1],
                                                  mode='lines',
                                                  opacity=1,
                                                  line=dict(color='black', width=1,dash='dot'),
                                                  showlegend=False,              
                                                  visible=True,
                                                  name=date_event,
                                                  xaxis="x"+str(i+1),yaxis="y"+str(i+1)),
                                                  row=r[i], col=c[i]) 

                            #st.write(pd.to_datetime(res2[res2["outlier"] != 1]["移植日"].values[0]))
                            fig_date(date_event="移植日",symbol="triangle-right",color="black",size=10,y_pos=-0.05,mytext="移植",text_size=12)
                            fig_date(date_event="倒伏期（70％）",symbol="asterisk",color="black",size=10,y_pos=-0.05,mytext="倒伏70%",text_size=12)
                            fig_date(date_event="根切日",symbol="asterisk",color="black",size=10,y_pos=0.05,mytext="✂",text_size=15)
                            fig_date(date_event="収穫日",symbol="triangle-left",color="black",size=10,y_pos=-0.05,mytext="収穫",text_size=12)
                            fig.update_layout(plot_bgcolor="white")
                      
                                                                     
                    #≧ndvi_cutoffとなる開始日、終了日、日数を表示###################################################################
                    temp_x=[]
                    temp_x2=[]
   
                    if len(list(hokan2[hokan2["predict"] >= ndvi_cutoff]['Date']))>0:
                        temp_x = list(hokan2[hokan2["predict"] >= ndvi_cutoff]['Date'])[0] #初めてカットオフ値を超えたdate
                        temp_x2 = list(hokan2[hokan2["predict"] >= ndvi_cutoff]['Date'])[len(list(hokan2[hokan2["predict"] >= ndvi_cutoff]['Date']))-1] #最後にカットオフ値を超えたdata

                        if make_fig==True:
                            #NDVI>=cutoffの期間を描写する
                            fig.add_annotation(x=temp_x,y=1.1,text= temp_x.strftime('%m/%d'),xref="x"+str(i+1),yref="y"+str(i+1),showarrow=False,font_color='black')
                            fig.add_annotation(x=temp_x2,y=1.1,text= temp_x2.strftime('%m/%d'),xref="x"+str(i+1),yref="y"+str(i+1),showarrow=False,font_color='black')
                      
                        #NDVI>=cutoffの期間を記録する
                        hokan2["s_NDVI≧cutoff"] = [temp_x]*len(hokan2["Date"])
                        hokan2["e_NDVI≧cutoff"] = [temp_x2]*len(hokan2["Date"])
                        d_format = '%Y/%m/%d'
                        s_to_e_days = temp_x2- temp_x
                        hokan2["days_NDVI≧cutoff"] = [s_to_e_days.days]*len(hokan2["Date"])

                        if make_fig==True:
                            fig.add_annotation(x=temp_x2,y=1.21,text= "~"+str(s_to_e_days.days)+"days",xref="x"+str(i+1),yref="y"+str(i+1),showarrow=False,axref="x1", ayref="y1",font_size=12,font_color='black')
                
                    else:
                        hokan2["s_NDVI≧cutoff"] = [0]*len(hokan2["Date"])
                        hokan2["e_NDVI≧cutoff"] = [0]*len(hokan2["Date"])  
                        hokan2["days_NDVI≧cutoff"] = [0]*len(hokan2["Date"])
                
                    #データを保存する#################################################################################################
                    whole_res = pd.concat([whole_res, res2], axis=0)
                    hokan2 = pd.merge(res, hokan2, how='outer',on="Date")
                    whole_hokan = pd.concat([whole_hokan, hokan2], axis=0)
                
                # 2列で表示、8分割して1が5つ分、2が3つ分
                col1, col2 = st.columns([5,3])
                
                if make_fig==True:
                    if len(dev_by)<=1:
                        fig.update_layout(yaxis_title = 'NDVI_mean',autosize=False, width=1000,height=330,plot_bgcolor="whitesmoke")
                    else:
                        fig.update_layout(yaxis_title = 'NDVI_mean',autosize=False, width=1000,height=300+300*(len(dev_by)//2),plot_bgcolor="whitesmoke")
                    fig.update_xaxes(linecolor='lightgray', gridcolor='lightgray',mirror=True,tickformat="%Y-%m-%d",tickangle=-30,dtick ='M1')
                    fig.update_yaxes(range=(0,1.25),linecolor='lightgray', gridcolor='lightgray',mirror=True,dtick =0.25)
                
                if len(dev_by)>=1:
                    st_matrix = whole_hokan.drop_duplicates(subset=["dev_name_y"]).filter(items=["dev_name_y","s_NDVI≧cutoff","e_NDVI≧cutoff","days_NDVI≧cutoff"])
                    st_matrix.columns = [dev_key,"NDVI開始日","NDVI終了日","NDVI継続期間"]                                                           
                    st_matrix['NDVI開始日'] = pd.to_datetime(st_matrix['NDVI開始日']).dt.strftime('%Y-%m-%d')
                    st_matrix['NDVI終了日'] = pd.to_datetime(st_matrix['NDVI終了日']).dt.strftime('%Y-%m-%d')
                    st_matrix['NDVI継続期間'] = st_matrix['NDVI継続期間']
                
                
                #グラフ数が少ない場合のみ画面出力する
                if make_fig==True:
                    if i <=200:
                        col1.title("NDVIの推移")
                        col1.plotly_chart(fig, use_container_width=True)
                        col2.title("解析データ")
                        col2.dataframe(st_matrix)
                        #st.plotly_chart(fig)
                    else:
                        st.write("対象圃場が多い（"+str(len(ind_dev_key_stocks)) +">200）ため、グラフの描写を中止しています。")
                        col2.title("解析データ")
                        col2.dataframe(st_matrix)
                else:
                        col2.title("解析データ")
                        col2.dataframe(st_matrix)
                    
                    
            
                #ダウンロードボタン
                import base64
                csv2 = st_matrix.to_csv(sep=",")
                b64 = base64.b64encode(csv2.encode('utf-8-sig')).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="解析結果.csv">Download Link</a>'
                st.markdown(f"解析結果： {href}", unsafe_allow_html=True)
            
                csv = whole_hokan.fillna("NaN").sort_values(['dev_name_y', 'Date']).to_csv(sep=",")
                b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="interpolated_NDVI_datasets.csv">Download Link</a>'
                st.markdown(f"補間済みNDVIデータ： {href}", unsafe_allow_html=True)
                
                @st.cache_data
                def convert_fig(fig):
                    return fig.to_html().encode('utf-8')
                html = convert_fig(fig)
            
                st.download_button(
                    "Figs Download",
                    html,
                    "Figs.html"
                )
                #解析を出力する########################################################################################################
                #fig.write_html(R"C:\Users\220127\Desktop\SpaceAgri_Download_Data_2023.html") 
                #whole_res.to_csv(R"C:\Users\220127\Desktop\SpaceAgri_Download_Data_2023_res.csv",encoding="shift-jis",sep=",")
                #whole_hokan.fillna("NaN").sort_values(['dev_name_y', 'Date']).to_csv(R"C:\Users\220127\Desktop\SpaceAgri_Download_Data_2023_hokan2.csv",encoding="shift-jis",sep=",")
                #print("fin.")



