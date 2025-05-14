# # from flask import Flask, render_template, request, jsonify
# # import io, contextlib

# # app = Flask(__name__)

# # @app.route('/')
# # def index():
# #     return render_template('index.html')

# # @app.route('/chat', methods=['POST'])
# # def chat():
# #     # 1) get the user message
# #     msg = request.json.get('message', '')

# #     # 2) here you would invoke your LLM agent to generate code.
# #     #    For now we'll just echo back and wrap it in a dummy code snippet.
# #     response_text = f"Received: {msg}"
# #     generated_code = (
# #         f"# Generated code for message: {msg!r}\n"
# #         "def hello():\n"
# #         "    print('Hello from your generated code!')\n"
# #         "\n"
# #         "hello()"
# #     )

# #     return jsonify({
# #         'response': response_text,
# #         'code': generated_code
# #     })


# # @app.route('/run', methods=['POST'])
# # def run_code():
# #     code = request.json.get('code', '')
# #     buf = io.StringIO()
# #     try:
# #         # capture stdout
# #         with contextlib.redirect_stdout(buf):
# #             exec(code, {})
# #         output = buf.getvalue()
# #     except Exception as e:
# #         output = f"Error: {e}"
# #     return jsonify({'output': output})


# # if __name__ == '__main__':
# #     # listen on all interfaces for intranet use
# #     app.run(host='0.0.0.0', port=5000, debug=True)
# from flask import Flask, render_template, request, jsonify
# import io, contextlib

# app = Flask(__name__)
# exec_counter = 0

# # Placeholder for user-defined functions:
# # - generate_response(msg) -> str
# # - generate_codes(msg) -> List[str]
# # - execute_sandbox(code_str) -> str

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/chat', methods=['POST'])
# def chat():
#     # 1) Get user message
#     msg = request.json.get('message', '')

#     # 2) Generate response text and list of code snippets
#     response_text = generate_response(msg)
#     code_list = generate_codes(msg)  # returns a list of Python code strings

#     # 3) Return response and code snippets
#     return jsonify({
#         'response': response_text,
#         'codes': code_list
#     })

# @app.route('/run', methods=['POST'])
# def run_code():
#     global exec_counter
#     # 1) Get single code snippet
#     snippet = request.json.get('code', '')
#     exec_counter += 1

#     # 2) Execute via user-defined sandbox
#     try:
#         raw_output = execute_sandbox(snippet)
#     except Exception as e:
#         raw_output = f"Error during sandbox execution: {e}"

#     # 3) Prefix with run number
#     output = f"Run #{exec_counter}:\n{raw_output.rstrip()}"

#     # 4) Return the execution result
#     return jsonify({'output': output})

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)



<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Intranet Chat + Code Runner</title>
  <style>
    body, html { margin: 0; height: 100%; font-family: sans-serif; }
    .container { display: flex; height: 100%; }

    /* Pane headers */
    .pane-header {
      display: flex;
      align-items: center;
      padding: 4px 10px;
      background: #eaeaea;
      border-bottom: 1px solid #ccc;
    }
    .pane-title {
      flex: 1;
      font-weight: bold;
      align-self: center;
    }
    .pane-header button {
      margin-left: 4px;
      padding: 2px 6px;
      font-size: 0.9rem;
    }

    /* Left chat pane */
    .chat-container {
      width: 50%;
      border-right: 1px solid #ccc;
      display: flex;
      flex-direction: column;
    }
    #chat {
      flex: 1;
      padding: 10px;
      overflow-y: auto;
      background: #f7f7f7;
    }
    .input-area {
      display: flex;
      padding: 10px;
      border-top: 1px solid #ccc;
    }
    .input-area input {
      flex: 1;
      padding: 8px;
      font-size: 1rem;
    }
    .input-area button {
      margin-left: 8px;
      padding: 8px 16px;
      font-size: 1rem;
    }

    /* Right code/result pane */
    .right-container {
      width: 50%;
      display: flex;
      flex-direction: column;
    }
    .pane {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .pane + .pane {
      border-top: 1px solid #ccc;
    }
    .content {
      flex: 1;
      padding: 10px;
      overflow-y: auto;
      background: #fdfdfd;
    }
    pre {
      background: #2d2d2d;
      color: #f8f8f2;
      padding: 10px;
      border-radius: 4px;
      margin-bottom: 10px;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Chat pane -->
    <div class="chat-container">
      <div class="pane-header">
        <span class="pane-title">Chat</span>
        <button id="chat-up">▲</button>
        <button id="chat-down">▼</button>
      </div>
      <div id="chat"></div>
      <div class="input-area">
        <input id="msg-input" type="text" placeholder="Type your message…" />
        <button id="run-btn">Run</button>
      </div>
    </div>

    <!-- Code / Result pane -->
    <div class="right-container">
      <div class="pane">
        <div class="pane-header">
          <span class="pane-title">Generated Code</span>
          <button id="code-up">▲</button>
          <button id="code-down">▼</button>
        </div>
        <div class="content" id="code-container">
          <!-- each run will append a <pre> block here -->
        </div>
      </div>
      <div class="pane">
        <div class="pane-header">
          <span class="pane-title">Execution Result</span>
          <button id="result-up">▲</button>
          <button id="result-down">▼</button>
        </div>
        <div class="content" id="result-container">
          <!-- each run will append a <pre> block here -->
        </div>
      </div>
    </div>
  </div>

  <script>
    const chatEl      = document.getElementById('chat');
    const inputEl     = document.getElementById('msg-input');
    const runBtn      = document.getElementById('run-btn');
    const codeCont    = document.getElementById('code-container');
    const resultCont  = document.getElementById('result-container');

    function appendChat(text, cls = '') {
      const p = document.createElement('p');
      p.textContent = text;
      if (cls) p.classList.add(cls);
      chatEl.appendChild(p);
      chatEl.scrollTop = chatEl.scrollHeight;
    }

    function appendPre(container, text) {
      const pre = document.createElement('pre');
      pre.textContent = text;
      container.appendChild(pre);
      container.scrollTop = container.scrollHeight;
    }

    function setupScroll(btnUpId, btnDownId, targetEl) {
      document.getElementById(btnUpId).addEventListener('click', () => {
        targetEl.scrollBy({ top: -100, behavior: 'smooth' });
      });
      document.getElementById(btnDownId).addEventListener('click', () => {
        targetEl.scrollBy({ top: 100, behavior: 'smooth' });
      });
    }

    // wire scroll buttons
    setupScroll('chat-up',   'chat-down',   chatEl);
    setupScroll('code-up',   'code-down',   codeCont);
    setupScroll('result-up', 'result-down', resultCont);

    runBtn.addEventListener('click', async () => {
      const msg = inputEl.value.trim();
      if (!msg) return;

      appendChat(`You: ${msg}`);
      inputEl.value = '';

      // 1) Fetch generated code & bot response
      const chatResp = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ message: msg })
      });
      const chatData = await chatResp.json();

      appendChat(`Bot: ${chatData.response}`, 'bot');

      // append (not replace) code
      appendPre(codeCont, chatData.code);

      // 2) run that code on the server
      const runResp = await fetch('/run', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ code: chatData.code })
      });
      const runData = await runResp.json();
      appendPre(resultCont, runData.output);
    });
  </script>
</body>
</html>