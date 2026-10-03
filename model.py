from pathlib import Path
import math
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'trade_panel.csv'
COUNTRIES = [('美国','USA','北美'),('德国','DEU','欧洲'),('荷兰','NLD','欧洲'),('英国','GBR','欧洲'),('日本','JPN','亚洲'),('韩国','KOR','亚洲'),('越南','VNM','亚洲'),('泰国','THA','亚洲'),('巴西','BRA','拉美'),('墨西哥','MEX','拉美'),('澳大利亚','AUS','大洋洲'),('沙特阿拉伯','SAU','中东')]
PRODUCTS = ['电动载人汽车','锂离子蓄电池','太阳能电池']

def generate(start='2023-01', end='2025-12'):
    rows=[]
    for date in pd.date_range(start,end,freq='MS'):
        t=(date.year-2023)*12+date.month-1
        for p,product in enumerate(PRODUCTS):
            for j,(country,iso,region) in enumerate(COUNTRIES):
                base=[190,280,150][p]*(1+((j*7+p*3)%11)/8)/(1+j/5)
                growth=[.012,.007,.004][p]+(j-5)*.0012
                season=1+.12*math.sin(date.month*math.pi/6+p)+.04*math.cos(t+j)
                value=round(base*math.exp(growth*t)*season*1_000_000,2)
                rows.append([date.strftime('%Y-%m'),product,country,iso,region,value])
    return pd.DataFrame(rows,columns=['period','product_group','partner_name','iso3','region','trade_value_usd'])

def validate(df):
    required=['period','product_group','partner_name','iso3','region','trade_value_usd']
    if not set(required)<=set(df.columns):
        raise ValueError('缺少字段：'+','.join(set(required)-set(df.columns)))
    df=df[required].copy()
    if df.isna().any().any(): raise ValueError('数据存在空值')
    if not df.period.astype(str).str.fullmatch(r'\d{4}-\d{2}').all(): raise ValueError('period 必须为 YYYY-MM')
    pd.to_datetime(df.period,format='%Y-%m',errors='raise')
    df.trade_value_usd=pd.to_numeric(df.trade_value_usd,errors='raise')
    if not df.trade_value_usd.map(math.isfinite).all() or (df.trade_value_usd<0).any(): raise ValueError('出口额必须为有限非负数')
    if df.duplicated(['period','product_group','iso3']).any(): raise ValueError('月份—产品—国家存在重复记录')
    return df

def indicators(df):
    rows=[]
    for period,g in df.groupby('period'):
        market=g.groupby('partner_name').trade_value_usd.sum().sort_values(ascending=False)
        total=market.sum(); share=market/total if total else market*0
        hhi=float((share**2).sum())
        rows.append(dict(period=period,total=total,hhi=hhi,cr5=float(share.head(5).sum()),effective=1/hhi if hhi else float('nan')))
    out=pd.DataFrame(rows).sort_values('period')
    dates=pd.to_datetime(out.period)
    totals=pd.Series(out.total.to_numpy(),index=dates)
    prev=totals.reindex(dates-pd.DateOffset(years=1)).to_numpy()
    out['yoy']=(out.total.to_numpy()/prev-1)*100
    return out
