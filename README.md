# 湖表压实台（cc-compact-lab）

CC_Codex 二期数据工程产品线：Tornado + 原生 JS 时间轴 SPA + SQLite。

## 主链

1. 小文件清单：登记湖区碎文件与体积
2. 压实计划：把碎文件编入计划
3. 重写合并：执行合并任务并回写状态
4. 体积对账：计划前后体积对照报告
5. 台参数：现行压实阈值与阈值说明

默认账号 `admin` / `123456`，端口 `7300`。

## 预留切口（出题用，基线先通）

- 计划与清单体积同源
- 合并失败半态 / 重跑
- 对账快照与现行体积

## 本地

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
python run.py
```
