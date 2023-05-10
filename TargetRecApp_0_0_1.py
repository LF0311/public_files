import folium
import streamlit as st
from streamlit_folium import st_folium
import os
import time
#from lib import tickingClock
import streamlit.components.v1 as components
#from time import time, localtime, sleep
import numpy as np

import plotly.graph_objects as go
import pandas as pd

def main():
    MAGE_EMOJI_URL = "streamlitBKN.png"
    st.set_page_config(page_title='环境传感器目标识别平台', page_icon=MAGE_EMOJI_URL, initial_sidebar_state='collapsed',
                       layout="wide")

    st.markdown(
        f'''
            <style>
                .reportview-container .sidebar-content {{
                    padding-top: {0}rem;
                }}
                .appview-container .main .block-container {{
                    {f'max-width: 100%;'}
                    padding-top: {0}rem;
                    padding-right: {1}rem;
                    padding-left: {1}rem;
                    padding-bottom: {0}rem;
                    overflow: auto;
                }}
            </style>
            ''',
        unsafe_allow_html=True,
    )

    st.subheader("  ")

    colmns0 = st.columns(3, gap="medium")

    with colmns0[1]:
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold">环境传感器目标识别平台</p></nobr>', unsafe_allow_html=True)
    with colmns0[0]:
        timestr = time.strftime('%Y-%m-%d %H:%M:%S')
        st.metric(label=' ', value=timestr)

    # 添加地图信息
    locations = [[39.91667, 116.41667 ],[31.231706, 121.472644], [30.58435, 114.29857],
                 [28.19409, 112.982279], [30.659462, 104.065735], [23.16667, 113.23333]]
    customers = ['北京', '上海', '武汉', '长沙', '成都', '广州']

    colmns = st.columns([2,5,2], gap="small")
    with colmns[1]:
        m = folium.Map(location=[34.90960, 145.39722], # 145.39722
                       tiles=None,
                       zoom_start=3.2,
                       control = False,
                       control_scale = True)

        folium.TileLayer(tiles='http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',
                         attr="&copy; <a href=http://ditu.amap.com/>高德地图</a>",
                         min_zoom=0,
                         max_zoom=19,
                         control=True,
                         show=True,
                         overlay=False,
                         name='baseLayer',
                         opacity=1.0
                         ).add_to(m)


        # add marker and link tooltip
        for c_idx in np.arange(0,len(customers)):
            #print(locations[c_idx])
            marker = folium.Marker(
                locations[c_idx],
                # popup = customers[c_idx], # app_links[c_idx]
                tooltip = customers[c_idx],
                icon=folium.Icon(icon="cloud"),
                # icon = folium.features.CustomIcon("https://i.gifer.com/9C4G.gif", icon_size=(14, 14))
            )
            marker.add_to(m)
        st_data = st_folium(m, width=1500, height=400)

        col_sub_1, col_sub_2, col_sub_3 = st.columns(3, gap="large")

        with col_sub_1:
            # st.write("声频")
            st.image("声频信号.png", caption = "声频信号", width=300)
            # st.write("振动")
            st.image("振动信号.jpg", caption = "振动信号", width=300)
            # st.write("地磁")
            st.image("地磁信号.png", caption = "地磁信号", width=300)
        with col_sub_2:
            # st.write("")
            st.selectbox('选择节点：',
                ('2023001', '2023002', '2023003', '2023004', '2023005',
                 '2023006', '2023007', '2023008', '2023009', '2023010',))
            st.markdown("###")
            st.markdown("###")
            st.write("识别结果")
            st.image("pic1.png", width=100)


        with col_sub_3:
            st.markdown("###")
            st.checkbox('动态时间规整算法')
            st.checkbox('决策树算法')
            st.checkbox('神经网络算法')
            st.markdown("###")
            st.markdown("###")
            st.markdown("###")
            st.markdown("###")
            st.write("广播警告")
            st.markdown("###")
            st.markdown("###")
            st.image("pic2.png", width=200)
        #     pass


    # First Columns
    with colmns[0]:

        visitor_clicked = st.button(label="🚀 刷新页面", help="刷新", key=None,
                     on_click=None, args=None, kwargs=None)

        # 按钮字体
        st.markdown("""<style>p, ol, ul, dl
        {
        margin: 0px 0px 1rem;
        padding: 0px;
        font-size: 1.2rem;
        font-weight: 800;
        }
        </style>""", unsafe_allow_html=True)


        col1, col2, col3 = st.columns(3)

        with col1:
            pass
        with col3:
            pass
        with col2:
            st.button(' 开始识别 ')


        st.markdown("""<style>.css-16idsys p
        {
        word-break: break-word;
        margin-bottom: 10px;
        font-size: 18px;
        }
        </style>""", unsafe_allow_html=True)

        st.markdown('###')

        txt = st.text_area(label="实时报文监测", value =
            '''节点2023XX1与2023年1月1日00时00分00秒识别到振动信号
节点2023XX1与2023年1月1日00时00分00秒识别到声频信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号
节点2023XX1与2023年1月1日00时00分00秒识别到磁场信号 ''', height = 650)

    with colmns[2]:
        st.markdown("已部署环境传感器")
        st.markdown('<p style="font-family:sans sarif; text-align: center;color:#38a800; font-size: 30px; font-weight: bold">99</p>', unsafe_allow_html=True)
        # st.metric(label="已部署环境传感器", value=99)
        st.markdown("###")
        st.markdown("正常工作率")
        # st.metric(label="正常工作率", value='99%')
        st.markdown('<p style="font-family:sans sarif; text-align: center;color:#ff4500; font-size: 30px; font-weight: bold">99%</p>', unsafe_allow_html=True)
        st.markdown("###")
        st.markdown("节点状态列表")
        # parameters = st.expander("", True)


        df1 = pd.read_csv("Node status_list-1.csv",sep=',', encoding='GBK') #, header=None
        df1 = df1.apply(lambda x: x.astype(str))
        # 重置行索引为默认整数索引
        df1 = df1.reset_index(drop=True)
        # 修改行索引从 1 开始
        df1.index = range(1, len(df1) + 1)
        # st.table(df1)
        st.dataframe(df1, width = 400, height=560)


    st.markdown("------")
    # Button Style
    st.markdown("""<style> div.stButton > button:first-child {
    background-color: white;
    color: black;
    height:4em; 
    width:8em; 
    border-radius:20px 20px 20px 20px;
    border: 3px solid #008CBA;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("""<style> div.stButton > button:hover {
    background-color: #008CBA;
    color: white;
    }
    </style>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
