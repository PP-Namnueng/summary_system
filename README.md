# 📚 Knowledge Summary System

สรุปความรู้จากหลายแหล่งด้วย AI | Summarize knowledge from multiple sources using AI

## ✨ Features

- 🎬 **YouTube** - Extract and summarize video transcripts
- 🌐 **Web Pages** - Summarize articles and blog posts  
- 📄 **PDF Files** - Extract and summarize PDF documents
- 📝 **Text** - Direct text input summarization
- 🇹🇭 **Thai Default** - Output summaries in Thai (configurable)
- 🤖 **Local LLM** - Uses Ollama for privacy-focused AI

## 🛠️ Prerequisites

1. **Python 3.10+**
2. **Ollama** - Local LLM runtime

### Install Ollama

```bash
# Windows (PowerShell)
winget install Ollama.Ollama

# Or download from https://ollama.ai
```

### Pull a Model

```bash
# Recommended models
ollama pull llama3.2
# or
ollama pull mistral
# or
ollama pull qwen2.5
```

## 🚀 Installation

1. **Clone/navigate to project directory**

```bash
cd C:\Users\PP\Desktop\Programming\summary
```

2. **Create virtual environment (recommended)**

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

## 📖 Usage

1. **Start Ollama** (if not running)

```bash
ollama serve
```

2. **Run the application**

```bash
streamlit run app.py
```

3. **Open browser** at `http://localhost:8501`

## 🎯 How to Use

### YouTube Videos
1. Select "🔗 URL (YouTube/Web)"
2. Paste YouTube URL
3. Click "📥 Extract Content"
4. Click "✨ Generate Summary"

### Web Pages
1. Select "🔗 URL (YouTube/Web)"
2. Paste article URL
3. Click "📥 Extract Content"
4. Click "✨ Generate Summary"

### PDF Files
1. Select "📄 PDF Upload"
2. Upload your PDF file
3. Click "📥 Extract Content"
4. Click "✨ Generate Summary"

### Direct Text
1. Select "📝 Text Input"
2. Paste your text
3. Click "✨ Generate Summary"

## ⚙️ Configuration

### Language
- Switch between Thai (🇹🇭) and English (🇬🇧) in the sidebar

### Model Selection
- Choose from available Ollama models in the sidebar

## 📁 Project Structure

```
summary/
├── app.py                  # Main Streamlit application
├── extractors/
│   ├── __init__.py
│   ├── youtube.py          # YouTube transcript extraction
│   ├── webpage.py          # Web page content extraction
│   └── pdf.py              # PDF text extraction
├── summarizer/
│   ├── __init__.py
│   └── ollama_client.py    # Ollama LLM integration
├── requirements.txt
└── README.md
```

## 🔧 Troubleshooting

### "Ollama Not Running"
```bash
ollama serve
```

### "No models found"
```bash
ollama pull llama3.2
```

### YouTube transcript not available
- Some videos have transcripts disabled
- Try videos with captions enabled

### PDF extraction issues
- Ensure PDF contains actual text (not scanned images)
- For scanned PDFs, OCR is not supported yet

## 📝 License

MIT License

## 🤝 Contributing

Feel free to submit issues and pull requests!
