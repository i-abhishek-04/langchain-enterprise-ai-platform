# Browser AI Playground

An interactive React/Vite frontend for direct calls to selected model-provider APIs and a local prompt simulator. The playground itself does not execute LangChain chains; the backend document Q&A workflow uses LangChain LCEL for Groq calls.

---

## ✨ Features

- **Provider calls:** Direct browser requests to Groq, OpenRouter, and local Ollama. Availability, pricing, and model access depend on each provider and account.
- **Local prompt simulation:** Shows a clearly labeled placeholder and does not call a model.
- **Illustrative flow diagram:** Shows a possible prompt/model/parser composition; it is not an executing LangChain chain.
- **Prompt Library:** Pre-loaded template collection for ReAct Agents, RAG Context Q&A, Structured Output JSON extraction, and LCEL chains.
- **Python Code Exporter:** Generates sample LangChain code for the current prompt configuration; the generated code is not executed by this frontend.
- **Performance Metrics:** Reports elapsed time and approximate token counts based on streamed text chunks.
- **Client-Side Security:** API keys are stored exclusively in `localStorage` and sent directly to official provider APIs.

---

## 🛠️ Quickstart & Development

### Prerequisites
- Node.js `v18+` (v24 supported)
- npm `v9+`

### Running Locally
```bash
# Navigate to the app directory
cd apps/free-ai-playground

# Install dependencies
npm install

# Launch development server
npm run dev
```

Open **`http://localhost:3000`** in your browser.

### Production Build
```bash
npm run build
```
The compiled static assets will be output to the `dist/` directory.

---

## 🔑 Getting Free API Keys

The local prompt simulator requires no API key. For live provider calls, configure credentials in Settings:

- **Groq Console:** [console.groq.com/keys](https://console.groq.com/keys)
- **OpenRouter:** [openrouter.ai/keys](https://openrouter.ai/keys)
- **Ollama:** [ollama.com](https://ollama.com) (local installation required)
