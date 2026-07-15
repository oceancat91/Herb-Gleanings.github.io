# 本草拾珍 · Herba Atlas

**中医药材属性的可视化图谱**  
*A Visual Atlas of Traditional Chinese Materia Medica*

---

## 项目简介

《本草拾珍》是一款中医药材属性信息可视化系统。以约 **1000** 味药材与 **100+** 首经典方剂为数据基础，沿「**史 · 方 · 药**」叙事呈现本草沿革，并围绕四气、五味、归经、升降沉浮、功效与配伍构建交互图谱；辅以交叉分析、用量安全、词频探查与方剂配伍网络，帮助读者从属性结构、禁忌警示到经典组方理解中药知识体系。

**English**  
**Herba Atlas** (*Bencao Shizhen*) is an interactive visualization of traditional Chinese materia medica. It connects historical chronology, formulas, and individual drugs, and maps core properties—qi, flavor, meridian tropism, ascending/descending tendencies, therapeutic categories, and compatibility constraints.

---

## 功能概览

| 模块 | 内容 |
|------|------|
| **首页** | 载药规模曲线、时代时间线（代表药 / 代表方）、穿越药历史名片、药方全文 |
| **属性图谱** | 四气 · 五味 · 升降沉浮 · 归经 · 功效 · 配伍（图 + 药签列表 + 详情） |
| **药材详情** | 概述、性味归经、功效主治、用量炮制、禁忌安全、药理与典籍引用 |
| **析图** | 配伍工坊、交叉关系、条件探查、用量·安全、词频·从症到药、方剂配伍网络 |
| **产区** | 大陆疏密图；点击省份进入产区药材子页 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | 单页 `index.html` · ECharts 5 · 宣纸风 UI |
| 后端 | FastAPI · Uvicorn · SQLAlchemy |
| 数据 | SQLite（`backend/data/herbs.db`）· JSON 方剂库 |

---

## 快速开始

### 环境要求

- Python 3.10+（建议 3.11 / 3.13）
- 已将 `python` 加入系统 PATH

### 一键启动（推荐）

双击项目根目录 **`启动.bat`**，或在终端执行：

```bash
pip install -r backend/requirements.txt
python run.py
```

脚本会启动后端并打开浏览器：**http://127.0.0.1:8000/**

### GitHub Pages 预览与本机后端

静态页：[https://oceancat91.github.io/Herb-Gleanings.github.io/](https://oceancat91.github.io/Herb-Gleanings.github.io/)

浏览器**不能**从网页直接启动本机程序。若要在打开 GitHub 主页后自动拉起后端并连库：

1. **首次**双击 `注册本机启动协议.bat`（写入当前用户 `herba://` 协议）
2. 再打开上述 GitHub 主页，允许浏览器打开「本草拾珍」协议
3. 本机 `run.py --daemon` 启动后，页面会自动跳转到 `http://127.0.0.1:8000/` 完整版

也可继续使用 `打开前端.bat` / `python run.py` 直接启动。卸载协议：`卸载本机启动协议.bat`。

### 手动启动

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器访问：http://127.0.0.1:8000/  
API 文档：http://127.0.0.1:8000/docs

### 重要提示

> **必须通过 `http://127.0.0.1:8000/` 访问。**  
> 请勿直接双击打开 `index.html`，也勿使用 VS Code / Cursor 的 Live Server——前端依赖同源 API，否则数据无法加载。

---

## 目录结构

```
可视化期末/
├── index.html              # 前端单页
├── run.py                  # 一键启动（后端 + 浏览器）
├── 启动.bat                # Windows 启动入口
├── 打开前端.bat            # 确保后端后打开页面
├── README.md
└── backend/
    ├── app/
    │   ├── main.py         # FastAPI 入口与路由
    │   ├── analysis.py     # 多维分析聚合
    │   ├── models.py
    │   ├── schemas.py
    │   └── database.py
    ├── data/
    │   ├── herbs.db        # 药材库
    │   ├── herbs_raw.json
    │   ├── herbs_extra.json
    │   └── formulas_raw.json
    ├── scripts/            # 下载 / 导入 /  enrichment 脚本
    ├── requirements.txt
    └── README.md           # 后端与数据说明（更细）
```

---

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/herbs` | 药材列表（搜索 / 筛选 / 分页） |
| GET | `/api/herbs/{id或key}` | 药材详情 |
| GET | `/api/herbs/{id或key}/story` | 历史名片（典籍 + 入方角色） |
| GET | `/api/formulas/{id或key}` | 方剂全文（治法、组成、方解、煎服、加减） |
| GET | `/api/stats` | 属性分布统计 |
| GET | `/api/analysis` | 交叉 / 安全 / 词频 / 方剂配伍等聚合 |

---

## 数据来源与许可

| 项目 | 说明 |
|------|------|
| 药材数据 | [本草典 Bencaodian](https://bencaodian.org/en/about/data/) |
| 许可 | **CC BY-SA 4.0** |
| 署名 | Bencaodian Editorial / 本草典编辑部 |
| 方剂数据 | 项目内整理的经典方剂 JSON（`formulas_raw.json`） |

正式出版物《中华本草》等受版权保护，本项目**不爬取**其全文，仅使用开源许可的同体系数据，并在本地做规范化导入与可视化扩展。

---

## 数据库重建（可选）

若需从原始 JSON 重新导入：

```bash
cd backend
python scripts/download_data.py      # 若尚未下载
python scripts/build_extra_herbs.py  # 生成扩充条目
python scripts/import_herbs.py       # 写入 herbs.db
```

更多字段与脚本说明见 [`backend/README.md`](backend/README.md)。

---

## 课程 / 答辩一句话

> 用可视化把本草属性从「条文记忆」变成「可探索的结构」：史给时间坐标，方连临床逻辑，药落性味归经与配伍安全。

---

## License 备注

- 本仓库代码可供课程展示与学习使用。  
- 药材数据遵循 **CC BY-SA 4.0**，衍生使用请保留本草典署名并遵守相同许可。
