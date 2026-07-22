from fastmcp import FastMCP
import sqlite3
import os
import json
import aiosqlite
import asyncio
import tempfile

mcp = FastMCP(name='Expense Tracker')

TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR,"expenses.db")
CATEGORIES_PATH =  os.path.join(os.path.dirname(__file__),"categories.json")

# init_db with synchronous sqlite
def init_db():
    try:
        with sqlite3.connect(DB_PATH) as c:
            c.execute( """CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT  NOT NULL,
            sub_category TEXT DEFAULT '',
            note TEXT DEFAULT '')
        """)
    except Exception as e:
        return {'error':f'directory not found{str(e)}'}
init_db()

@mcp.tool
async def add_expenses(date,amount,category,sub_category='',note=''):
    try:
        async with aiosqlite.connect(DB_PATH) as c:
            curr = await c.execute("INSERT INTO expenses(date,amount,category,sub_category,note) VALUES(?,?,?,?,?)",
                            (date,amount,category,sub_category,note))
            await c.commit()
        return {'status':'ok','id':curr.lastrowid,'message':"expense added succesfully"}
        

    except Exception as e:     # Changed: simplified exception handling
       
        return {"status": "error", "message": f"Database error: {str(e)}"}
    

@mcp.tool
async def list_expenses(start_date:str,end_date:str):
        try:
            async with aiosqlite.connect(DB_PATH) as c:
                curr = await c.execute("""SELECT id,date,amount,category,sub_category,note FROM expenses
                                WHERE date BETWEEN ? AND ?
                                ORDER BY id ASC""",
                                (start_date,end_date)
                )
                rows = await curr.fetchall()
                cols = [d[0] for d in curr.description]
            return [dict(zip(cols,r)) for r in rows]
        except Exception as e:
            return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

@mcp.tool
async def summary_expenses(start_date:str,end_date:str,category:str |None=None):
        try:
            async with await aiosqlite.connect(DB_PATH) as c:
                query = ("""SELECT category,SUM(amount) AS total_amount FROM expenses
                        WHERE date BETWEEN ? AND ?""")
                param =  [start_date,end_date]
                if category:
                    query += " AND category = ?"
                    param.append(category)
                query+= "GROUP BY category ORDER BY category ASC"
                rows = await curr.fetchall()
                curr = await c.execute(query,param)
                cols = [d[0] for d in curr.description]
            return [dict(zip(cols,r)) for r in rows]   
        except Exception as e:
            return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}    


@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    try:
        # Provide default categories if file doesn't exist
        default_categories = {
            "categories": [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Travel",
                "Education",
                "Business",
                "Other"
            ]
        }
        try:
            with open('categories.json','r') as json_file:
                data = json_file.read()
            return data
        except FileNotFoundError:
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'
       
             


if __name__ == "__main__":
    mcp.run(transport='http',host='0.0.0.0',port=8000)
    
