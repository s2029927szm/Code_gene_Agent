import os
import re
import psycopg2
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MAX_DEBUG_LOOPS = 3
# Consider using a less privileged user for safety
DB_CONNECTION_STRING = f"dbname='{DB_NAME}' user='{DB_USER}' host='{DB_HOST}' port='{DB_PORT}' password='{DB_PASSWORD}'"

# --- OpenAI Client Initialization ---
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Helper Functions ---

def get_db_schema(conn_string):
    """
    Connects to the database and retrieves schema information (table names and columns).
    This is crucial context for the LLM.
    """
    schema = {}
    try:
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Get table names
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
                """)
                tables = [row[0] for row in cur.fetchall()]

                # Get columns for each table
                for table in tables:
                    cur.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = '{table}';
                    """)
                    columns = {row[0]: row[1] for row in cur.fetchall()}
                    schema[table] = columns
        return schema
    except psycopg2.Error as e:
        print(f"Database Schema Error: {e}")
        return None # Indicate failure

def format_schema_for_prompt(schema):
    """Formats the schema dictionary into a string for the LLM prompt."""
    if not schema:
        return "Could not retrieve database schema."
    prompt = "Database Schema:\n"
    for table, columns in schema.items():
        prompt += f"Table: {table}\n"
        prompt += " Columns:\n"
        for col_name, col_type in columns.items():
            prompt += f"  - {col_name}: {col_type}\n"
        prompt += "\n"
    return prompt.strip()

def extract_sql_code(llm_response):
    """
    Extracts the SQL code block from the LLM's response.
    Assumes the LLM uses Markdown format (```sql ... ```).
    """
    # Regex to find SQL code blocks
    match = re.search(r"```sql\s*([\s\S]+?)\s*```", llm_response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    else:
        # Fallback: maybe the LLM just returned SQL directly?
        # Be cautious with this, might grab non-SQL text.
        # Simple check: does it contain SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP?
        if any(keyword in llm_response.upper() for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]):
             print("Warning: Could not find ```sql block, attempting to use the entire response as SQL.")
             return llm_response.strip()
    return None # No SQL found


def execute_sql(conn_string, sql_query):
    """
    Executes the generated SQL query against the PostgreSQL database.
    Returns the result (as a pandas DataFrame) or an error message.
    """
    try:
        with psycopg2.connect(conn_string) as conn:
            with conn.cursor() as cur:
                print(f"Executing SQL:\n{sql_query}")
                cur.execute(sql_query)

                # Check if the query was likely a SELECT statement to fetch results
                # This is a heuristic; DDL/DML might not have fetchable results
                if cur.description:
                    colnames = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    df = pd.DataFrame(results, columns=colnames)
                    print("Execution successful.")
                    return df, None # Data, No error
                else:
                    # For INSERT, UPDATE, DELETE, etc., report success but no data frame
                    # Might want to return cur.rowcount if useful
                    conn.commit() # Important for DML/DDL
                    print(f"Execution successful. Rows affected: {cur.rowcount}")
                    return f"Command executed successfully. Rows affected: {cur.rowcount}", None # Success message, No error

    except psycopg2.Error as e:
        print(f"SQL Execution Error: {e}")
        # Try to return a clean error message
        error_message = f"PostgreSQL Error:\n{e.pgcode}\n{e.pgerror}\nQuery:\n{sql_query}"
        return None, error_message # No data, Error message
    except Exception as e:
        print(f"Unexpected Execution Error: {e}")
        return None, f"Unexpected Error: {str(e)}\nQuery:\n{sql_query}" # No data, Error message

# --- Main Agent Class ---

class LLMDatabaseAgent:
    def __init__(self, openai_client, db_conn_string, max_loops=MAX_DEBUG_LOOPS):
        self.client = openai_client
        self.db_conn_string = db_conn_string
        self.max_loops = max_loops
        self.schema_info = None
        self.schema_prompt = ""

    def _load_schema(self):
        """Loads and formats the database schema."""
        print("Loading database schema...")
        self.schema_info = get_db_schema(self.db_conn_string)
        if self.schema_info:
            self.schema_prompt = format_schema_for_prompt(self.schema_info)
            print("Schema loaded successfully.")
            # print(f"Schema for Prompt:\n{self.schema_prompt}") # Optional: print schema
        else:
            print("Failed to load database schema. LLM may generate incorrect queries.")
            self.schema_prompt = "Error: Could not retrieve database schema."

    def process_query(self, user_query):
        """
        Main method to process a user's natural language query.
        Handles interaction with LLM, code execution, and debugging loop.
        """
        if not self.schema_prompt:
            self._load_schema()
            if not self.schema_info: # Check again if loading failed
                 return "Error: Cannot proceed without database schema.", None

        print(f"\nProcessing Query: '{user_query}'")

        conversation_history = [
            {
                "role": "system",
                "content": f"""You are an expert PostgreSQL assistant. Your task is to translate natural language queries into executable SQL code based on the provided database schema.
- Analyze the user's request and the schema carefully.
- Generate *only* the SQL query required to fulfill the request.
- **Important:** Enclose the final SQL query within ```sql ... ``` markdown block.
- Do not include explanations outside the code block unless specifically asked.
- If the request is ambiguous or requires information not present in the schema, ask for clarification (though prefer generating SQL if possible).
- Ensure the generated SQL is compatible with PostgreSQL.
- If you are given an error message from a previous attempt, analyze the error and the SQL code that caused it, then provide a corrected SQL query in the ```sql ... ``` block.

{self.schema_prompt}"""
            },
            {
                "role": "user",
                "content": f"Generate the PostgreSQL query for this request: {user_query}"
            }
        ]

        last_error = None
        generated_sql = None

        for attempt in range(self.max_loops):
            print(f"\n--- Attempt {attempt + 1} of {self.max_loops} ---")
            try:
                print("Calling OpenAI API...")
                response = self.client.chat.completions.create(
                    model="gpt-4o", # Or "gpt-3.5-turbo", or other appropriate model
                    messages=conversation_history,
                    temperature=0.2, # Lower temperature for more deterministic code generation
                )
                llm_response_content = response.choices[0].message.content
                print("LLM Response Received.")
                # print(f"LLM Raw Response:\n{llm_response_content}") # Debugging

                generated_sql = extract_sql_code(llm_response_content)

                if not generated_sql:
                    print("Error: Could not extract SQL code from LLM response.")
                    last_error = "LLM did not provide SQL code in the expected format (```sql ... ```)."
                    # Add this failure to the conversation history in case we want to retry
                    conversation_history.append({"role": "assistant", "content": llm_response_content})
                    conversation_history.append({"role": "user", "content": "You did not provide the SQL code inside a ```sql block. Please provide only the SQL code inside ```sql ... ```."})
                    continue # Try asking again

                # Execute the extracted SQL
                result_data, execution_error = execute_sql(self.db_conn_string, generated_sql)

                if execution_error:
                    print(f"Execution failed. Error: {execution_error}")
                    last_error = execution_error
                    # Add assistant's failed response and the error to the conversation
                    conversation_history.append({"role": "assistant", "content": llm_response_content}) # Add the response that generated bad SQL
                    conversation_history.append({
                        "role": "user",
                        "content": f"The following SQL code produced an error:\n```sql\n{generated_sql}\n```\nError message:\n{execution_error}\nPlease analyze the error and provide the corrected SQL query."
                    })
                    # Continue to the next attempt
                else:
                    # Success!
                    print("Query processed successfully.")
                    return result_data, None # Return the data (DataFrame or success message)

            except Exception as e:
                print(f"An unexpected error occurred during attempt {attempt + 1}: {e}")
                last_error = f"Agent Error: {str(e)}"
                # If the error was during the API call or processing, we might not have new SQL to show
                # Add a generic error message to the conversation
                conversation_history.append({
                    "role": "user",
                    "content": f"An internal error occurred in the system while processing the previous step: {str(e)}. Please review the initial request and provide the SQL query."
                })
                # Be cautious with loops after unexpected errors
                # break # Option: Stop if a non-SQL execution error occurs

        # If loop finishes without success
        print(f"\n--- Failed after {self.max_loops} attempts ---")
        return f"Failed to execute query after {self.max_loops} attempts. Last error: {last_error}\nLast Generated SQL:\n{generated_sql if generated_sql else 'N/A'}", last_error


# --- Example Usage ---
if __name__ == "__main__":
    if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
        print("Database connection details missing in environment variables.")
    else:
        # Create the agent instance
        agent = LLMDatabaseAgent(openai_client=client, db_conn_string=DB_CONNECTION_STRING)

        # Example Query (adjust to your schema)
        # user_task = "Show me the names and email addresses of all customers who live in London."
        # user_task = "What is the average order value?"
        # user_task = "List all tables in the database." # This tests if the LLM uses the schema info correctly
        user_task = "Count the number of products in the 'products' table." # Adjust table name

        # Process the query
        final_result, error = agent.process_query(user_task)

        print("\n--- Final Result ---")
        if error:
            print("Agent failed.")
            print(final_result) # Contains the error message
        elif isinstance(final_result, pd.DataFrame):
            print("Data:")
            print(final_result.to_string()) # Use to_string() to print full DataFrame
        else:
            print("Result:")
            print(final_result) # Could be a success message for DML/DDL