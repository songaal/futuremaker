import pandas as pd
import plotly.offline as offline
import plotly.graph_objs as go

# jupyter notebook 에서 출력
offline.init_notebook_mode(connected=True)
df = pd.read_csv('bitfinex/90d.csv')
trace = go.Candlestick(x=df.MTS,
                       open=df.Open,
                       high=df.High,
                       low=df.Low,
                       close=df.Close)
data = [trace]

layout = go.Layout(title='비트코인 캔들차트')
fig = go.Figure(data=data, layout=layout)
offline.iplot(fig, filename="candlestick")
