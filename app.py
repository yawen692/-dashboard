import json
import pandas as pd
import plotly.express as px
import streamlit as st
from model import DATA, ROOT, PRODUCTS, validate, indicators
from update_demo import update

st.set_page_config(page_title='新三样 · 出口监测',page_icon='📊',layout='wide')
st.markdown('''<style>.block-container{padding-top:2rem}h1{letter-spacing:-1px}[data-testid="stMetric"]{background:#eef4fc;padding:18px;border-radius:12px;border-top:3px solid #2563eb}div[data-testid="stSidebar"]{background:#f1f5fa}</style>''',unsafe_allow_html=True)
st.title('新三样 · 出口市场监测')
st.caption('教学示例 / 所有数值均为模拟数据，不代表实际贸易情况')
if not DATA.exists(): update(reset=True)
with st.sidebar:
    st.header('监测范围')
    uploaded=st.file_uploader('读取标准格式 CSV',type='csv',help='只在当前页面使用，不覆盖示例文件')
try:
    df=validate(pd.read_csv(uploaded if uploaded is not None else DATA))
except Exception as exc:
    st.error(f'数据无法读取：{exc}'); st.stop()
with st.sidebar:
    product=st.selectbox('产品',['全部产品']+sorted(df.product_group.unique().tolist()))
    region=st.selectbox('地区',['全球']+sorted(df.region.unique().tolist()))
    months=sorted(df.period.unique())
    month=st.select_slider('观察月份',options=months,value=months[-1])
    st.divider()
    if uploaded is None and st.button('演示更新：追加一个月',width='stretch'):
        update(); st.rerun()
    if st.button('重新读取数据',width='stretch'): st.rerun()
    st.caption('追加按钮生成模拟数据；真实监测需另接 API。')
    st.caption('CSV 按月读取；更新文件后重新读取即可刷新结果。')
f=df.copy()
if product!='全部产品': f=f[f.product_group==product]
if region!='全球': f=f[f.region==region]
if f.empty: st.warning('该产品在所选地区没有数据。'); st.stop()
st.caption(f'最新数据期：{df.period.max()}  ·  当前观察期：{month}  ·  {product} / {region}')
series=indicators(f)
current=series[series.period==month]
if current.empty: st.warning('当前月份没有数据，请选择其他月份。'); st.stop()
r=current.iloc[0]
a,b,c,d=st.columns(4)
a.metric('当月出口额',f'{r.total/1e8:.2f} 亿美元',None if pd.isna(r.yoy) else f'{r.yoy:+.1f}% 同比')
b.metric('HHI',f'{r.hhi:.4f}')
c.metric('CR5',f'{r.cr5:.1%}')
d.metric('有效市场数',f'{r.effective:.1f}')
st.caption('全球模式以示例12个目的地的合计为分母；地区筛选后，以地区内出口额为分母重新计算指标。')
tabs=st.tabs(['出口总览','全球市场','多元化','市场变化','数据与口径'])
def chart(fig):
    fig.update_layout(template='plotly_white',font=dict(family='Arial, sans-serif',size=14),margin=dict(l=15,r=15,t=35,b=15),colorway=['#2563eb','#06b6d4','#f59e0b','#8b5cf6'])
    st.plotly_chart(fig,width='stretch')
with tabs[0]:
    history=series[series.period<=month].copy(); history['出口额（亿美元）']=history.total/1e8
    chart(px.line(history,x='period',y='出口额（亿美元）',title='月度出口趋势',markers=True))
    g=f[f.period<=month].groupby(['period','product_group'],as_index=False).trade_value_usd.sum(); g['亿美元']=g.trade_value_usd/1e8
    chart(px.area(g,x='period',y='亿美元',color='product_group',title='产品结构'))
with tabs[1]:
    markets=f[f.period==month].groupby(['partner_name','iso3','region'],as_index=False).trade_value_usd.sum().sort_values('trade_value_usd',ascending=False)
    markets['份额']=markets.trade_value_usd/markets.trade_value_usd.sum(); markets['亿美元']=markets.trade_value_usd/1e8
    chart(px.choropleth(markets,locations='iso3',color='亿美元',hover_name='partner_name',hover_data={'份额':':.1%'},color_continuous_scale='Blues',projection='natural earth',title='出口目的地 · 世界地图'))
    left,right=st.columns([1.4,1])
    with left: chart(px.bar(markets.head(10).sort_values('trade_value_usd'),x='亿美元',y='partner_name',orientation='h',title='Top 10 目的地'))
    with right: chart(px.pie(markets,names='region',values='trade_value_usd',hole=.65,title='地区构成'))
with tabs[2]:
    chart(px.line(series[series.period<=month],x='period',y='hhi',title='HHI · 越低表示市场越分散'))
    chart(px.line(series[series.period<=month],x='period',y='cr5',title='CR5 · 前五大目的地的份额'))
    st.info('HHI = Σ市场份额²；CR5 = 前五大市场份额之和；有效市场数 = 1/HHI。指标刻画市场结构，不直接等同于出口风险。')
with tabs[3]:
    prior=(pd.Period(month,freq='M')-12).strftime('%Y-%m')
    now=f[f.period==month].groupby('partner_name').trade_value_usd.sum()
    before=f[f.period==prior].groupby('partner_name').trade_value_usd.sum()
    if before.empty: st.info('尚无去年同月数据，无法计算市场份额同比变化。')
    elif now.sum()==0 or before.sum()==0: st.info('出口合计为零，无法计算市场份额变化。')
    else:
        change=pd.concat([now.rename('当期出口额'),before.rename('去年同期出口额')],axis=1).fillna(0)
        change['份额变化（百分点）']=(change['当期出口额']/now.sum()-change['去年同期出口额']/before.sum())*100
        change['当期份额']=change['当期出口额']/now.sum()*100
        change['亿美元']=change['当期出口额']/1e8
        chart(px.scatter(change.reset_index(),x='当期份额',y='份额变化（百分点）',size='亿美元',hover_name='partner_name',title='市场份额与同比变化',size_max=55))
        threshold=st.slider('份额变化提醒阈值（百分点）',.1,5.,.5,.1)
        alerts=change[change['份额变化（百分点）'].abs()>=threshold]
        if alerts.empty: st.success('所选阈值下无提醒。')
        else: st.dataframe(alerts.sort_values('份额变化（百分点）'),width='stretch')
        st.caption('提醒仅指出变化，不认定政策影响或因果关系。')
with tabs[4]:
    st.markdown('**示例口径**：2023年1月—2025年12月，三类产品，12个模拟目的地；更新演示可延长时间范围。所有金额使用美元。')
    if uploaded is None:
        meta=json.loads((ROOT/'data'/'metadata.json').read_text(encoding='utf-8'))
        st.caption('文件更新时间（UTC）：'+meta['updated_at'])
    st.markdown('**接入自己的数据**：保留下表六列；每个“月份—产品—国家”一行。国家使用 ISO3 代码。先将 HS 明细按产品汇总，再接入页面。')
    st.dataframe(df.head(24),width='stretch')
    st.download_button('下载当前筛选数据 CSV',f.to_csv(index=False).encode('utf-8-sig'),file_name='filtered_trade.csv',mime='text/csv')
    st.markdown('真实数据接入时须检查月份完整性、数据修订、产品口径以及世界合计与双边明细重复；页面不会将缺失月份当作零。')
