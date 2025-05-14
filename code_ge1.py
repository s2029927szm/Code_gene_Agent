import os
import re
import sqlite3
from openai import OpenAI
from camel.toolkits.code_execution import CodeExecutionToolkit

# 1. 设置 OpenAI API Key
# openai.api_key = os.getenv("OPENAI_API_KEY")

# 2. 定义调用 LLM 以生成查询代码的函数
# 请生成一段 Python 代码，用于打开本地名为 example.db 的 SQLite 数据库，
# 查询 users 表中 id=1 的记录，并打印查询结果。
# 请将完整的可执行代码包含在三重反引号代码块中。
def generate_query_code():
    prompt = """
# You are an expert PostgreSQL assistant. Your task is to translate the 'natural language query' into executable 'Python code' (inculding SQL).
- Analyze the user's question carefully.
- Generate comlete Python code to fulfill the request. You can obtain and quote some necessary information from the following example.
- **Important:** Enclose the 'Python code' within $$$ python ... $$$ markdown block.
- Do not include explanations outside the code block unless specifically asked.
- If you are given an error message from a previous attempt, analyze the error and the 'Python code' that caused it, then provide a corrected 'Python code' in the $$$ python ... $$$ block.

# Example:
- natural language queries: what's the weather in Manchester on 1 Jan 2023 and 2 Jan 2023?
- Python code:
$$$
import psycopg2
from datetime import datetime

def query_weather_data():
    conn_params = {
        "dbname": "manchester_p",
        "user": "postgres",
        "host": "localhost",
        "password": "zhaomin199" #this is the only correct password
    }
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        cur.execute("SELECT * FROM weather_data WHERE date >= '2023-01-01' AND date < '2023-01-03';)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print(query_weather_data())
$$$
# Okey, let's design and generate Python code for the new query:
- natural language queries: what's the weather in Manchester on 19 Nov. 2023?
"""
    client1 = OpenAI(api_key='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')
    completion1 = client1.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0,
    )
    content = completion1.choices[0].message.content
    # response = openai.ChatCompletion.create(
    #     model="gpt-4o",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # # 从返回内容中提取三重反引号内的代码
    # content = response.choices[0].message.content
    with open("./output.txt", "w", encoding="utf-8") as file:
        file.write(content)
    match = re.search(r"\$\$\$\s*python\s*\n(.*?)\$\$\$", content, re.DOTALL)
    return match.group(1) if match else content

# 3. 生成代码
generated_code = generate_query_code()

# 4. 在子进程沙箱中执行生成的代码
toolkit = CodeExecutionToolkit(sandbox="subprocess", require_confirm=False)
result = toolkit.execute_code(generated_code)

# 5. 输出执行结果
print("执行结果：\n", result)
