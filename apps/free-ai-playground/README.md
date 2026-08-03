# 🦜 LangChain Free AI Studio & Model Playground

An interactive web application built with React and Vite that allows developers to test, visualize, and experiment with LangChain prompts, chains, and agents using **100% free-tier AI model providers** and local LLMs.

---

## ✨ Features

- **6 Free-Tier AI Engines Supported:**
  1. **Groq Cloud:** Ultra-fast streaming for `Llama 3.3 70B`, `DeepSeek R1 Distill 70B`, and `Mixtral 8x7B`.
  2. **Google Gemini:** `Gemini 2.0 Flash` & `Gemini 1.5 Flash` with generous free daily API limits.
  3. **OpenRouter (Free Tier):** Access to free models (`Llama 3.2 11B Vision:free`, `Gemma 2 9B:free`, `DeepSeek R1:free`).
  4. **HuggingFace Inference:** Serverless inference for `Qwen 2.5 Coder 32B` and `Llama 3.1 8B`.
  5. **Local Ollama:** Offline connection to `http://localhost:11434` for local models (e.g. `llama3`, `mistral`, `deepseek-r1`).
  6. **Zero-Config Browser Fallback:** Client-side simulation mode allowing instant testing with 0 API keys!

- **LCEL Chain Flow Visualizer:** Visual flowchart mapping `ChatPromptTemplate` → `LLM Engine` → `StrOutputParser`.
- **Prompt Library:** Pre-loaded template collection for ReAct Agents, RAG Context Q&A, Structured Output JSON extraction, and LCEL chains.
- **Python Code Exporter:** Generate 1-click runnable Python LangChain code snippets for any prompt configuration.
- **Performance Metrics:** Real-time token generation speed (tokens/sec), duration in milliseconds, and total token counters.
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

You can test the app immediately with zero keys using the **Browser AI Fallback** mode, or grab a free key from any of these official providers:

- **Groq Console (Fastest):** [console.groq.com/keys](https://console.groq.com/keys)
- **Google AI Studio (Gemini):** [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **OpenRouter Free Keys:** [openrouter.ai/keys](https://openrouter.ai/keys)
