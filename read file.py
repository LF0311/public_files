import pandas as pd

k = pd.read_csv('./sensor_files/sensor_1_gps.txt', sep=',', header=None)
print(k)
