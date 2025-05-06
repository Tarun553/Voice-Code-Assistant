# Voice Code Assistant

A powerful voice-controlled programming assistant built with LangGraph, Groq's LLama3-70B model, and speech recognition that lets you write, modify, and execute code using just your voice.

## 🌟 Features

- **Voice Control**: Write code, create files, and execute commands just by speaking
- **Code Generation**: Write complete Python programs through voice commands
- **File Management**: Create, read, modify, and execute files with voice commands
- **Shell Integration**: Run shell commands to manage your filesystem
- **Context Awareness**: Maintains conversation history to understand complex requests

## 🛠️ Technology Stack

- **LangGraph**: Orchestration framework for managing LLM workflows
- **Groq's LLama3-70B**: High-performance LLM for generating code and understanding commands
- **SpeechRecognition**: Converts voice to text with high accuracy
- **pyttsx3**: Text-to-speech for vocal responses
- **Python Subprocess**: Safely executes shell commands

## 📋 Prerequisites

- Python 3.8+
- Groq API key
- Microphone access

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/voice-code-assistant.git
   cd voice-code-assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

## 📝 Usage

To start the voice assistant:

```bash
python voice_assistant.py
```

Once running, you can speak commands like:

- "Write a program to sum 2 numbers in Python and save in add.py"
- "Read the add.py file"
- "Modify add.py to multiply instead of add"
- "Create a folder called projects"
- "List files in the current directory"
- "Execute add.py"

## 🗣️ Voice Command Examples

### Creating Files
- "Write a program that calculates factorial in Python and save it as factorial.py"
- "Create a script that downloads images from URLs and save as downloader.py"

### Modifying Files
- "Read the content of factorial.py"
- "Modify factorial.py to handle negative numbers"
- "Fix the error in downloader.py"

### File Operations
- "Create a folder called project"
- "List files in the project folder"
- "Move factorial.py to the project folder"

### Execution
- "Execute factorial.py"
- "Run the Python script I just created"

## 🧰 Available Tools

The assistant comes with five powerful tools:

1. **write_code**: Writes code to a specified file
2. **read_file**: Reads content from a file
3. **execute_python**: Executes Python code directly
4. **list_directory**: Lists files in a directory
5. **run_command**: Executes shell commands

## 🛡️ Safety Features

- Dangerous shell commands are blocked
- Command execution has timeouts
- Comprehensive error handling

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Anthropic for LangGraph
- Groq for their powerful LLM API
- The open-source community for SpeechRecognition and pyttsx3
