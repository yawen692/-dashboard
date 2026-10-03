# 中国“新三样”出口市场监测 — Streamlit 教学示例

所有数据为模拟数据，不是中国真实贸易数据。无需 API key 即可体验。

## 本地运行（推荐 Python 3.11）
解压后在本目录打开 Anaconda Prompt / 终端，执行：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

浏览器通常打开 http://localhost:8501 。保持终端运行。停止服务按 Ctrl+C。
Windows 安装好依赖后可双击 start_windows.bat；如 python 未配置到 PATH，建议使用 Anaconda Prompt。
不要在 Spyder 编辑器中直接点击 app.py 的运行按钮，Streamlit 需通过上述命令启动。

## 可以体验的交互
- 产品、地区和月份切换，联动更新图表与指标。
- 月度趋势、产品构成、世界地图、Top10、地区构成。
- HHI、CR5、有效市场数及份额变化提醒。
- CSV 上传与筛选结果下载；上传数据仅在本次页面会话使用。
- “追加一个月”按钮：更新 CSV 后页面立即重新读取。

## 数据口径
初始数据：2023-01 至 2025-12，3产品×12国家×36月份=1296行。
全球在本示例中指全部12个目的地，不是所有真实国家。地区筛选后 HHI / CR5 和份额改用地区内合计。
同比按上年同月匹配，不使用简单前12行替代。没有同期数据时不显示同比。
模拟数据不是 HS 历史口径示例；真实太阳能等数据需先完成 HS 跨期映射。
世界地图可能需要浏览器访问 Plotly 的地图资源；若网络限制导致底图不显示，其他图表和国家排名仍可用。

CSV 必须包含：
period,product_group,partner_name,iso3,region,trade_value_usd
period 为 YYYY-MM；iso3 为三位国家代码；美元金额为有限非负数；月份—产品—国家不能重复。
真实数据若包括多个 HS 码，应先聚合到上述粒度。不得把世界总计与国家数据同时累加。

## 更新演示
```bash
python update_demo.py         # 追加下一月模拟数据
python update_demo.py --reset # 恢复初始36个月模拟数据
```
演示更新使用原子文件替换；这不等同于真实 Comtrade 增量下载。
真实监测应把 update_demo.py 替换为 API 下载流程，并保留数据验证。
还应补充 quota / retry / checkpoint / 历史修订回查 / 缺期检查。

## GitHub + Streamlit Community Cloud
1. 新建 GitHub 仓库，将本文件夹内部所有文件上传到仓库根目录（包括 .streamlit 和 .github）。
2. 登录 Streamlit Community Cloud 并连接 GitHub。
3. 创建应用，选择仓库与分支，入口填写 app.py。
4. 部署后得到可分享的 streamlit.app 地址。

官方部署说明：https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
当前项目包含 requirements.txt，可以由平台安装依赖。
未代为创建 GitHub 仓库或上线：需要您的 GitHub / Streamlit 账户。

## GitHub Actions 演示
仓库 Actions 中可手动运行 Update simulation data，追加模拟月份并提交 CSV。
当前不设自动日程，避免误把模拟数据增长当作真实监测。
接入真实 API 后，可在工作流 on 下增加 schedule。API 密钥放在仓库 Secrets，勿写入代码。
公开仓库的原始数据和代码可被访问。

Streamlit 云端按钮写入只适合临时演示，云文件可能随重启恢复。
持续更新应由采集端（例如 Actions）提交数据，再由页面读取。

## 文件
app.py 页面；model.py 数据生成/验证/指标；update_demo.py 更新演示；
data/trade_panel.csv 数据；data/metadata.json 更新时间；requirements.txt 依赖。
