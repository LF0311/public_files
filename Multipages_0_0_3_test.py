import folium
import streamlit as st
from streamlit_folium import st_folium
import os
import time
import json
import requests
import subprocess
#from lib import tickingClock
import streamlit.components.v1 as components
#from time import time, localtime, sleep
import numpy as np
import re
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


# 定义一个自定义排序函数，按照文件名中的数字序号排序
def sort_by_number(filename):
    return int(re.findall(r'\d+', filename)[0])


def mean_percentile(percent, df, column_name):
    # percentile = 0.8
    q1, q2 = np.percentile(df[column_name], [100 * (0.5 - percent / 2), 100 * (0.5 + percent / 2)])
    mean80 = df[(df[column_name] >= q1) & (df[column_name] <= q2)][column_name].mean()
    return mean80


def read_files_split(df):
    # 将经纬度和时间分割成三个变量
    df['T'] = df[11].str.split('T:', expand=True)[1].str.split('N:', expand=True)[0]
    df['N'] = df[11].str.split('T:', expand=True)[1].str.split('N:', expand=True)[1].str.split('E:', expand=True)[0]
    df['E'] = df[11].str.split('T:', expand=True)[1].str.split('N:', expand=True)[1].str.split('E:', expand=True)[1]
    # 重命名列名
    df.columns = ['Frame', 'X_Accel', 'Y_Accel', 'Z_Accel', 'X_Gyro', 'Y_Gyro', 'Z_Gyro', 'X_Mag', 'Y_Mag', 'Z_Mag',
                  'Audio', 'Location', 'T', 'N', 'E']
    # 删除Location列
    df['Audio'] = df['Audio'].apply(lambda x: x / 100)
    df['N'] = df['N'].apply(lambda x: float(x) / 100)
    df['E'] = df['E'].apply(lambda x: float(x) / 100)
    df1 = df.drop('Location', axis=1)
    return df1

def progress_bar(progress_text, duration, column):
    # st.spinner(text=progress_text)
    my_bar = column.progress(0)
    for percent_complete in range(1, 101):
        time.sleep(duration / 100)
        my_bar.progress(percent_complete / 100)
        # column.success('完成！')

def app1():
    st.sidebar.success("已选择：🌍  主监测页面")

    directory = "./sensor_files/"

    # 获取目录下的所有文件名，并按照数字序号排序
    files_name = sorted(os.listdir(directory), key=sort_by_number)
    files_nums = []
    files_time = []

    # 定义匹配数字序号的正则表达式
    pattern = r'\d+'

    # 循环处理每个文件
    for filename in files_name:
        # 仅处理.txt文件
        if filename.endswith('.txt'):
            # 提取数字序号
            files_nums.append(re.findall(pattern, filename)[0])
            # 打开文件并读取第一行内容
            with open(directory + filename, 'r') as f:
                first_line = f.readline()
                start_index = first_line.find("T:") + 2
                end_index = first_line.find("N:")
                time_str = first_line[start_index:end_index]
                files_time.append(datetime.datetime.utcfromtimestamp(float(time_str)
                                                                     + 1682395190).strftime('%Y-%m-%d %H:%M:%S'))
            # 提取T和N之间的数字
            # t_value = re.findall(r'T:(\d+\.\d+)', first_line)[0]
            # n_value = re.findall(r'N:(\d+\.\d+)', first_line)[0]
            # 输出结果
            # print(f'File {filename} has number {number}, Time value {time_str}')
    # 将传感器编号左填补为001，002
    files_str_nums = [str(num).zfill(3) for num in files_nums]
    # 获取传感器序列号2023001，2023002
    sensors_label = ['2023' + str(num1) for num1 in files_str_nums]
    curr_status = []
    curr_power = []
    for labels in range(len(sensors_label)):
        curr_status.append('通信正常')
        curr_power.append('正常')
    sensors_label_df = pd.DataFrame({'节点序列号': sensors_label, '当前状态': curr_status, '电量': curr_power})

    sensors_df = pd.DataFrame({'labels': files_str_nums, 'time': files_time})
    # 将日期时间列解析为 Pandas 中的日期时间格式
    sensors_df['time'] = pd.to_datetime(sensors_df['time'], format='%Y-%m-%d %H:%M:%S')

    # 对 DataFrame 进行日期时间排序
    sorted_df = sensors_df.sort_values(by='time', ascending=False).reset_index(drop=True)

    txt_name_time = []
    for name_index in range(len(sorted_df['time'])):
        txt_name_time.append("●  节点2023" + sorted_df['labels'][name_index] + "于" + str(sorted_df['time'][name_index]) + "识别到振动信号")
    txt_name_time_df = pd.DataFrame({'txt': txt_name_time})

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

    # st.container()
    # page_button = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    # if page_button:
    #     option = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    #     st.write('你选择了：', option)

    with colmns0[1]:
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold">环境传感器目标识别平台</p></nobr>', unsafe_allow_html=True)
    with colmns0[0]:
        timestr = time.strftime('%Y-%m-%d %H:%M:%S')
        st.metric(label='时间', value=timestr, label_visibility='collapsed') # visible hidden collapsed

    # 添加地图信息
    locations = [[39.91667, 116.41667 ],[31.231706, 121.472644], [30.58435, 114.29857],
                 [28.19409, 112.982279], [30.659462, 104.065735], [23.16667, 113.23333]]
    customers = ['北京', '上海', '武汉', '长沙', '成都', '广州']

    colmns = st.columns([2,5,2], gap="small")
    with colmns[1]:
        m = folium.Map(location=[34.90960, 145.39722], # 145.39722
                       tiles=None,
                       zoom_start=3.2,
                       control=False,
                       control_scale=True)

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
        st_data = st_folium(m, width=1500, height=350)



    visitor_clicked = colmns[0].button(label="🚀 刷新页面", help="刷新", key=None,
                                on_click=None, args=None, kwargs=None)
    # 按钮字体
    st.markdown("""<style>p, ol, ul, dl
    {
    margin: 0px 0px 1rem;
    padding: 0px;
    font-size: 1.0rem;
    font-weight: 1000;
    }
    </style>""", unsafe_allow_html=True)

    col1, col2, col3 = colmns[0].columns(3, gap="small")

    button2 = col2.button(' 获取实时数据 ')
    button3 = col2.button(' 获取历史数据 ')
    button4 = col2.button(' 开始识别 ')


    if not button4 and not button3:
        if button2:
            # # Run external Python program using subprocess
            # subprocess.run(["python", r"E:\2项目资料\工作项目\目标识别软件编程\Target recognition software\App_0_0_2\UDP_Receive.py"])
            # col2.success("开始获取实时数据")
            progress_container = col2.empty()
            # 第一个进度条

            progress_text = "获取实时数据命令已发送至空基通信平台，等待实时数据传输..."
            # st.markdown(f'<span style="font-family:Arial; font-size:28pt;">{progress_text}</span>',
            #                             unsafe_allow_html=True)
            # root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(5) > div > div.css-c6gdys.edb2rvg0 > div > p
            st.markdown("""<style> div.stButton > button:first-child {
            background-color: white;
            color: black;
            height:3em; 
            width:8em; 
            border-radius:10px 10px 10px 10px;
            border: 3px solid #008CBA;
            }
            </style>""", unsafe_allow_html=True)

            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(5) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)
            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(4) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)

            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(6) > div > div > div > div > div > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)

            my_bar = progress_container.progress(0, text=progress_text)
            for percent_complete in range(1, 11):
                time.sleep(1)
                my_bar.progress(percent_complete / 10, text=progress_text)
            # 删除第一个元素
            progress_container.empty()

            progress_container = col2.empty()
            # 第二个进度条
            progress_text2 = "已获取布撒式传感器实时数据，报文请参见以下数据..."
            my_bar = progress_container.progress(0, text=progress_text2)
            for percent_complete2 in range(1, 11):
                time.sleep(1)
                my_bar.progress(percent_complete2 / 10, text=progress_text2)

            # 删除第二个元素
            progress_container.empty()
            col2.success("请点击开始识别按钮启动目标识别操作!")
            text_area_height = 450
        else:
            text_area_height = 600
    elif not button4 and not button2:
        if button3:
            # # Run external Python program using subprocess
            # subprocess.run(["python", r"E:\2项目资料\工作项目\目标识别软件编程\Target recognition software\App_0_0_2\UDP_Receive.py"])
            # col2.success("开始获取实时数据")
            progress_container = col2.empty()
            # 第一个进度条
            progress_text = "获取历史数据命令已发送至空基通信平台，等待历史数据传输..."

            st.markdown("""<style> div.stButton > button:first-child {
            background-color: white;
            color: black;
            height:3em; 
            width:8em; 
            border-radius:10px 10px 10px 10px;
            border: 3px solid #008CBA;
            }
            </style>""", unsafe_allow_html=True)

            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(5) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)
            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(4) > div > div.css-c6gdys.edb2rvg0 > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)

            st.markdown("""<style> 
            #root > div:nth-child(1) > div.withScreencast > div > div > div > section.main.css-uf99v8.egzxvld5 > div.block-container.css-z5fcl4.egzxvld4 > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(1) > div:nth-child(1) > div > div.css-ocqkz7.e1tzin5v3 > div:nth-child(2) > div:nth-child(1) > div > div:nth-child(6) > div > div > div > div > div > div > p {
            font-size: 4px;
            }
            </style>""", unsafe_allow_html=True)

            my_bar = progress_container.progress(0, text=progress_text)
            for percent_complete in range(1, 11):
                time.sleep(1)
                my_bar.progress(percent_complete / 10, text=progress_text)
            # 删除第一个元素
            progress_container.empty()

            progress_container = col2.empty()
            # 第二个进度条
            progress_text2 = "已获取布撒式传感器历史数据，报文请参见以下数据..."
            my_bar = progress_container.progress(0, text=progress_text2)
            for percent_complete2 in range(1, 11):
                time.sleep(1)
                my_bar.progress(percent_complete2 / 10, text=progress_text2)

            # 删除第二个元素
            progress_container.empty()
            col2.success("请点击开始识别按钮启动目标识别操作!")
            text_area_height = 450
        else:
            text_area_height = 600
    else:
        text_area_height = 600

    # First Columns
    with colmns[0]:
        st.markdown("""<style>.css-16idsys p
        {
        word-break: break-word;
        margin-bottom: 10px;
        font-size: 18px;
        }
        </style>""", unsafe_allow_html=True)

        # st.markdown('###')

        # txt = st.dataframe(txt_name_time_df, height=650)
        multi_line_str = "\n".join(txt_name_time)
        txt2 = st.text_area(label="实时报文监测", value=multi_line_str, height=text_area_height)

    with colmns[2]:
        st.markdown("已部署环境传感器")
        sensors_num = len(sorted_df['labels'])
        st.markdown('<p style="font-family:sans sarif; text-align: center;color:#38a800; font-size: 30px; font-weight: bold">{}</p>'.format(sensors_num), unsafe_allow_html=True)
        # st.metric(label="已部署环境传感器", value=99)
        st.markdown("###")
        st.markdown("正常工作率")
        # st.metric(label="正常工作率", value='99%')
        if sensors_num!=0:
            sensors_work_percent = "100%"
        else:
            sensors_work_percent = "0%"
        st.markdown('<p style="font-family:sans sarif; text-align: center;color:#ff4500; font-size: 30px; font-weight: bold">{}</p>'.format(sensors_work_percent), unsafe_allow_html=True)
        st.markdown("###")
        st.markdown("节点状态列表")
        # parameters = st.expander("", True)

        # df1 = pd.read_csv("Node status_list-1.csv",sep=',', encoding='GBK') #, header=None
        sensors_label_df = sensors_label_df.apply(lambda x: x.astype(str))
        # 重置行索引为默认整数索引
        sensors_label_df = sensors_label_df.reset_index(drop=True)
        # 修改行索引从 1 开始
        sensors_label_df.index = range(1, len(sensors_label_df) + 1)
        # st.table(df1)
        st.dataframe(sensors_label_df, width = 400, height=610)


    col_sub_1, col_sub_2, col_sub_3 = colmns[1].columns([2.5,1,1], gap="small")

    # with col_sub_1:
    #
    #     # st.write("声频")
    #     st.image("声频信号.png", caption = "声频信号", width=300)
    #     # st.write("振动")
    #     st.image("振动信号.jpg", caption = "振动信号", width=300)
    #     # st.write("地磁")
    #     st.image("地磁信号.png", caption = "地磁信号", width=300)

    # with col_sub_2:
        # st.write("")
    col_sub_2.markdown("###")
    # col_sub_2.markdown("###")
    sensor_node = col_sub_2.selectbox('选择节点：', sensors_label)
    # col_sub_2.markdown(type(sensor_node[4::]))
    col_sub_2.markdown("###")
    col_sub_2.markdown("###")
    col_sub_2.markdown("###")
    col_sub_2.write("识别结果")



    with col_sub_3:
        st.markdown("###")
        st.checkbox('动态时间规整', value=True)
        st.checkbox('决策树')
        st.checkbox('神经网络')
        # st.markdown("###")
        st.markdown("###")
        # st.markdown("###")
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown("###")
        st.write("广播警告")

        # st.markdown("###")
        st.markdown("###")
    warning_container = col_sub_3.container()
    # warning_container.image("pic2-2.png", width=150)
    # st.image("pic2.png", width=150)
    col_sub_3.markdown("###")
    col_sub_3.markdown("###")

    # st.markdown("""<style>
    # #bui16__anchor > button > div > p:first-child   {
    # # background-color:white;
    # # color:black;
    # height:2em;
    # # width:8em;
    # # border-radius:10px 10px 10px 10px;
    # # border: 3px solid ;
    # }
    # </style>""", unsafe_allow_html=True)

    st.markdown("""<style> 
    #bui10__anchor > button > div > p:first-child {
    background-color: white;
    color: black;
    height:2em; 
    width:10em; 
    border-radius:5px 5px 5px 5px;
    border: 3px solid #008CBA;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("""<style> 
    #bui10__anchor > button > div > p:hover {
    background-color: #008CBA;
    color: white;
    }
    </style>""", unsafe_allow_html=True)
    st.markdown("""<style>
    #bui10__anchor > button
    {
    padding-top:0px;
    padding-bottom:0px;
    padding-right:0px;
    padding-left:0px;
    border-top-width:0px;
    border-bottom-width:0px;
    border-right-width:0px;
    border-left-width:0px;
    }
    </style>""", unsafe_allow_html=True)

    button5 = col_sub_3.button('发送数据至服务器', help="发送数据",)

    if button4:  # 开始识别按钮
        read_files_name = 'sensor_' + str(int(sensor_node[4:])) + '_gps.txt'
        # st.markdown(read_files_name)
        # 读取文本文件
        read_file_df = pd.read_csv('./sensor_files/'
                                   + read_files_name, sep=',', header=None)
        final_file_df = read_files_split(read_file_df)
        # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

        if len(final_file_df['Audio']) != 0:
            audio_mean = final_file_df['Audio'].mean()
            audio_80 = mean_percentile(0.8, final_file_df, 'Audio')
            if audio_mean <= 66.23 and audio_80 <= 66.23:
                col_sub_2.image("pic1.png", width=120)
                target_mblb = '人员'
            else:
                col_sub_2.image("pic3.png", width=200)
                target_mblb = '车辆'
                # st.markdown(audio_mean)
        warning_container.empty()
        warning_container.image("pic2.png", width=150)
        # audio_75 = final_file_df['Audio'].describe()['75%'] 6592.771144278607, 6593.689440993789, 6573.0, 6623.0
        # audio_65 = final_file_df['Audio'].quantile(0.70)
        # audio_35 = final_file_df['Audio'].quantile(0.35)
        # 计算80%的平均值


        # 创建X,Y,Z轴加速度散点图
        trace1_1 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['X_Accel'],
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='X_Accel'
        )

        trace1_2 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Y_Accel'],
            mode='lines',
            marker=dict(
                color='blue',
                size=10,
                line=dict(
                    color='blue',
                    width=1
                )
            ),
            name='Y_Accel'
        )

        trace1_3 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Z_Accel'].apply(lambda x: x * -1),
            mode='lines',
            marker=dict(
                color='red',
                size=10,
                line=dict(
                    color='red',
                    width=1
                )
            ),
            name='Z_Accel'
        )

        # 创建声频散点图
        trace2 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Audio'],
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='dB'
        )

        # 创建X,Y,Z轴磁场散点图
        trace3_1 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['X_Mag'].apply(lambda x: x * -1),
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='X_Mag'
        )
        trace3_2 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Y_Mag'].apply(lambda x: x * -1),
            mode='lines',
            marker=dict(
                color='blue',
                size=10,
                line=dict(
                    color='blue',
                    width=1
                )
            ),
            name='Y_Mag'
        )
        trace3_3 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Z_Mag'],
            mode='lines',
            marker=dict(
                color='red',
                size=10,
                line=dict(
                    color='red',
                    width=1
                )
            ),
            name='Z_Mag'
        )

        layout = go.Layout(
            width=300,
            height=150,
        )

        # 将两个散点图放在同一个坐标系中
        fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
        fig2 = go.Figure(data=[trace2], layout=layout)

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(trace3_1, secondary_y=False)
        fig3.add_trace(trace3_2, secondary_y=False)
        fig3.add_trace(trace3_3, secondary_y=True)

        fig1.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='振动信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig2.update_layout(
            margin=dict(l=0,r=10,t=0,b=0),  # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='声频信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(
                showline=True,
                showgrid=True,
                mirror=True,
                nticks=8,
                showticklabels=True,
            ),
        )

        fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
        fig3.update_yaxes(title_text="Z轴磁场信号",
                          showline=True,
                          showgrid=True,
                          mirror=True,
                          nticks=11,
                          showticklabels=True,
                          secondary_y=True)
        fig3.update_layout(
            # title="",
            width=300,
            height=200,
            margin=dict(l=0, r=10, t=0, b=0),
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            # yaxis_title='质量累计含量R(x) - [%]',
            showlegend=True,
            legend=dict(
                font=dict(size=12),
                orientation="h",
                # yanchor="bottom",
                y=1.4,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),

        )

        col_sub_1.plotly_chart(fig1, use_container_width=True)
        col_sub_1.plotly_chart(fig2, use_container_width=True)
        col_sub_1.plotly_chart(fig3, use_container_width=True)

    elif not button5:
        warning_container.empty()
        warning_container.image("pic2-2.png", width=150)
        layout = go.Layout(
            width=300,
            height=150,
        )
        layout1 = go.Layout(
            width=300,
            height=180,
        )
        # 将两个散点图放在同一个坐标系中
        fig1 = go.Figure(data=[], layout=layout)
        fig2 = go.Figure(data=[], layout=layout)
        fig3 = go.Figure(data=[], layout=layout1)

        fig1.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='振动信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig2.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='声频信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig3.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='磁场信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )


        col_sub_1.plotly_chart(fig1, use_container_width=True)
        col_sub_1.plotly_chart(fig2, use_container_width=True)
        col_sub_1.plotly_chart(fig3, use_container_width=True)

    if button5:
        # 将字典转换为JSON格式
        warning_container.empty()
        warning_container.image("pic2.png", width=150)
        read_files_name = 'sensor_' + str(int(sensor_node[4:])) + '_gps.txt'
        read_file_df = pd.read_csv('./sensor_files/'
                                   + read_files_name, sep=',', header=None)
        final_file_df = read_files_split(read_file_df)
        # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

        if len(final_file_df['Audio']) != 0:
            audio_mean = final_file_df['Audio'].mean()
            audio_80 = mean_percentile(0.8, final_file_df, 'Audio')
            if audio_mean <= 66.23 and audio_80 <= 66.23:
                col_sub_2.image("pic1.png", width=120)
                target_mblb = '人员'
            else:
                col_sub_2.image("pic3.png", width=200)
                target_mblb = '车辆'
            # st.markdown(audio_mean)

        # audio_75 = final_file_df['Audio'].describe()['75%'] 6592.771144278607, 6593.689440993789, 6573.0, 6623.0
        # audio_65 = final_file_df['Audio'].quantile(0.70)
        # audio_35 = final_file_df['Audio'].quantile(0.35)
        # 计算80%的平均值

        # 创建X,Y,Z轴加速度散点图
        trace1_1 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['X_Accel'],
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='X_Accel'
        )

        trace1_2 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Y_Accel'],
            mode='lines',
            marker=dict(
                color='blue',
                size=10,
                line=dict(
                    color='blue',
                    width=1
                )
            ),
            name='Y_Accel'
        )

        trace1_3 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Z_Accel'].apply(lambda x: x * -1),
            mode='lines',
            marker=dict(
                color='red',
                size=10,
                line=dict(
                    color='red',
                    width=1
                )
            ),
            name='Z_Accel'
        )

        # 创建声频散点图
        trace2 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Audio'],
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='dB'
        )

        # 创建X,Y,Z轴磁场散点图
        trace3_1 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['X_Mag'].apply(lambda x: x * -1),
            mode='lines',
            marker=dict(
                color='black',
                size=10,
                line=dict(
                    color='black',
                    width=1
                )
            ),
            name='X_Mag'
        )
        trace3_2 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Y_Mag'].apply(lambda x: x * -1),
            mode='lines',
            marker=dict(
                color='blue',
                size=10,
                line=dict(
                    color='blue',
                    width=1
                )
            ),
            name='Y_Mag'
        )
        trace3_3 = go.Scatter(
            x=final_file_df['Frame'],
            y=final_file_df['Z_Mag'],
            mode='lines',
            marker=dict(
                color='red',
                size=10,
                line=dict(
                    color='red',
                    width=1
                )
            ),
            name='Z_Mag'
        )

        layout = go.Layout(
            width=300,
            height=150,
        )

        # 将两个散点图放在同一个坐标系中
        fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
        fig2 = go.Figure(data=[trace2], layout=layout)

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(trace3_1, secondary_y=False)
        fig3.add_trace(trace3_2, secondary_y=False)
        fig3.add_trace(trace3_3, secondary_y=True)

        fig1.update_layout(
            margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='振动信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig2.update_layout(
            margin=dict(l=0, r=10, t=0, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            # xaxis_title='时间 - [秒]',
            yaxis_title='声频信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(
                showline=True,
                showgrid=True,
                mirror=True,
                nticks=8,
                showticklabels=True,
            ),
        )

        fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
        fig3.update_yaxes(title_text="Z轴磁场信号",
                          showline=True,
                          showgrid=True,
                          mirror=True,
                          nticks=11,
                          showticklabels=True,
                          secondary_y=True)
        fig3.update_layout(
            # title="",
            width=300,
            height=200,
            margin=dict(l=0, r=10, t=0, b=0),
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            # yaxis_title='质量累计含量R(x) - [%]',
            showlegend=True,
            legend=dict(
                font=dict(size=12),
                orientation="h",
                # yanchor="bottom",
                y=1.4,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),

        )

        col_sub_1.plotly_chart(fig1, use_container_width=True)
        col_sub_1.plotly_chart(fig2, use_container_width=True)
        col_sub_1.plotly_chart(fig3, use_container_width=True)
        trans_data = {}
        trans_data.update(
            {
                'JDMIN': final_file_df['N'].min(),
                'JDMAX': final_file_df['N'].max(),
                'WDMIN': final_file_df['E'].min(),
                'WDMAX': final_file_df['E'].max(),
                'MBLB': target_mblb,
                'JTLX': None,
                'MBGS': len([sensor_node]),
                'SBXH': '声噪',
                'FXSJ': str(sensors_df.query("labels == '{}'".format(sensor_node[4:]))['time'].values[0]),

            }
        )
        # st.markdown(trans_data)
        json_data = json.dumps(trans_data, ensure_ascii=False)
        # st.markdown(json_data)
        # 发送POST请求
        url = 'http://51.51.51.15:18000/resourceManagerWLW/sendTargetInfo'
        response = requests.post(url, json=trans_data)

        # 打印响应结果
        # print(response.text)

    st.markdown("------")
    # Button Style
    st.markdown("""<style> div.stButton > button:first-child {
    background-color: white;
    color: black;
    height:3em; 
    width:8em; 
    border-radius:10px 10px 10px 10px;
    border: 3px solid #008CBA;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown("""<style> div.stButton > button:hover {
    background-color: #008CBA;
    color: white;
    }
    </style>""", unsafe_allow_html=True)

def app2():
    st.sidebar.success("已选择：📊  目标识别数据库")
    directory_person = "./" \
                       "recognition_database/person/"
    directory_vehicle = "./" \
                        "recognition_database/vehicle/"

    # 获取目录下的所有文件名，并按照数字序号排序
    person_files_name = sorted(os.listdir(directory_person), key=sort_by_number)
    vehicle_files_name = sorted(os.listdir(directory_vehicle), key=sort_by_number)

    person_files_nums = []
    vehicle_files_nums = []
    person_files_time = []
    vehicle_files_time = []

    # 定义匹配数字序号的正则表达式
    pattern = r'\d+'

    # 循环处理每个文件
    for filename1 in person_files_name:
        # 仅处理.txt文件
        if filename1.endswith('.txt'):
            # 提取数字序号
            person_files_nums.append(re.findall(pattern, filename1)[0])
            # 打开文件并读取第一行内容
            with open(directory_person + filename1, 'r') as f:
                first_line = f.readline()
                start_index = first_line.find("T:") + 2
                end_index = first_line.find("N:")
                time_str = first_line[start_index:end_index]
                person_files_time.append(datetime.datetime.utcfromtimestamp(float(time_str)
                                                                     + 1682395190).strftime('%Y-%m-%d %H:%M:%S'))
    for filename2 in vehicle_files_name:
        # 仅处理.txt文件
        if filename2.endswith('.txt'):
            # 提取数字序号
            vehicle_files_nums.append(re.findall(pattern, filename2)[0])
            # 打开文件并读取第一行内容
            with open(directory_vehicle + filename2, 'r') as f:
                first_line = f.readline()
                start_index = first_line.find("T:") + 2
                end_index = first_line.find("N:")
                time_str = first_line[start_index:end_index]
                vehicle_files_time.append(datetime.datetime.utcfromtimestamp(float(time_str)
                                                                     + 1682395190).strftime(
                            '%Y-%m-%d %H:%M:%S'))

    # 将传感器编号左填补为001，002
    person_files_str_nums = [str(num).zfill(3) for num in person_files_nums]
    vehicle_files_str_nums = [str(num).zfill(3) for num in vehicle_files_nums]
    person_files_str_nums = [str(num).zfill(3) for num in person_files_nums]
    vehicle_files_str_nums = [str(num).zfill(3) for num in vehicle_files_nums]

    # 获取传感器序列号2023001，2023002
    person_sensors_label = ['2023' + str(num1) for num1 in person_files_str_nums]
    vehicle_sensors_label = ['2023' + str(num2) for num2 in vehicle_files_str_nums]

    person_sensors_df = pd.DataFrame({'labels': person_files_str_nums, 'time': person_files_time})
    vehicle_sensors_df = pd.DataFrame({'labels': vehicle_files_str_nums, 'time': vehicle_files_time})
    # 将日期时间列解析为 Pandas 中的日期时间格式
    person_sensors_df['time'] = pd.to_datetime(person_sensors_df['time'], format='%Y-%m-%d %H:%M:%S')
    vehicle_sensors_df['time'] = pd.to_datetime(vehicle_sensors_df['time'], format='%Y-%m-%d %H:%M:%S')

    # 对 DataFrame 进行日期时间排序
    person_sorted_df = person_sensors_df.sort_values(by='time', ascending=False).reset_index(drop=True)
    vehicle_sorted_df = vehicle_sensors_df.sort_values(by='time', ascending=False).reset_index(drop=True)


    signal_label = ["人员信号", "车辆信号"]


    # MAGE_EMOJI_URL = "streamlitBKN.png"
    # st.set_page_config(page_title='环境传感器目标识别平台', page_icon=MAGE_EMOJI_URL, initial_sidebar_state='collapsed',
    #                    layout="wide")

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

    st.markdown(
        """
        <style>
        .column-color {
            background-color: red;
            padding: 1rem;
            border-radius: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


    colmns0 = st.columns(3, gap="large")

    # st.container()
    # page_button = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    # if page_button:
    #     option = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    #     st.write('你选择了：', option)

    with colmns0[1]:
        # st.session_state.parameters = {}
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold">目标识别数据库</p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        st.markdown('###')
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">声频信号数据库</p></nobr>', unsafe_allow_html=True)
        selected_dB_type = colmns0[1].multiselect('选择识别类别：', signal_label, signal_label, key='dB')  # ["人员信号", "车辆信号"]
        if len(selected_dB_type) != 0:
            if len(selected_dB_type) == 2:
                merge_sensors_label = person_sensors_label + vehicle_sensors_label
                multi_line_str2 = "\n".join(merge_sensors_label)
            elif len(selected_dB_type) == 1:
                if '人员信号' in selected_dB_type:
                    merge_sensors_label = person_sensors_label
                    multi_line_str2 = "\n".join(merge_sensors_label)
                else:
                    merge_sensors_label = vehicle_sensors_label
                    multi_line_str2 = "\n".join(merge_sensors_label)
            txt_node = st.text_area(label="声频信号数据库", value=multi_line_str2, height=200, label_visibility='collapsed')

            colmns0_3 = colmns0[1].columns([1, 3], gap="small")
            selected_dB_sensor = colmns0_3[0].selectbox('   声频信号节点：', merge_sensors_label)
            db_uploaded_file = colmns0_3[1].file_uploader("添加文件:", type=["csv", "txt"], key="db_upload_file")
            db_delete_button = colmns0_3[0].button("删除数据", key="db_delete_file")


            # 获取选择的信号节点文件路径
            read_files_name = 'sensor_' + str(int(selected_dB_sensor[4:])) + '_gps.txt'
            person_file_path = os.path.join(directory_person, read_files_name)
            vehicle_file_path = os.path.join(directory_vehicle, read_files_name)

            if os.path.exists(person_file_path):
                read_file_df = pd.read_csv(person_file_path, sep=',', header=None)
                final_file_df = read_files_split(read_file_df)
                # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)
            else:
                read_file_df = pd.read_csv(vehicle_file_path, sep=',', header=None)
                final_file_df = read_files_split(read_file_df)
                # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

            # 创建声频散点图
            trace2 = go.Scatter(
                x=final_file_df['Frame'],
                y=final_file_df['Audio'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='dB'
            )

            layout = go.Layout(
                width=300,
                height=280,
            )

            fig2 = go.Figure(data=[trace2], layout=layout)
            fig2.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                xaxis_title='时间 - [秒]',
                yaxis_title='声频信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.25,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(
                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=8,
                    showticklabels=True,
                ),
            )
            colmns0[1].plotly_chart(fig2, use_container_width=True)

        else:
            colmns0[1].error("请选择需要绘制的信号类型！")
            txt_node = st.text_area(label="声频信号数据库", value='无', height=200, label_visibility='collapsed', key='dB_txt')


        # colmns0_1 = colmns0[1].columns(2, gap="large")


    with colmns0[0]:
        timestr = time.strftime('%Y-%m-%d %H:%M:%S')
        st.metric(label='时间', value=timestr, label_visibility='collapsed') # visible hidden collapsed
        # st.markdown('###')
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        # st.markdown('###')
        st.markdown('###')
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">振动信号数据库</p></nobr>', unsafe_allow_html=True)
        selected_Acc_type = colmns0[0].multiselect('选择识别类别：', signal_label, signal_label, key='Acc')  # ["人员信号", "车辆信号"]
        if len(selected_Acc_type) != 0:
            if len(selected_Acc_type) == 2:
                merge_sensors_label = person_sensors_label + vehicle_sensors_label
                multi_line_str = "\n".join(merge_sensors_label)
            elif len(selected_Acc_type) == 1:
                if '人员信号' in selected_Acc_type:
                    merge_sensors_label = person_sensors_label
                    multi_line_str = "\n".join(merge_sensors_label)
                else:
                    merge_sensors_label = vehicle_sensors_label
                    multi_line_str = "\n".join(merge_sensors_label)
            txt_node = st.text_area(label="振动信号数据库", value=multi_line_str, height=200, label_visibility='collapsed')

            colmns0_1 = colmns0[0].columns([1,3], gap="small")
            selected_Acc_sensor = colmns0_1[0].selectbox('振动信号节点：', merge_sensors_label)
            Acc_uploaded_file = colmns0_1[1].file_uploader("添加文件:", type=["csv", "txt"], key="Acc_upload_file")
            Acc_delete_button = colmns0_1[0].button("删除数据", key="Acc_delete_file")

            # 获取选择的信号节点文件路径
            read_files_name = 'sensor_' + str(int(selected_Acc_sensor[4:])) + '_gps.txt'
            person_file_path = os.path.join(directory_person, read_files_name)
            vehicle_file_path = os.path.join(directory_vehicle, read_files_name)

            if os.path.exists(person_file_path):
                read_file_df = pd.read_csv(person_file_path, sep=',', header=None)
                final_file_df = read_files_split(read_file_df)
                # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

            else:
                read_file_df = pd.read_csv(vehicle_file_path, sep=',', header=None)
                final_file_df = read_files_split(read_file_df)
                # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

            # 创建X,Y,Z轴加速度散点图
            trace1_1 = go.Scatter(
                x=final_file_df['Frame'],
                y=final_file_df['X_Accel'],
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='X_Accel'
            )

            trace1_2 = go.Scatter(
                x=final_file_df['Frame'],
                y=final_file_df['Y_Accel'],
                mode='lines',
                marker=dict(
                    color='blue',
                    size=10,
                    line=dict(
                        color='blue',
                        width=1
                    )
                ),
                name='Y_Accel'
            )

            trace1_3 = go.Scatter(
                x=final_file_df['Frame'],
                y=final_file_df['Z_Accel'].apply(lambda x: x * -1),
                mode='lines',
                marker=dict(
                    color='red',
                    size=10,
                    line=dict(
                        color='red',
                        width=1
                    )
                ),
                name='Z_Accel'
            )

            layout = go.Layout(
                width=300,
                height=280,
            )

            # 将两个散点图放在同一个坐标系中
            fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
            fig1.update_layout(
                margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
                # title="",
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                xaxis_title='时间 - [秒]',
                yaxis_title='振动信号',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    # yanchor="bottom",
                    y=1.25,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),
                yaxis=dict(

                    showline=True,
                    showgrid=True,
                    mirror=True,
                    nticks=11,
                    showticklabels=True,
                ),
            )

            colmns0[0].plotly_chart(fig1, use_container_width=True)

        else:
            colmns0[0].error("请选择需要绘制的信号类型！")
            txt_node = st.text_area(label="振动信号数据库", value='无', height=200, label_visibility='collapsed', key='Acc_txt')

    with colmns0[2]:
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; '
                    'font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        st.markdown('###')
        # st.markdown('###')
        st.markdown('###')
        st.markdown('###')
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">磁场信号数据库</p></nobr>', unsafe_allow_html=True)
        selected_Mag_type = colmns0[2].multiselect('选择识别类别：', signal_label, signal_label, key='Mag')  # ["人员信号", "车辆信号"]
        if len(selected_Mag_type) != 0:
            if len(selected_Mag_type) == 2:
                merge_sensors_label = person_sensors_label + vehicle_sensors_label
                multi_line_str3 = "\n".join(merge_sensors_label)
            elif len(selected_Mag_type) == 1:
                if '人员信号' in selected_Mag_type:
                    merge_sensors_label = person_sensors_label
                    multi_line_str3 = "\n".join(merge_sensors_label)
                else:
                    merge_sensors_label = vehicle_sensors_label
                    multi_line_str3 = "\n".join(merge_sensors_label)
            txt_signal = st.text_area(label="磁场信号数据库", value=multi_line_str3, height=200, label_visibility='collapsed')
            colmns0_2 = colmns0[2].columns([1, 3], gap="small")
            selected_Mag_sensor = colmns0_2[0].selectbox('磁场信号节点：', merge_sensors_label)
            Mag_uploaded_file = colmns0_2[1].file_uploader("添加文件:", type=["csv", "txt"], key="Mag_upload_file")
            Mag_delete_button = colmns0_2[0].button("删除数据", key="Mag_delete_file")



            # 获取选择的信号节点文件路径
            read_files_name = 'sensor_' + str(int(selected_Mag_sensor[4:])) + '_gps.txt'
            person_file_path = os.path.join(directory_person, read_files_name)
            vehicle_file_path = os.path.join(directory_vehicle, read_files_name)

            if os.path.exists(person_file_path):
                read_file_df = pd.read_csv(person_file_path, sep=',', header=None)
                final_file_df = read_files_split(read_file_df)
                # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)
            else:
                read_file_df = pd.read_csv(vehicle_file_path, sep=',', header=None)
                final_file_df = read_files_split(read_file_df)
                # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

            # 创建X,Y,Z轴磁场散点图
            trace3_1 = go.Scatter(
                x=final_file_df['Frame'],
                y=final_file_df['X_Mag'].apply(lambda x: x * -1),
                mode='lines',
                marker=dict(
                    color='black',
                    size=10,
                    line=dict(
                        color='black',
                        width=1
                    )
                ),
                name='X_Mag'
            )
            trace3_2 = go.Scatter(
                x=final_file_df['Frame'],
                y=final_file_df['Y_Mag'].apply(lambda x: x * -1),
                mode='lines',
                marker=dict(
                    color='blue',
                    size=10,
                    line=dict(
                        color='blue',
                        width=1
                    )
                ),
                name='Y_Mag'
            )
            trace3_3 = go.Scatter(
                x=final_file_df['Frame'],
                y=final_file_df['Z_Mag'],
                mode='lines',
                marker=dict(
                    color='red',
                    size=10,
                    line=dict(
                        color='red',
                        width=1
                    )
                ),
                name='Z_Mag'
            )

            layout = go.Layout(
                width=300,
                height=280,
            )

            fig3 = make_subplots(specs=[[{"secondary_y": True}]])
            fig3.add_trace(trace3_1, secondary_y=False)
            fig3.add_trace(trace3_2, secondary_y=False)
            fig3.add_trace(trace3_3, secondary_y=True)
            fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
            fig3.update_yaxes(title_text="Z轴磁场信号",
                              showline=True,
                              showgrid=True,
                              mirror=True,
                              nticks=11,
                              showticklabels=True,
                              secondary_y=True)
            fig3.update_layout(
                # title="",
                width=300,
                height=280,
                margin=dict(l=0, r=10, t=20, b=0),
                xaxis_gridcolor="lightgray",
                yaxis_gridcolor="lightgray",
                xaxis_title='时间 - [秒]',
                # yaxis_title='质量累计含量R(x) - [%]',
                showlegend=True,
                legend=dict(
                    font=dict(size=12),
                    orientation="h",
                    # yanchor="bottom",
                    y=1.25,
                    # xanchor="right",
                    x=0
                ),
                xaxis=dict(
                    showline=True,
                    showgrid=True,
                    showticklabels=True,
                    mirror=True,
                    # nticks=21,
                ),

            )
            colmns0[2].plotly_chart(fig3, use_container_width=True)

        else:
            colmns0[2].error("请选择需要绘制的信号类型！")
            txt_node = st.text_area(label="磁场信号数据库", value='无', height=200, label_visibility='collapsed', key='Mag_txt')


    st.markdown("------")

    st.markdown("""<style>.css-16idsys p
    {
    word-break: break-word;
    margin-bottom: 10px;
    font-size: 15px;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('###')

def app3():
    st.sidebar.success("已选择：📈  感知历史数据库")
    directory = "./sensor_files/"

    # 获取目录下的所有文件名，并按照数字序号排序
    files_name = sorted(os.listdir(directory), key=sort_by_number)
    files_nums = []
    files_time = []

    # 定义匹配数字序号的正则表达式
    pattern = r'\d+'

    # 循环处理每个文件
    for filename in files_name:
        # 仅处理.txt文件
        if filename.endswith('.txt'):
            # 提取数字序号
            files_nums.append(re.findall(pattern, filename)[0])
            # 打开文件并读取第一行内容
            with open(directory + filename, 'r') as f:
                first_line = f.readline()
                start_index = first_line.find("T:") + 2
                end_index = first_line.find("N:")
                time_str = first_line[start_index:end_index]
                files_time.append(datetime.datetime.utcfromtimestamp(float(time_str)
                                                                     + 1682395190).strftime('%Y-%m-%d %H:%M:%S'))
            # 提取T和N之间的数字
            # t_value = re.findall(r'T:(\d+\.\d+)', first_line)[0]
            # n_value = re.findall(r'N:(\d+\.\d+)', first_line)[0]
            # 输出结果
            # print(f'File {filename} has number {number}, Time value {time_str}')
    # 将传感器编号左填补为001，002
    files_str_nums = [str(num).zfill(3) for num in files_nums]
    # 获取传感器序列号2023001，2023002
    sensors_label = ['2023' + str(num1) for num1 in files_str_nums]
    curr_status = []
    curr_power = []
    for labels in range(len(sensors_label)):
        curr_status.append('通信正常')
        curr_power.append('正常')
    sensors_label_df = pd.DataFrame({'节点序列号': sensors_label, '当前状态': curr_status, '电量': curr_power})

    sensors_df = pd.DataFrame({'labels': files_str_nums, 'time': files_time})
    # 将日期时间列解析为 Pandas 中的日期时间格式
    sensors_df['time'] = pd.to_datetime(sensors_df['time'], format='%Y-%m-%d %H:%M:%S')

    # 对 DataFrame 进行日期时间排序
    sorted_df = sensors_df.sort_values(by='time', ascending=False).reset_index(drop=True)

    txt_name_time = []
    for name_index in range(len(sorted_df['time'])):
        txt_name_time.append("●  节点2023" + sorted_df['labels'][name_index] + "于" + str(sorted_df['time'][name_index]) + "识别到振动信号")
    txt_name_time_df = pd.DataFrame({'txt': txt_name_time})



    # MAGE_EMOJI_URL = "streamlitBKN.png"
    # st.set_page_config(page_title='环境传感器目标识别平台', page_icon=MAGE_EMOJI_URL, initial_sidebar_state='collapsed',
    #                    layout="wide")

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

    st.markdown(
        """
        <style>
        .column-color {
            background-color: red;
            padding: 1rem;
            border-radius: 0.25rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


    colmns0 = st.columns(3, gap="large")

    # st.container()
    # page_button = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    # if page_button:
    #     option = st.sidebar.selectbox('请选择', ['选项1', '选项2', '选项3'])
    #     st.write('你选择了：', option)

    with colmns0[1]:
        # st.session_state.parameters = {}
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold">感知历史数据库</p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        # st.markdown('###')

        multi_line_str = "\n".join(sensors_label)
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">环境感知节点</p></nobr>', unsafe_allow_html=True)
        txt_node = st.text_area(label="环境感知节点", value=multi_line_str, height=200, label_visibility='collapsed')
        selected_node = st.selectbox('选择节点：', sensors_label)

    with colmns0[0]:
        timestr = time.strftime('%Y-%m-%d %H:%M:%S')
        st.metric(label='时间', value=timestr, label_visibility='collapsed') # visible hidden collapsed
        # st.markdown('###')
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        # st.markdown('###')
        # st.markdown('###')
        tempt_date = sorted_df['time'].dt.strftime('%Y-%m-%d').tolist()
        multi_line_str2 = "\n".join(tempt_date)
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">环境感知日期</p></nobr>', unsafe_allow_html=True)
        txt_date = st.text_area(label="环境感知日期", value=multi_line_str2, height=200, label_visibility='collapsed')
        # st.markdown('###')
        # st.markdown('###')
        selected_date = st.date_input('选择日期：', value=datetime.date(2023, 5, 1), min_value=datetime.date(2023, 1, 1),
                                      max_value=datetime.datetime.now()) # , key='date_filter'
    with colmns0[2]:

        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        st.markdown('<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 32px; font-weight: bold"></p></nobr>', unsafe_allow_html=True)
        # st.markdown('###')
        # st.markdown('###')

        st.markdown('###')
        st.markdown('###')
        # st.markdown('###')
        signal_label = ["振动信号", "声频信号", "磁场信号"]
        multi_line_str3 = "\n".join(signal_label)
        st.markdown('<nobr><p style="font-size: 18px;font-weight: bold">环境感知数据</p></nobr>', unsafe_allow_html=True)
        txt_signal = st.text_area(label="环境感知数据", value=multi_line_str3, height=200, label_visibility='collapsed')
        selected_signal = st.multiselect('选择信号：', signal_label, signal_label)

    read_files_name = 'sensor_' + str(int(selected_node[4:])) + '_gps.txt'
    # st.markdown(read_files_name)
    # 读取文本文件
    read_file_df = pd.read_csv('./sensor_files/'
                               + read_files_name, sep=',', header=None)
    final_file_df = read_files_split(read_file_df)
    # final_file_df['Audio'] = final_file_df['Audio'].apply(lambda x: x / 100)

    # 创建X,Y,Z轴加速度散点图
    trace1_1 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['X_Accel'],
        mode='lines',
        marker=dict(
            color='black',
            size=10,
            line=dict(
                color='black',
                width=1
            )
        ),
        name='X_Accel'
    )

    trace1_2 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Y_Accel'],
        mode='lines',
        marker=dict(
            color='blue',
            size=10,
            line=dict(
                color='blue',
                width=1
            )
        ),
        name='Y_Accel'
    )

    trace1_3 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Z_Accel'].apply(lambda x: x * -1),
        mode='lines',
        marker=dict(
            color='red',
            size=10,
            line=dict(
                color='red',
                width=1
            )
        ),
        name='Z_Accel'
    )

    # 创建声频散点图
    trace2 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Audio'],
        mode='lines',
        marker=dict(
            color='black',
            size=10,
            line=dict(
                color='black',
                width=1
            )
        ),
        name='dB'
    )

    # 创建X,Y,Z轴磁场散点图
    trace3_1 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['X_Mag'].apply(lambda x: x * -1),
        mode='lines',
        marker=dict(
            color='black',
            size=10,
            line=dict(
                color='black',
                width=1
            )
        ),
        name='X_Mag'
    )
    trace3_2 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Y_Mag'].apply(lambda x: x * -1),
        mode='lines',
        marker=dict(
            color='blue',
            size=10,
            line=dict(
                color='blue',
                width=1
            )
        ),
        name='Y_Mag'
    )
    trace3_3 = go.Scatter(
        x=final_file_df['Frame'],
        y=final_file_df['Z_Mag'],
        mode='lines',
        marker=dict(
            color='red',
            size=10,
            line=dict(
                color='red',
                width=1
            )
        ),
        name='Z_Mag'
    )

    layout = go.Layout(
        width=300,
        height=280,
    )

    # 将两个散点图放在同一个坐标系中
    fig1 = go.Figure(data=[trace1_1, trace1_2, trace1_3], layout=layout)
    fig2 = go.Figure(data=[trace2], layout=layout)

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(trace3_1, secondary_y=False)
    fig3.add_trace(trace3_2, secondary_y=False)
    fig3.add_trace(trace3_3, secondary_y=True)

    fig1.update_layout(
        margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
        # title="",
        xaxis_gridcolor="lightgray",
        yaxis_gridcolor="lightgray",
        xaxis_title='时间 - [秒]',
        yaxis_title='振动信号',
        showlegend=True,
        legend=dict(
            orientation="h",
            # yanchor="bottom",
            y=1.25,
            # xanchor="right",
            x=0
        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            mirror=True,
            # nticks=21,
        ),
        yaxis=dict(

            showline=True,
            showgrid=True,
            mirror=True,
            nticks=11,
            showticklabels=True,
        ),
    )
    fig2.update_layout(
        margin=dict(l=0, r=10, t=20, b=0),  # margin=dict(l=5, r=5, t=5, b=5)
        # title="",
        xaxis_gridcolor="lightgray",
        yaxis_gridcolor="lightgray",
        xaxis_title='时间 - [秒]',
        yaxis_title='声频信号',
        showlegend=True,
        legend=dict(
            orientation="h",
            # yanchor="bottom",
            y=1.25,
            # xanchor="right",
            x=0
        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            mirror=True,
            # nticks=21,
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            mirror=True,
            nticks=8,
            showticklabels=True,
        ),
    )

    fig3.update_yaxes(title_text="X,Y轴磁场信号", nticks=11, secondary_y=False)
    fig3.update_yaxes(title_text="Z轴磁场信号",
                      showline=True,
                      showgrid=True,
                      mirror=True,
                      nticks=11,
                      showticklabels=True,
                      secondary_y=True)
    fig3.update_layout(
        # title="",
        width=300,
        height=280,
        margin=dict(l=0, r=10, t=20, b=0),
        xaxis_gridcolor="lightgray",
        yaxis_gridcolor="lightgray",
        xaxis_title='时间 - [秒]',
        # yaxis_title='质量累计含量R(x) - [%]',
        showlegend=True,
        legend=dict(
            font=dict(size=12),
            orientation="h",
            # yanchor="bottom",
            y=1.25,
            # xanchor="right",
            x=0
        ),
        xaxis=dict(
            showline=True,
            showgrid=True,
            showticklabels=True,
            mirror=True,
            # nticks=21,
        ),

    )

    if len(selected_signal) != 0:
        if len(selected_signal) == 3:
            colmns1 = st.columns(3, gap="large")
            colmns1[0].plotly_chart(fig1, use_container_width=True)
            colmns1[1].plotly_chart(fig2, use_container_width=True)
            colmns1[2].plotly_chart(fig3, use_container_width=True)
        elif len(selected_signal) == 2:
            colmns1 = st.columns(2, gap="large")
            if "振动信号" in selected_signal:
                colmns1[0].plotly_chart(fig1, use_container_width=True)
                if "声频信号" in selected_signal:
                    colmns1[1].plotly_chart(fig2, use_container_width=True)
                else:
                    colmns1[1].plotly_chart(fig3, use_container_width=True)
            else:
                colmns1[0].plotly_chart(fig2, use_container_width=True)
                colmns1[1].plotly_chart(fig3, use_container_width=True)
        elif len(selected_signal) == 1:
            if "振动信号" in selected_signal:
                st.plotly_chart(fig1, use_container_width=True)
            elif "声频信号" in selected_signal:
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.plotly_chart(fig3, use_container_width=True)
    else:
        colmns1 = st.columns(3, gap="large")
        layout = go.Layout(
            width=300,
            height=280,
        )
        layout1 = go.Layout(
            width=300,
            height=280,
        )
        # 将两个散点图放在同一个坐标系中
        fig1 = go.Figure(data=[], layout=layout)
        fig2 = go.Figure(data=[], layout=layout)
        fig3 = go.Figure(data=[], layout=layout1)

        fig1.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='振动信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig2.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='声频信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )
        fig3.update_layout(
            margin=dict(l=0,r=10,t=20,b=0), # margin=dict(l=5, r=5, t=5, b=5)
            # title="",
            xaxis_gridcolor="lightgray",
            yaxis_gridcolor="lightgray",
            xaxis_title='时间 - [秒]',
            yaxis_title='磁场信号',
            showlegend=True,
            legend=dict(
                orientation="h",
                # yanchor="bottom",
                y=1.5,
                # xanchor="right",
                x=0
            ),
            xaxis=dict(
                showline=True,
                showgrid=True,
                showticklabels=True,
                mirror=True,
                # nticks=21,
            ),
            yaxis=dict(

                showline=True,
                showgrid=True,
                mirror=True,
                nticks=11,
                showticklabels=True,
            ),
        )


        colmns1[0].plotly_chart(fig1, use_container_width=True)
        colmns1[1].plotly_chart(fig2, use_container_width=True)
        colmns1[2].plotly_chart(fig3, use_container_width=True)
        colmns0[2].error("请选择需要绘制的信号类型！")

    st.markdown("------")
    st.markdown("""<style>.css-16idsys p
    {
    word-break: break-word;
    margin-bottom: 10px;
    font-size: 18px;
    }
    </style>""", unsafe_allow_html=True)

    st.markdown('###')




st.set_page_config(page_title='环境传感器目标识别平台', page_icon="streamlitBKN.png", initial_sidebar_state='collapsed',
                   layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

page_names_to_funcs = {
    "🌍  主监测页面": app1,
    "📊  目标识别数据库": app2,
    "📈  感知历史数据库": app3
}
st.sidebar.markdown(
    '<nobr><p style="text-align: center;font-family:sans serif; color:Black; font-size: 20px; font-weight: bold">环境传感器目标识别平台</p></nobr>',
    unsafe_allow_html=True)
# st.sidebar.markdown("###")
st.sidebar.markdown(
    '<nobr><p style="font-family:sans serif; color:Black; font-size: 15px; font-weight: bold">选择页面：</p></nobr>',
    unsafe_allow_html=True)
demo_name = st.sidebar.selectbox("选择页面", page_names_to_funcs.keys(), label_visibility='collapsed')
page_names_to_funcs[demo_name]()
