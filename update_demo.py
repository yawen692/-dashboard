"""追加下一月模拟数据。重复执行会继续推进一月，不请求真实 API。"""
from datetime import datetime, timezone
import json
import logging
import pandas as pd
from model import DATA, ROOT, generate, validate

def update(reset=False):
    DATA.parent.mkdir(exist_ok=True)
    if reset or not DATA.exists():
        df=generate()
    else:
        df=validate(pd.read_csv(DATA))
        next_month=(pd.Period(df.period.max(),freq='M')+1).strftime('%Y-%m')
        df=pd.concat([df,generate(next_month,next_month)],ignore_index=True)
    df=validate(df)
    tmp=DATA.with_suffix('.tmp'); df.to_csv(tmp,index=False); tmp.replace(DATA)
    (ROOT/'data'/'metadata.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(),'latest_period':df.period.max(),'source':'模拟数据'},ensure_ascii=False),encoding='utf-8')
    logging.info('保存 %s 行；最新月份 %s',len(df),df.period.max())
    return df
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument('--reset',action='store_true'); args=parser.parse_args()
    logging.basicConfig(level=logging.INFO); update(args.reset)
