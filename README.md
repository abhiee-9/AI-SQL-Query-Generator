# 🧠 NaturalQuery: AI-Powered SQL Generator

Transform **natural language into optimized SQL queries** with AI-driven intelligence. NaturalQuery combines the power of **GPT-4**, **FastAPI**, and **Streamlit** to make database querying accessible to everyone.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue.svg)](https://mysql.com)

---

## 🎯 What NaturalQuery Does

**Input:** _"Show me all customers who purchased more than $1000 worth of products last month"_

**Output:** Optimized SQL query + execution results + performance recommendations

---

## ✨ Key Features

🤖 **AI-Powered Translation** - Convert plain English to optimized SQL using GPT-4  
⚡ **Smart Query Execution** - Run queries safely with built-in validation  
🔍 **Performance Analysis** - Get execution plans and indexing recommendations  
🎨 **Interactive Web UI** - User-friendly Streamlit interface  
🚀 **REST API Ready** - FastAPI backend for integration  
📊 **Multi-Database Support** - MySQL, PostgreSQL, SQL Server ready  
🛡️ **Query Validation** - Syntax checking before execution

---

## Screenshots of Work

### UI

<div align="center">
  <img src="results/ui.png" alt="Application Screenshot" width="700" height="auto">
</div>

### Query Generation

<div align="center">
  <img src="results/r1.png" alt="Application Screenshot" width="700" height="auto">
</div>

### Query Execution

<div align="center">
  <img src="results/r2.png" alt="Application Screenshot" width="700" height="auto">
</div>

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- OpenAI API Key

### 1️⃣ Installation

```bash
git clone https://github.com/yourusername/naturalquery.git
cd naturalquery

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Configuration

Copy the example env file and fill in your own values:

```bash
cp .env.example .env
```

```env
# Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
MYSQL_PORT=3306

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
```

### 3️⃣ Launch Application

```bash
# 1. Install updated requirements
pip install -r requirements.txt

# 2. Start FastAPI (Terminal 1)
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000

# 3. Start Streamlit (Terminal 2)
python -m streamlit run ui.py
```

### 4️⃣ Access the Application

- **Web Interface:** http://localhost:8501
- **API Documentation:** http://localhost:8000/docs

---

## 💡 Usage Examples

### Natural Language Queries

```
✅ "Find all orders placed in the last 30 days"
✅ "Show me the top 5 customers by total purchase amount"
✅ "List products that are running low on inventory"
✅ "Get monthly revenue trends for this year"
```

## 📁 Project Structure

```
naturalquery/
├── app.py                 # FastAPI application
├── query_generator.py     # Core AI logic
├── database.py           # Database connection & schema
├── ui.py                 # Streamlit interface
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

---

## 🛡️ Safety

QueryZen only ever generates and executes **read-only `SELECT`/`WITH` statements**.
Any generated or manually submitted query containing mutating keywords
(`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, etc.) is rejected
before it ever reaches the database. Queries without an explicit `LIMIT` are
automatically capped (`DEFAULT_ROW_LIMIT`, default 200 rows) to keep demos fast
and safe against accidentally scanning huge tables.

---

## 🔧 Configuration Options

### Database Support

- **MySQL** (default)
- **PostgreSQL**
- **SQL Server**
- **Snowflake**

### AI Models

- **GPT-4** (recommended)
- **GPT-3.5-turbo** (faster, cost-effective)

---

**Made with ❤️ by Ovi**
