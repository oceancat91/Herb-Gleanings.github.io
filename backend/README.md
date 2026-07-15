# 本草拾珍 · 后端数据库

中医药材属性 API 与 SQLite 数据库。

## 重要说明：数据来源

正式出版物《中华本草》（上海科学技术出版社）受版权保护，**不可直接爬取全文**。

本项目采用开源许可的同体系本草数据：

| 项目 | 说明 |
|------|------|
| 数据源 | [本草典 Bencaodian](https://bencaodian.org/en/about/data/) |
| 规模 | 365 味标准药材 |
| 许可 | **CC BY-SA 4.0** |
| 署名 | Bencaodian Editorial / 本草典编辑部 |
| 字段 | 四气、五味、归经、功效、主治、用量、炮制、禁忌、药理、典籍引用等 |

字段设计对齐可视化前端的六大分类：**四气 / 五味 / 升降沉浮 / 归经 / 功效 / 配伍**。

## 快速开始

**推荐：双击项目根目录的 `启动.bat`**（或运行 `python run.py`）。  
脚本会自动启动后端，并在浏览器打开前端：http://127.0.0.1:8000/

手动启动：

```bash
cd backend
pip install -r requirements.txt

# 若尚未下载原始 JSON（已下载可跳过）
python scripts/download_data.py

# 导入数据库（自动合并 data/herbs_extra.json 扩充条目）
python scripts/build_extra_herbs.py   # 生成扩充 JSON（可重复运行）
python scripts/expand_to_1000.py      # 通识批量扩充至约 1000 味（不爬取《中华本草》）
python scripts/import_herbs.py

# 启动 API（同时托管前端页面）
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开前端：http://127.0.0.1:8000/  
打开文档：http://127.0.0.1:8000/docs

## API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/herbs` | 分页列表，支持 `q/siqi/wuwei/guijing/shengjiang/category` |
| GET | `/api/herbs/{id或key}` | 单味药材详情 |
| GET | `/api/stats` | 各属性分布统计（供可视化） |
| GET | `/api/categories` | 功效分类及数量 |
| GET | `/api/filter/siqi/{寒\|凉\|平\|温\|热}` | 按四气筛选 |
| GET | `/api/filter/wuwei/{酸\|苦\|甘\|辛\|咸}` | 按五味筛选 |
| GET | `/api/filter/guijing/{心\|肝\|脾…}` | 按归经筛选 |

### 示例

```bash
# 搜索人参
curl "http://127.0.0.1:8000/api/herbs?q=人参"

# 寒性药
curl "http://127.0.0.1:8000/api/filter/siqi/寒"

# 统计
curl "http://127.0.0.1:8000/api/stats"
```

## 数据库结构（`data/herbs.db`）

表 `herbs` 主要字段：

- `name_zh` / `name_pinyin` / `name_latin` — 名称
- `siqi` — 四气（寒凉平温热…）
- `wuwei` — 五味（酸苦甘辛咸…，顿号分隔）
- `guijing` — 归经（心肝脾肺肾…）
- `shengjiang` — 升降沉浮（按功效分类推断）
- `gongxiao` / `gongxiao_detail` — 功效摘要与明细
- `zhuzhi` — 主治
- `peiwu_jinji` — 配伍禁忌（含十八反等）
- `dosage_*` — 用量
- `paozhi` / `jinjizheng` / `anquan` / `pharmacology` — 炮制、禁忌、安全、药理

## 目录

```
backend/
├── app/
│   ├── main.py          # FastAPI 入口
│   ├── models.py        # SQLAlchemy 模型
│   ├── schemas.py       # Pydantic 响应模型
│   └── database.py      # SQLite 连接
├── scripts/
│   ├── download_data.py # 下载开源 JSON
│   └── import_herbs.py  # 规范化并入库
├── data/
│   ├── herbs_raw.json   # 原始开源数据
│   └── herbs.db         # SQLite 数据库
└── requirements.txt
```
