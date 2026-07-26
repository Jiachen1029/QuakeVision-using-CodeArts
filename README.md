# Tongji_Database_Earthquake

同济大学华为码道实习项目——QuakeVision · 地震信息查询可视化平台。 项目涵盖地震数据的**结构化存储、数据导入、查询接口与基础可视化展示**等功能。

---

## 📁 项目结构

```
Tongji_Database_Earthquake/
├── app/                      # 后端应用代码（Flask 等）
├── frontend/                 # 前端页面或前端框架代码
├── app.db                    # SQLite 示例数据库
├── config.py                 # 系统配置（数据库路径等）
├── init_db.py                # 数据库初始化脚本
├── import_data.py            # 地震 Excel 数据导入脚本
├── inspect_excel.py          # Excel 数据结构检查脚本
├── run.py                    # 后端服务启动入口
├── schema.sql                # 数据库表结构定义
├── 速报目录.xls  # 原始地震速报数据
└── README.md
```

---

## 🚀 项目功能

- 地震速报数据的数据库建模与管理
- 从 Excel 文件自动导入历史地震数据
- 提供后端接口用于地震信息查询
- 支持前端页面或接口形式的数据展示
- 便于后续扩展可视化与统计分析功能

---

## 🧱 数据库初始化

首次运行前需初始化数据库表结构：

```bash
python init_db.py
```

或手动执行：

```bash
sqlite3 app.db < schema.sql
```

---

## ▶️ 启动后端服务

```bash
python run.py
```

默认访问地址：

```
http://127.0.0.1:5000
```

---

## 📥 地震数据导入

项目中的管理员/职员可以直接在系统中上传数据表格，表格数据来源为：中国地震台网速报地震目录
https://data.earthquake.cn/datashare/report.shtml?PAGEID=earthquake_subao

当然，可以使用简单粗暴的方式，将 Excel 格式的地震速报数据导入数据库：

```bash
python import_data.py "速报目录.xls"
```

支持自定义文件路径：

```bash
python import_data.py /path/to/your/data.xls
```

---

## 🌐 前端说明

项目包含 `frontend/` 目录，可用于地震数据的前端展示。  

```bash
cd frontend
npm install
npm run dev
```

---

## 📊 数据库说明

数据库结构定义在 `schema.sql` 中，核心字段包括：

- 地震发生时间
- 经度 / 纬度
- 震级
- 深度
- 地点描述
- ......

---
