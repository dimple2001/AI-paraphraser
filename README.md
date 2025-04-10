# AI-Paraphraser📝
Transform your text with AI assistance. The AI Paraphraser is a web-based tool that allows users to rewrite content in different tones and styles using AI. It supports multiple modes such as Fluency, Academic, Simple, and Creative to suit various rewriting needs.

## 🔍 Features

📝 Dual-pane layout: View Original Text and Modified Text side by side.

🧠 AI-Powered: Leverages advanced NLP models for context-aware paraphrasing.
📄 Sample Text: Insert predefined text for a quick demo.

📎 Character Limit: 1500 characters for input/output.

🌗 Clean and modern UI inspired by professional writing tools.

✨ Multiple Modes:

- Fluency – Natural-sounding paraphrasing

- Academic – Formal academic style

- Simple – Simplified language

- Creative – More expressive and imaginative

## 📁 Project Structure

```bash
├── index.html           # UI layout (Assigned to Viraj)
├── script.js            # Handles UI interactions (Vishal)
├── styles.css           # Custom styling (Dimple)
├── app.py               # Backend Flask server (Ayush)
├── requirements.txt     # Python dependencies (Vishal)
├── api.env              # API Key and environment variables (Ayush)
├── README.md            # Project documentation (Dimple)
├── ppt/                 # Presentation files (Dimple & Ayush)

```

### 🚀 How to Run
Clone the repository:

```bash
git clone https://github.com/dimple2001/AI-paraphraser

cd ai-paraphraser
```

Install dependencies:

```bash
pip install -r requirements.txt
```
Add your API key in  (locally in your root directory):
```bash 
api.env
```

Start the Flask server:

```bash
python app.py
```
### Team Members and Responsibilities


- Viraj    	Frontend HTML Layout

- Vishal	  JavaScript functionality, Requirements.txt 

- Dimple    CSS Styling, README, PPT

- Ayush   	Flask Backend, API Config, PPT


### Future Improvements
- Add user authentication

- Enable PDF/DOCX file input

- Dark mode toggle

