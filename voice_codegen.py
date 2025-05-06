from typing import Annotated, List, Union
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
import speech_recognition as sr
import pyttsx3
import os
import json
import subprocess
import shlex
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
load_dotenv()

# File-writing tool
@tool
def write_code(file_name: str, code: str) -> str:
    """Writes Python code to a specified file.
    
    Args:
        file_name: The path/filename to write to
        code: The Python code content to write
        
    Returns:
        A confirmation message with the file path
    """
    # Only create directory if path contains directory components
    if os.path.dirname(file_name):
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(code)
    return f"✅ Code written to {file_name}"

# File reading tool
@tool
def read_file(file_name: str) -> str:
    """Reads content from a specified file.
    
    Args:
        file_name: The path/filename to read from
        
    Returns:
        The content of the file
    """
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            content = f.read()
        return f"📄 Content of {file_name}:\n{content}"
    except FileNotFoundError:
        return f"❌ File not found: {file_name}"

# Execute Python code tool
@tool
def execute_python(code: str) -> str:
    """Executes Python code and returns the output.
    
    Args:
        code: The Python code to execute
        
    Returns:
        The output of the execution
    """
    import sys
    from io import StringIO
    import traceback
    
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    
    try:
        exec(code)
        sys.stdout = old_stdout
        return f"🚀 Execution result:\n{redirected_output.getvalue()}"
    except Exception as e:
        sys.stdout = old_stdout
        return f"❌ Execution error:\n{traceback.format_exc()}"

# List directory tool
@tool
def list_directory(path: str = ".") -> str:
    """Lists files in the specified directory.
    
    Args:
        path: The directory path to list (defaults to current directory)
        
    Returns:
        A list of files in the directory
    """
    try:
        files = os.listdir(path)
        return f"📁 Files in {path}:\n" + "\n".join(files)
    except Exception as e:
        return f"❌ Error listing directory: {str(e)}"

# Shell command execution tool
@tool
def run_command(cmd: str) -> str:
    """Executes a shell command and returns the output.
    
    Args:
        cmd: The shell command to execute
        
    Returns:
        The command output or error message
    """
    # List of potentially dangerous commands or patterns
    dangerous_patterns = [
        "rm -rf", "rmdir /s", "format", "mkfs", 
        "dd if=", "> /dev/", "chmod -R 777", 
        ":(){ :|:& };:", "> /etc/passwd"
    ]
    
    # Check if command contains dangerous patterns
    for pattern in dangerous_patterns:
        if pattern.lower() in cmd.lower():
            return f"❌ Potentially dangerous command detected: '{pattern}'. Command not executed for safety reasons."
    
    try:
        # Execute the command
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Set timeout for command execution (5 seconds)
        stdout, stderr = process.communicate(timeout=30)
        
        # Return the result
        if process.returncode == 0:
            if stdout.strip():
                return f"✅ Command executed successfully:\n{stdout}"
            else:
                return f"✅ Command executed successfully (no output)"
        else:
            return f"⚠️ Command returned error code {process.returncode}:\n{stderr}"
    except subprocess.TimeoutExpired:
        process.kill()
        return "❌ Command execution timed out after 30 seconds"
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"

# Groq LLM setup
llm = ChatOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama3-70b-8192",
)

# LangGraph state
class State(TypedDict):
    messages: Annotated[list, add_messages]
    history: List[Union[HumanMessage, AIMessage, ToolMessage]]

# System prompt for the assistant
SYSTEM_PROMPT = """You are a helpful voice-controlled programming assistant. 
You can write code, read files, execute Python code, and run shell commands to help users.
Always respond concisely and focus on the task at hand.

IMPORTANT: When asked to write a program, you should ALWAYS use the write_code tool.
For example, if the user says "write a program to sum 2 numbers in Python and save in add.py",
you should use write_code("add.py", "...python code here...").

Similarly, if asked to modify an existing file, first read it with read_file, then 
write the modified version with write_code.

Common voice command patterns to look for:
- "Write a program to..." → Create a new file with write_code
- "Create a script that..." → Create a new file with write_code
- "Modify the file..." → Read with read_file, then update with write_code
- "Change the code to..." → Read with read_file, then update with write_code
- "Run the program..." → Execute with either execute_python or run_command

You have the following tools at your disposal:
1. write_code(file_name, code): Write code to a specified file
2. read_file(file_name): Read content from a file
3. execute_python(code): Execute Python code directly
4. list_directory(path): List files in a directory
5. run_command(cmd): Execute shell commands to create folders, manipulate files, etc.

When executing shell commands:
- Use 'mkdir' to create directories
- Use 'echo' to write simple text to files
- Use 'cat', 'head', or 'tail' to view file contents
- Use 'mv', 'cp', or 'rm' for file operations
- Use 'touch' to create empty files

Be careful with commands that could be destructive.
Keep responses brief and focused on completing the requested task.
"""

def llm_node(state: State):
    # Add system message if it's a new conversation
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    # Add history if available
    if state.get("history"):
        messages.extend(state["history"])
    
    # Add current messages
    if state.get("messages"):
        messages.extend(state["messages"])
    
    # Process programming intent for clearer instructions to the LLM
    if state.get("messages") and isinstance(state["messages"][0], HumanMessage):
        user_message = state["messages"][0].content.lower()
        
        # Extract programming intent patterns
        programming_intents = {
            "write a program": "create a new file with appropriate code",
            "create a script": "create a new file with appropriate code",
            "make a program": "create a new file with appropriate code",
            "write code": "create appropriate code",
            "modify the file": "update an existing file",
            "change the code": "update an existing file",
            "fix the program": "update an existing file",
        }
        
        # Check if user message contains programming intents
        detected_intents = []
        for intent, description in programming_intents.items():
            if intent in user_message:
                detected_intents.append(f"'{intent}' → {description}")
        
        # If we detected programming intents, add a reminder message
        if detected_intents:
            reminder = (
                f"\nI detected the following programming intents in the user message:\n"
                f"{', '.join(detected_intents)}\n"
                f"\nRemember to use the write_code tool for file creation/modification."
            )
            messages.append(SystemMessage(content=reminder))
    
    # Debug output before LLM call
    print(f"📤 Sending {len(messages)} messages to LLM")
    for i, msg in enumerate(messages):
        print(f"  Message {i}: {type(msg).__name__} with {len(str(msg.content))} chars")
    
    # Invoke LLM
    response = llm.invoke(messages)
    print(f"📥 Received response from LLM: {type(response).__name__}")
    
    # Update history
    history = state.get("history", [])
    
    # Add current messages to history
    if state.get("messages"):
        history.extend(state["messages"])
    
    # Add response to history
    history.append(response)
    
    return {"messages": [response], "history": history}

# Text-to-speech function
def speak(text):
    # Clean text for better speech
    text = text.replace("```python", "").replace("```", "")
    
    # Initialize the TTS engine
    engine = pyttsx3.init()
    
    # Set properties
    engine.setProperty('rate', 180)  # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    # Split long text into manageable chunks
    max_chunk_length = 500
    chunks = [text[i:i+max_chunk_length] for i in range(0, len(text), max_chunk_length)]
    
    for chunk in chunks:
        engine.say(chunk)
        engine.runAndWait()

# Format LLM response for speech
def format_for_speech(response):
    content = response.content
    
    # If response has code blocks, mention it but don't read the code
    if "```" in content:
        # Get the text before any code block
        intro = content.split("```")[0].strip()
        return f"{intro} I've prepared the code for you and saved it."
    
    # If response is a tool call result, simplify it
    if "✅" in content and "Code written to" in content:
        # Extract the filename
        filename = content.split("Code written to")[1].strip()
        return f"I've created the {filename} file successfully."
        
    elif "✅" in content or "❌" in content or "📄" in content or "📁" in content or "🚀" in content:
        # Extract main message
        return content.split("\n")[0]
        
    return content

# Tool setup
tools = [write_code, read_file, execute_python, list_directory, run_command]
tool_node = ToolNode(tools=tools)

# Graph construction
builder = StateGraph(State)
builder.add_node("llm_node", RunnableLambda(llm_node))
builder.add_node("tool_node", tool_node)
builder.set_entry_point("llm_node")

# Conditional edge that properly handles tool calls
builder.add_conditional_edges(
    "llm_node",
    lambda x: "tool_node" if x["messages"] and x["messages"][-1].tool_calls else END,
)

# After tool execution, we want another LLM response to process tool results
builder.add_edge("tool_node", "llm_node")
graph = builder.compile()

# Add debug tracing
# graph.set_tracing(True)  # This will print detailed state transitions

# Voice input
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print("🎧 Recognizing...")
            text = recognizer.recognize_google(audio)
            print(f"🗣️ You said: {text}")
            
            # Process common programming-related terms that might be misheard
            text = text.replace("python", "Python")
            text = text.replace("javas script", "JavaScript")
            text = text.replace("coat", "code")
            text = text.replace("program", "program")
            text = text.replace("add dot pie", "add.py")
            text = text.replace("pi", "py")
            text = text.replace(" dot ", ".")
            
            return text
        except sr.WaitTimeoutError:
            print("❌ No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None
        except Exception as e:
            print("❌ Error:", str(e))
            return None

# Main execution
def run():
    print("🤖 Voice-controlled programming assistant initialized")
    print("📢 Say 'exit' or 'quit' to end the session")
    speak("Voice-controlled programming assistant ready. How can I help you today?")
    
    history = []
    
    while True:
        user_input = listen()
        if not user_input:
            speak("I didn't catch that. Please try again.")
            continue
            
        # Exit commands
        if user_input.lower() in ["exit", "quit", "goodbye", "bye"]:
            speak("Goodbye! Have a great day.")
            break
            
        messages = [HumanMessage(content=user_input)]
        
        try:
            # Process through LangGraph
            final_state = graph.invoke({"messages": messages, "history": history})
            
            # Debug print the final state
            print("\n🔍 Final state structure:")
            print(json.dumps({
                "messages_count": len(final_state.get("messages", [])),
                "history_count": len(final_state.get("history", [])),
                "message_types": [type(m).__name__ for m in final_state.get("messages", [])],
            }, indent=2))
            
            # First try to get the response from the messages key
            ai_message = None
            if final_state.get("messages"):
                for msg in reversed(final_state["messages"]):
                    if isinstance(msg, AIMessage):
                        ai_message = msg
                        break
            
            # If not found, try from history
            if not ai_message and final_state.get("history"):
                for msg in reversed(final_state["history"]):
                    if isinstance(msg, AIMessage):
                        ai_message = msg
                        break
            
            if ai_message:
                # Print the full response
                print("\n🤖 Assistant:", ai_message.content)
                
                # Speak a simplified version
                speech_text = format_for_speech(ai_message)
                speak(speech_text)
                
                # Update history for next iteration
                history = final_state["history"]
            else:
                print("❓ No AI response found in the final state")
                speak("I processed your request but couldn't generate a response. Please try again.")
            
        except Exception as e:
            print(f"❌ Error processing request: {str(e)}")
            import traceback
            traceback.print_exc()
            speak("I encountered an error processing your request. Please try again.")

if __name__ == "__main__":
    run()