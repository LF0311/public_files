import pandas as pd
import streamlit as st

txt_name_time_df = pd.read_csv('./sensor_files/sensor_1_gps.txt', sep=',', header=None)
st.dataframe(txt_name_time_df, height=650)
