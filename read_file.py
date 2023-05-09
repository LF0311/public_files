import pandas as pd
import streamlit as st
import os

txt_name_time_df = pd.read_csv('./sensor_files/sensor_1_gps.txt', sep=',', header=None)
directory = './sensor_files/'
a = os.listdir(directory)
st.dataframe(txt_name_time_df, height=650)
st.markdown(a)

