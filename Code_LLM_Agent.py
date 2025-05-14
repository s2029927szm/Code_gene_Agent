import os
import re
import json
import sqlite3
from datetime import datetime
from openai import OpenAI
from camel.toolkits.code_execution import CodeExecutionToolkit
from functions_tem import func_desp


# API_KEY = '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'
# Path for storing memory of queries and responses
MEMORY_FILE = "./query_memory.json"

def call_llm(prompt: str, tem: float=0)-> str:
    client = OpenAI(api_key='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')
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature = tem,
    )
    return completion.choices[0].message.content

def task_plan_agent(query: str, his: str=None)-> str:
    tpa_promt="""
You are a planning assistant that turns a user's current natural-language question into a structured plan for downstream APIs.
## Available functions ##
traffic volume | weather | poi | road close | road accident | road event

## Guidelines ##
1. **Reason first.**  
   - Think step-by-step about which function(s) are needed, and any other details the APIs will require.  
   - Write this internal chain-of-thought prefixed with the word **“Thoughts:”**, and keep it concise.

2. **Then output the plan.**  
   - Wrap the plan exactly like:
     '''plan
     { ... }
     '''

   - Inside the triple single-quotes is a *valid Python dict* whose keys are **only** the allowed function names.  
   - The value for each key is a short sub-query that contains all essential information (who / what / where / when) needed by that function.  
   - Include **only** the functions that are truly relevant; omit all others. Some information may be provided from conversation history.

3. **Output format strictness.**  
   - Produce nothing except the “Thoughts:” line and the plan block.  
   - Do **not** add explanations, salutations, markdown headings, or extra text.

## Example (for dev)  ##
_User query_:  
“what's the car volume near Manchester Piccadilly and Oxford Road on 11 June 2024, and please also give me the weather and POI information at the same time and place?”

_Model response_:  
Thoughts: The user wants traffic volume, weather, and POIs for Manchester Piccadilly/Oxford Road on 2024-06-11; no road incidents requested.

'''plan
{
  "traffic volume": "car volume near Manchester Piccadilly and Oxford Road on 11 June 2024",
  "weather": "weather near Manchester Piccadilly and Oxford Road on 11 June 2024",
  "poi": "points of interest near Manchester Piccadilly and Oxford Road"
}
'''

## Conversation to solve ##
"""
    tpa_con_his = "" if his is None else his
    tpa_promt = tpa_promt+f"""
_conversation history_: 
{tpa_con_his}
"""
    tpa_promt = tpa_promt+f"""
_conversation history_: 
{query}
"""
    tpa_response = call_llm(tpa_promt, 0.1)
    match = re.search(r"'''(?:plan\s*)?\n(.*?)'''", tpa_response, re.DOTALL)
    if match:
        plan_str = match.group(1)
        # print("Extracted content:\n", tpa_response, plan_str)
    else:
        print("No match found.")
    plan_dict = json.loads(plan_str)
    return plan_str, plan_dict


# task_plan_agent("what's the road close, accident and roadwork information near Manchester Oxford Road in April 2024?")

def code_generate(query: str, exmp: str)-> str:
    sys_prompt = f"""
# You are an expert PostgreSQL assistant. Your task is to translate the 'natural language query' into executable 'Python code' (inculding SQL).
- Analyze the user's question carefully.
- Generate comlete Python code to fulfill the request. You can obtain and quote some necessary information from the following example.
- **Important:** Enclose the 'Python code' within $$$ python ... $$$ markdown block.
- Do not include explanations outside the code block unless specifically asked.
- If you are given an error message from a previous attempt, analyze the error and the 'Python code' that caused it, then provide a corrected 'Python code' in the $$$ python ... $$$ block.

# Example:
{exmp}

# Okey, let's design and generate Python code for the new query:
- natural language query: {query}
"""
    content = call_llm(sys_prompt, 0)
    with open("./output.txt", "w", encoding="utf-8") as file:
        file.write(content)
    match = re.search(r"\$\$\$\s*python\s*\n(.*?)\$\$\$", content, re.DOTALL)
    return match.group(1) if match else None, sys_prompt
    
def code_debug(query: str)-> str:
    sys_prompt = f"""
##read conversation first##
{query}
## You are an expert code debug assistant. Your task is to fix the error of the last **error message** for the last **python code** to solve the **natural language query**. Now give the bug free python code and make it solve the initial query.##
- **Important:** Enclose the output 'Python code' (bug free) within $$$ python ... $$$ markdown block.
"""
    content = call_llm(sys_prompt, 0)
    # with open("./output.txt", "w", encoding="utf-8") as file:
    #     file.write(content)
    match = re.search(r"\$\$\$\s*python\s*\n(.*?)\$\$\$", content, re.DOTALL)
    return match.group(1) if match else None


# def code_gene_agent(query: str, exmp: str)-> str:
#     cga_max_loop = 3
#     cga_short_memo = ""
#     cga_attempts = 1

#     # call code generation first, add whole prompt as initial short term memory
#     cga_code0, sys_pro = code_generate(query, exmp)
#     cga_short_memo = cga_short_memo+f"""
# {sys_pro}
# - Python code:
# $$$
# {cga_code0}
# $$$
# """
#     if cga_code0 is None:
#         print("**************************\n first generate code is wrong !!!!!\n\n\n")
    
#     # process the code first
#     toolkit = CodeExecutionToolkit(sandbox="subprocess", require_confirm=False)
#     result = toolkit.execute_code(cga_code0)
#     print(f"^^^^^\n^^^^^^^^^^\n{result}\n\n^^^^^^^^^^^^^^^\n^^^^^^^^^^^^\n")
#     if "Error:" in result or "Traceback" in result:
#         error_message = result
#         cga_short_memo = cga_short_memo + f"""
# - error message after execution:
# {error_message}
# """

#         # if the first process has error, start debug
#         while cga_attempts > cga_max_loop:

#             # call code debug iteratively
#             cga_code1 = code_debug(cga_short_memo)
#             print(f"^^^^^^ attempts: {cga_attempts} ^^^^^^^\n\n{cga_code1}\n\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
#             cga_attempts+=1

#             # add the new code to short term memory
#             cga_short_memo = cga_short_memo + f"""
# - Python code:
# $$$
# {cga_code1}
# $$$
# """
#             result = toolkit.execute_code(cga_code1)
#             if "Error:" in result or "Traceback" in result:
#                 error_message = result
#                 cga_short_memo = cga_short_memo + f"""
# - error message after execution:
# {error_message}
# """
#             else:
#             # try:
#             #     result = toolkit.execute_code(cga_code1)
#                 return cga_code1, result

#         return f"after 3 times debug, LLM agent still cannot fix the problem: {error_message}" , error_message



#     else:
#         result = toolkit.execute_code(cga_code0)
#         return cga_code0, result




    

# from flask import Flask, render_template, request, jsonify

# app = Flask(__name__)
# exec_counter = 0

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/chat', methods=['POST'])
# def chat():
# #def main(long_term: str, user_query: str)-> str:
#     # user_query = "what's the weather in Manchester on 19 Nov. 2023?"
#     long_term = ""
#     sum_result = ""
#     global exec_counter
#     msg = request.json.get('message', '')
#     user_query = msg
#     generated_code = ""
#     output = ""

#     #1. planning agent process the query and reasoning the plan
#     plan_content, plan_dic = task_plan_agent(user_query, long_term)

#     #2. process the plan one by one
#     for i, (key, value) in enumerate(plan_dic.items()):
#         print(f"*** This is {i+1} sub-task:\n")
#         func_example = func_desp[key]

#         #3. calling code generating agent to finish the task
#         sub_code, sub_result = code_gene_agent(value, func_example)

#         #4. summary the result and make the answer concise
#         sum_propmt = sub_result + f"""
# ###
# please summary the above result for the query: {value}
# """
#         sum_sub_result = call_llm(sum_propmt)
#         sum_result+= sum_sub_result

#         #####
#         generated_code += f"Sub-task{i+1} Generated code: \n{sub_code}"
#         output += f"Sub-task{i+1} Executed result: \n{sub_result}"
    
#     # add the final total results into long term memory
#     long_term+= f"_user query_:\n{user_query}\n\n_LLM agent answer_:\n{sum_result}\n\n"

#     #########
#     response_text = sum_result
#     return jsonify({
#         'response': response_text,
#         'code': generated_code,
#         'output': output
#     })
#     # return sum_result

# # if __name__ == "__main__":
# #     main("")

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)



def code_gene_agent(query: str, exmp: str) -> tuple:
    cga_max_loop = 3
    cga_short_memo = ""
    cga_attempts = 1
    
    # Lists to collect intermediate results
    all_code_versions = []
    all_execution_results = []
    final_code = None
    final_result = None
    success = False

    # call code generation first, add whole prompt as initial short term memory
    cga_code0, sys_pro = code_generate(query, exmp)
    cga_short_memo = cga_short_memo+f"""
{sys_pro}
- Python code:
$$$
{cga_code0}
$$$
"""
    # Store the first code version
    all_code_versions.append({"attempt": 1, "code": cga_code0})
    
    if cga_code0 is None:
        print("**************************\n first generate code is wrong !!!!!\n\n\n")
        all_execution_results.append({"attempt": 1, "result": "Error: Failed to generate code", "success": False})
        return None, "Error: Failed to generate code", all_code_versions, all_execution_results, False
    
    # process the code first
    toolkit = CodeExecutionToolkit(sandbox="subprocess", require_confirm=False)
    result = toolkit.execute_code(cga_code0)
    # print(f"^^^^^\n^^^^^^^^^^\n{result}\n\n^^^^^^^^^^^^^^^\n^^^^^^^^^^^^\n")
    
    # Store first execution result
    all_execution_results.append({"attempt": 1, "result": result, "success": not ("Error:" in result or "Traceback" in result)})
    match = re.search(r"> Executed Results:\s*(.*)", result, re.DOTALL)
    match = match.group(1).strip()
    
    if "Error:" in match or "Traceback" in match:
        error_message = result
        cga_short_memo = cga_short_memo + f"""
- error message after execution:
{error_message}
"""
        # if the first process has error, start debug
        while cga_attempts < cga_max_loop:  # Fixed the condition (was > instead of <)
            cga_attempts += 1
            
            # call code debug iteratively
            cga_code1 = code_debug(cga_short_memo)
            # print(f"^^^^^^ attempts: {cga_attempts} ^^^^^^^\n\n{cga_code1}\n\n^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")
            
            # Store this version of code
            all_code_versions.append({"attempt": cga_attempts, "code": cga_code1})
            
            # add the new code to short term memory
            cga_short_memo = cga_short_memo + f"""
- Python code:
$$$
{cga_code1}
$$$
"""
            result = toolkit.execute_code(cga_code1)
            
            # Store this execution result
            all_execution_results.append({"attempt": cga_attempts, "result": result, "success": not ("Error:" in result or "Traceback" in result)})
            match = re.search(r"> Executed Results:\s*(.*)", result, re.DOTALL)
            match = match.group(1).strip()
    
            if "Error:" in match or "Traceback" in match:
            #if "Error:" in result or "Traceback" in result:
                error_message = result
                cga_short_memo = cga_short_memo + f"""
- error message after execution:
{error_message}
"""
            else:
                # Success! Return the final working code and result
                final_code = cga_code1
                final_result = result
                success = True
                return final_code, final_result, all_code_versions, all_execution_results, success

        # If we get here, we've exhausted all attempts
        final_result = f"After {cga_max_loop} debug attempts, LLM agent still cannot fix the problem: {error_message}"
        return None, final_result, all_code_versions, all_execution_results, False
    else:
        # First attempt worked successfully
        final_code = cga_code0
        final_result = result
        success = True
        return final_code, final_result, all_code_versions, all_execution_results, success

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
exec_counter = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    # user_query = "what's the weather in Manchester on 19 Nov. 2023?"
    long_term = ""
    sum_result = ""
    global exec_counter
    msg = request.json.get('message', '')
    user_query = msg
    
    # Data structures to collect all intermediate results
    all_generated_code = []
    all_execution_results = []
    all_summary_results = []

    #1. planning agent process the query and reasoning the plan
    plan_content, plan_dic = task_plan_agent(user_query, long_term)

    #2. process the plan one by one
    for i, (key, value) in enumerate(plan_dic.items()):
        # print(f"*** This is {i+1} sub-task:\n")
        func_example = func_desp[key]

        #3. calling code generating agent to finish the task
        sub_code, sub_result, code_versions, execution_results, success = code_gene_agent(value, func_example)
        
        # Store all intermediate results in organized formats
        task_results = {
            "task_number": i+1,
            "task_description": value,
            "function_type": key,
            "code_versions": code_versions,
            "execution_results": execution_results,
            "final_code": sub_code,
            "final_result": sub_result,
            "success": success
        }
        
        all_generated_code.append(task_results)
        
        #4. summary the result and make the answer concise
        sum_propmt = sub_result + f"""
###
please summary the above result for the query: {value}
"""
        sum_sub_result = call_llm(sum_propmt)
        sum_result += sum_sub_result
        
        all_summary_results.append({
            "task_number": i+1,
            "summary": sum_sub_result
        })
    
    # add the final total results into long term memory
    long_term += f"_user query_:\n{user_query}\n\n_LLM agent answer_:\n{sum_result}\n\n"
    
    # Format the code and output for display
    formatted_code = format_code_for_display(all_generated_code)
    formatted_output = format_output_for_display(all_generated_code)
    
    # Return detailed information including all intermediate steps
    return jsonify({
        'response': sum_result,
        'code': formatted_code,  
        'output': formatted_output,
        'detailed_results': {
            'plan': plan_dic,
            'all_generated_code': all_generated_code,
            'all_summary_results': all_summary_results
        }
    })

def format_code_for_display(all_generated_code):
    """Format all code versions for display in web interface"""
    formatted_text = ""
    
    for task in all_generated_code:
        formatted_text += f"== SUB-TASK {task['task_number']}: {task['task_description']} ==\n\n"
        
        for version in task['code_versions']:
            formatted_text += f"--- Attempt {version['attempt']} ---\n"
            formatted_text += f"{version['code']}\n\n"
            
        formatted_text += "----------------------------------------\n\n"
    
    return formatted_text

def format_output_for_display(all_generated_code):
    """Format all execution results for display in web interface"""
    formatted_text = ""
    
    for task in all_generated_code:
        formatted_text += f"== SUB-TASK {task['task_number']}: {task['task_description']} ==\n\n"
        
        for result in task['execution_results']:
            formatted_text += f"--- Attempt {result['attempt']} ---\n"
            formatted_text += f"{'SUCCESS' if result['success'] else 'ERROR'}\n"
            formatted_text += f"{result['result']}\n\n"
            
        formatted_text += "----------------------------------------\n\n"
    
    return formatted_text

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)