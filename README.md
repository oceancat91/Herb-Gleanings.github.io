# 本草拾珍 · Herba Atlas

**中医药材属性的信息可视化期末作品**  
*A Visual Atlas of Traditional Chinese Materia Medica*

> 信息可视化课程 · 期末大作业  
> 评分重点：**数据分析与叙事、可视化设计、交互探索**（非登录/后台类网站功能）

---

## 一、问题意识与作品定位

中药学习常停留在「条文记忆」：四气五味、归经功效彼此割裂，方剂与时代语境更难一眼看清。  
本作品以约 **1000** 味药材与 **100+** 首经典方剂为基底，提出并回答：

1. **史**：本草知识如何随朝代累积、转向？  
2. **方**：经典方如何按功效聚类，君臣佐使如何组网？  
3. **药**：性味归经与禁忌、用量如何形成可对照的结构？

叙事主线：**史给时间坐标 → 方连临床逻辑 → 药落属性与安全**。

---

## 二、与评分细则的对应关系

| 评分项目 | 分值 | 本作品如何体现 | 详见 |
|----------|------|----------------|------|
| 数据分析与信息叙事 | 20 | 开源数据清洗入库；交叉/关联/趋势/词频/共现；「史·方·药」叙事与 insight 结论 | [docs/评分对照.md](docs/评分对照.md#1-数据分析与信息叙事能力20-分) |
| 可视化设计 | 20 | 环图/力导向/热力/桑基等按问题选型；宣纸风编码与层级布局 | 同上 §2 |
| 交互设计 | 15 | 筛选、下钻、朝代切换、炼药试炼、析图标签切图与过渡 | 同上 §3 |
| 技术实现与完成度 | 15 | FastAPI + ECharts；一键启动；同源托管，运行稳定 | 同上 §4 |
| 创新性与综合表现 | 10 | 时代生态、齐药融合成方、单屏析图叙事 | 同上 §5 |
| 展示汇报（5 分钟） | 20 | 见下文「答辩建议」 | 同上 §6 |

完整「评价参考 → 文件证据」表：**[docs/评分对照.md](docs/评分对照.md)**

---

## 三、功能模块（按探索路径）

| 模块 | 可视化与交互要点 |
|------|------------------|
| **首页 · 沿革** | 左侧朝代轴 + 中央方剂功效环；点朝代看累计与结构，点圆心入「时代生态」 |
| **属性图谱** | 四气 / 五味 / 升降沉浮 / 归经 / 功效 / 配伍：图 + 药签 + 详情 |
| **配伍 · 炼药** | 抓药柜（首字母分层）↔ 炼药炉力导向；试炼只给方义不泄组成，齐药后融合显方名 |
| **析图** | 用量·安全 / 词频 / 方剂配伍 / 交叉关系；**主题 Tab + 图标签单屏切换**（无堆叠滚动） |
| **产区** | 大陆疏密图 → 省份药材子页 |

---

## 四、技术栈

| 层级 | 技术 |
|------|------|
| 前端 | `index.html` 单页 · ECharts 5 · 宣纸风 UI |
| 后端 | FastAPI · Uvicorn · SQLAlchemy |
| 数据 | SQLite（`backend/data/herbs.db`）· 方剂 / 时代 / 地理 JSON |
| 分析 | `backend/app/analysis.py` 服务端聚合，前端负责视觉编码与叙事 |

---

## 五、快速开始

### 环境

- Python 3.10+（建议 3.11 / 3.13）
- `python` 已在 PATH 中

### 依赖（首次）

```bash
pip install -r backend/requirements.txt
```

### 一键启动（推荐）

双击 **`启动.bat`** → 自动起后端并打开 **http://127.0.0.1:8000/**

### 手动启动

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- 前端：http://127.0.0.1:8000/  
- API 文档：http://127.0.0.1:8000/docs  

### 重要提示

> **必须通过 `http://127.0.0.1:8000/` 访问。**  
> 不要直接双击 `index.html`，也不要用 Live Server——前端依赖同源 API。

### GitHub Pages

静态预览：[Herb-Gleanings.github.io](https://oceancat91.github.io/Herb-Gleanings.github.io/)  
完整数据与炼药等需本机后端：先运行 `启动.bat`，再在 Pages 上进入本地完整版。

---

## 六、仓库文件分类

按**课程用途**归类（路径未大幅搬迁，避免破坏启动与 API）：

```
可视化期末/
├── index.html                 # 【可视化·交互】主界面与全部图表逻辑
├── china-geo-embed.js         # 【可视化】产区 GeoJSON 嵌入
├── launch.py / 启动.bat       # 【工程】一键启动
├── README.md                  # 【文档】本说明
├── docs/
│   └── 评分对照.md            # 【文档】细则 ↔ 证据 ↔ 文件
└── backend/
    ├── app/                   # 【服务·分析】
    │   ├── main.py            #   API 路由、静态托管
    │   ├── analysis.py        #   交叉 / 安全 / 词频 / 方剂网络等
    │   ├── alchemy.py         #   炼药置入与炼制
    │   ├── workshop.py        #   配伍禁忌校核
    │   ├── era_library.py     #   朝代典籍与方药索引
    │   └── …                  #   models / schemas / database / pinyin_fix
    ├── data/                  # 【数据】
    │   ├── herbs.db           #   运行库（导入生成）
    │   ├── herbs_*.json       #   原始 / 扩充药材
    │   ├── formulas_*.json    #   方剂
    │   ├── era_library.json   #   时代叙事库
    │   ├── era_maps/          #   时代相关地图数据
    │   ├── herb_geo_density.json
    │   └── herb_media/        #   药材媒体元数据（可选）
    ├── scripts/               # 【数据处理】
    │   ├── download_data.py / import_herbs.py / build_extra_herbs.py
    │   ├── expand_to_1000.py / fix_bulk_pinyin.py
    │   ├── build_era_library.py / build_era_maps.py
    │   ├── crawl_*_formulas.py / expand_*formulas.py
    │   └── …
    ├── requirements.txt
    └── README.md              # 后端与字段说明
```

| 分类标签 | 服务评分项 |
|----------|------------|
| 数据 + scripts + analysis | 数据分析与叙事 |
| index.html 图表与布局 | 可视化设计 |
| 筛选 / 炼药 / 切图 / 下钻 | 交互设计 |
| FastAPI + 启动脚本 | 技术实现与完成度 |

---

## 七、数据来源与许可

| 项目 | 说明 |
|------|------|
| 药材主数据 | [本草典 Bencaodian](https://bencaodian.org/en/about/data/) |
| 许可 | **CC BY-SA 4.0**（署：Bencaodian Editorial / 本草典编辑部） |
| 方剂与时代 | 项目内整理 / 扩充的 JSON（`formulas_*.json`、`era_library.json`） |
| 地理 | `china.json`、`herb_geo_density.json` |

《中华本草》等正式出版物受版权保护，本项目**不爬取其全文**，仅使用开源许可数据并在本地规范化、可视化扩展。

重建数据库（可选）见 [`backend/README.md`](backend/README.md)。

---

## 八、主要 API（服务可视化）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/herbs` | 列表（搜索 / 属性筛选） |
| GET | `/api/herbs/{id或key}` | 详情 |
| GET | `/api/formulas/{id或key}` | 方剂全文 |
| GET | `/api/eras`、`/api/eras/{id}` | 朝代索引与生态 |
| GET | `/api/stats` | 属性分布 |
| GET | `/api/analysis` | 析图用聚合 |
| POST | `/api/alchemy/*`、`/api/workshop/check` | 炼药 / 配伍校核 |

---

## 九、答辩建议（5 分钟）

| 时段 | 内容 | 演示 |
|------|------|------|
| 0:00–0:40 | 问题：属性割裂 → 目标：可探索的结构 | 点题即可 |
| 0:40–1:40 | 数据来源、清洗扩充、分析类型（交叉/共现/趋势） | 可闪 `docs/评分对照` 或析图结论 |
| 1:40–4:10 | 三屏：首页朝代环 → 炼药试炼齐药成方 → 析图标签切图 | **主演示** |
| 4:10–4:50 | 设计取舍（单屏析图、试炼不泄组成）、局限与伦理 | 口述 |
| 4:50–5:00 | 收束：史·方·药把条文变成可探索图谱 | 定格首页 |

**一句话收束**

> 用可视化把本草属性从「条文记忆」变成「可探索的结构」：史给时间坐标，方连临床逻辑，药落性味归经与配伍安全。

---

## License

- 本仓库代码供课程展示与学习使用。  
- 药材数据遵循 **CC BY-SA 4.0**，衍生使用请保留本草典署名并遵守相同许可。
