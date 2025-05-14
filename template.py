# import os
# import re
# import sqlite3
# from openai import OpenAI
# from camel.toolkits.code_execution import CodeExecutionToolkit

# def generate_query_code():
#     prompt = """
# # You are an expert PostgreSQL assistant. Your task is to translate the 'natural language query' into executable 'Python code' (inculding SQL).
# # Okey, let's design and generate Python code for the new query:
# - natural language queries: what's the weather in Manchester on 19 Nov. 2023?
# """
#     client1 = OpenAI(api_key=API_KEY)
#     completion1 = client1.chat.completions.create(
#     model="gpt-4o",
#     messages=[{"role": "user", "content": prompt}],
#     temperature=0,
#     )
#     content = completion1.choices[0].message.content
#     with open("./output.txt", "w", encoding="utf-8") as file:
#         file.write(content)
#     match = re.search(r"\$\$\$\s*python\s*\n(.*?)\$\$\$", content, re.DOTALL)
#     return match.group(1) if match else content

# # 3. 生成代码
# generated_code = generate_query_code()

# # 4. 在子进程沙箱中执行生成的代码
# toolkit = CodeExecutionToolkit(sandbox="subprocess", require_confirm=False)
# result = toolkit.execute_code(generated_code)

# # 5. 输出执行结果
# print("执行结果：\n", result)



import os
import re
import json
import sqlite3
from datetime import datetime
from openai import OpenAI
from camel.toolkits.code_execution import CodeExecutionToolkit

API_KEY = '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'
# Path for storing memory of queries and responses
MEMORY_FILE = "./query_memory.json"

def generate_query_code(prompt, conversation_history=None):
    """
    Generate Python code based on a natural language query
    
    Args:
        prompt (str): The prompt to send to the LLM
        conversation_history (list, optional): Previous conversation history
    
    Returns:
        str: Generated code
    """
    client = OpenAI(api_key=API_KEY)
    
    messages = []
    
    # If there's conversation history, include it
    if conversation_history:
        messages = conversation_history
    else:
        messages = [{"role": "user", "content": prompt}]
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0,
    )
    
    content = completion.choices[0].message.content
    
    with open("./output.txt", "w", encoding="utf-8") as file:
        file.write(content)
    
    # Extract Python code from the response
    match = re.search(r"\`\`\`python\s*(.*?)\`\`\`", content, re.DOTALL)
    if not match:
        match = re.search(r"\$\$\$\s*python\s*\n(.*?)\$\$\$", content, re.DOTALL)
    
    return match.group(1) if match else content, content

def fix_code_with_error(query, code, error, conversation_history=None):
    """
    Generate a fixed version of the code based on the error
    
    Args:
        query (str): Original natural language query
        code (str): The code that produced the error
        error (str): Error message from execution
        conversation_history (list, optional): Previous conversation history
    
    Returns:
        tuple: (fixed_code, full_response, updated_history)
    """
    if conversation_history is None:
        conversation_history = []
    
    # Create prompt for fixing the code
    fix_prompt = f"""
You previously generated code for this query: "{query}"

The code you generated was:
```python
{code}
```

But it resulted in this error:
```
{error}
```

Please fix the code to properly handle this error. Only provide the corrected Python code.
"""
    
    # Add this exchange to the conversation history
    updated_history = conversation_history.copy()
    updated_history.append({"role": "user", "content": fix_prompt})
    
    # Generate fixed code
    client = OpenAI(api_key=API_KEY)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=updated_history,
        temperature=0,
    )
    
    full_response = completion.choices[0].message.content
    updated_history.append({"role": "assistant", "content": full_response})
    
    # Extract Python code from the response
    match = re.search(r"\`\`\`python\s*(.*?)\`\`\`", full_response, re.DOTALL)
    if not match:
        match = re.search(r"\$\$\$\s*python\s*\n(.*?)\$\$\$", full_response, re.DOTALL)
    
    fixed_code = match.group(1) if match else full_response
    
    return fixed_code, full_response, updated_history

def save_to_memory(query, final_result, success):
    """
    Save query and final result to a JSON memory file
    
    Args:
        query (str): The natural language query
        final_result (str): The final output (successful or error)
        success (bool): Whether the execution was successful
    """
    # Create memory entry
    memory_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "result": final_result,
        "success": success
    }
    
    # Load existing memory if it exists
    memory = []
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                memory = json.load(file)
        except json.JSONDecodeError:
            # Handle corrupted JSON file
            memory = []
    
    # Add new entry and save
    memory.append(memory_entry)
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=2)

def extract_query_from_prompt(prompt):
    """Extract the natural language query from the prompt"""
    match = re.search(r"natural language queries:\s*(.*?)(?:\n|$)", prompt, re.DOTALL)
    if match:
        return match.group(1).strip()
    return prompt  # Return the whole prompt if no pattern is found

def main():
    # Initial prompt with query
    prompt = """
# You are an expert PostgreSQL assistant. Your task is to translate the 'natural language query' into executable 'Python code' (inculding SQL).
# Okey, let's design and generate Python code for the new query:
- natural language queries: what's the weather in Manchester on 19 Nov. 2023?
"""
    
    # Extract the query for memory purposes
    query = extract_query_from_prompt(prompt)
    print(f"Processing query: {query}")
    
    # Initialize conversation history
    conversation_history = [{"role": "user", "content": prompt}]
    
    # Generate initial code
    generated_code, full_response = generate_query_code(prompt)
    conversation_history.append({"role": "assistant", "content": full_response})
    
    # Initialize toolkit
    toolkit = CodeExecutionToolkit(sandbox="subprocess", require_confirm=False)
    
    # Maximum number of fix attempts
    MAX_ATTEMPTS = 3
    attempts = 0
    success = False
    result = None
    
    # Loop for error fixing
    while attempts < MAX_ATTEMPTS:
        try:
            # Execute the generated code
            print(f"\nAttempt {attempts + 1}/{MAX_ATTEMPTS}:")
            print("Executing code...")
            result = toolkit.execute_code(generated_code)
            
            # If we get here, execution was successful
            print("Code executed successfully!")
            success = True
            break
            
        except Exception as e:
            # Code execution failed
            error_message = str(e)
            print(f"Execution failed with error: {error_message}")
            
            # Increment attempt counter
            attempts += 1
            
            if attempts >= MAX_ATTEMPTS:
                print(f"Maximum attempts ({MAX_ATTEMPTS}) reached. Giving up.")
                result = f"Failed after {MAX_ATTEMPTS} attempts. Last error: {error_message}"
                break
            
            # Generate fixed code using the error information
            print("Generating fixed code...")
            generated_code, full_response, conversation_history = fix_code_with_error(
                query, 
                generated_code, 
                error_message,
                conversation_history
            )
    
    # Output execution result
    print("\nFinal execution result:")
    print(result)
    
    # Save to memory
    save_to_memory(query, result, success)
    print(f"\nQuery and result saved to {MEMORY_FILE}")

if __name__ == "__main__":
    main()


