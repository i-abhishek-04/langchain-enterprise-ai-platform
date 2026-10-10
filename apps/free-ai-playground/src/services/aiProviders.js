// Direct browser provider calls and a local prompt-only simulator.

export const PROVIDERS = {
  groq: {
    id: 'groq',
    name: 'Groq Cloud',
    description: 'Chat completions through the Groq API',
    badge: 'Remote API',
    apiKeyRequired: true,
    keyUrl: 'https://console.groq.com/keys',
    models: [
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile' },
      { id: 'deepseek-r1-distill-llama-70b', name: 'DeepSeek R1 Distill (70B)' },
      { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B (32k context)' },
      { id: 'llama3-8b-8192', name: 'Llama 3 8B' },
    ]
  },
  openrouter: {
    id: 'openrouter',
    name: 'OpenRouter',
    description: 'Chat completions through the OpenRouter API',
    badge: 'Remote API',
    apiKeyRequired: true,
    keyUrl: 'https://openrouter.ai/keys',
    models: [
      { id: 'meta-llama/llama-3.2-11b-vision-instruct:free', name: 'Llama 3.2 11B Vision (Free)' },
      { id: 'google/gemma-2-9b-it:free', name: 'Gemma 2 9B (Free)' },
      { id: 'deepseek/deepseek-r1:free', name: 'DeepSeek R1 (Free)' },
      { id: 'qwen/qwen-2.5-coder-32b-instruct:free', name: 'Qwen 2.5 Coder 32B (Free)' },
    ]
  },
  ollama: {
    id: 'ollama',
    name: 'Local Ollama',
    description: 'Runs 100% locally on your computer (No API key needed)',
    badge: 'Offline & Local',
    apiKeyRequired: false,
    keyUrl: 'https://ollama.com',
    models: [
      { id: 'llama3', name: 'Llama 3 (Local)' },
      { id: 'mistral', name: 'Mistral (Local)' },
      { id: 'deepseek-r1', name: 'DeepSeek R1 (Local)' },
      { id: 'phi3', name: 'Phi-3 (Local)' },
    ]
  },
  browser: {
    id: 'browser',
    name: 'Local Prompt Simulator',
    description: 'Displays a local placeholder; no model is called',
    badge: 'Simulation',
    apiKeyRequired: false,
    keyUrl: '#',
    models: [
      { id: 'langchain-agent-sim', name: 'Prompt Simulation' },
      { id: 'js-code-assistant', name: 'Prompt Simulation' }
    ]
  }
};

/**
 * Stream or call AI model response across selected provider
 */
export async function streamCompletion({
  providerId,
  modelId,
  apiKey,
  systemPrompt,
  userPrompt,
  temperature = 0.7,
  maxTokens = 1000,
  onChunk,
  onFinish,
  onError
}) {
  const startTime = performance.now();
  let accumulated = '';
  let tokenCount = 0;

  try {
    // 1. Groq Provider
    if (providerId === 'groq') {
      if (!apiKey) throw new Error('Groq API Key is required. Please set it in Settings.');

      const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: modelId,
          messages: [
            ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
            { role: 'user', content: userPrompt }
          ],
          temperature: parseFloat(temperature),
          max_tokens: parseInt(maxTokens),
          stream: true
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error?.message || `Groq API Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            try {
              const data = JSON.parse(line.slice(6));
              const delta = data.choices[0]?.delta?.content || '';
              if (delta) {
                accumulated += delta;
                tokenCount += 1;
                onChunk(accumulated);
              }
            } catch (e) {
              // ignore partial line parse
            }
          }
        }
      }
    }
    // 2. OpenRouter Provider
    else if (providerId === 'openrouter') {
      if (!apiKey) throw new Error('OpenRouter API Key required. Set it in Settings.');

      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json',
          'HTTP-Referer': 'http://localhost:3000',
          'X-Title': 'LangChain Free AI Playground'
        },
        body: JSON.stringify({
          model: modelId,
          messages: [
            ...(systemPrompt ? [{ role: 'system', content: systemPrompt }] : []),
            { role: 'user', content: userPrompt }
          ],
          temperature: parseFloat(temperature),
          max_tokens: parseInt(maxTokens),
          stream: true
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error?.message || `OpenRouter Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            try {
              const data = JSON.parse(line.slice(6));
              const delta = data.choices[0]?.delta?.content || '';
              if (delta) {
                accumulated += delta;
                tokenCount += 1;
                onChunk(accumulated);
              }
            } catch (e) {}
          }
        }
      }
    }
    // 3. Local Ollama Provider
    else if (providerId === 'ollama') {
      const response = await fetch('http://localhost:11434/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: modelId,
          system: systemPrompt,
          prompt: userPrompt,
          stream: true,
          options: { temperature: parseFloat(temperature) }
        })
      });

      if (!response.ok) {
        throw new Error(`Could not connect to local Ollama at localhost:11434. Is Ollama running?`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(Boolean);
        for (const line of lines) {
          try {
            const data = JSON.parse(line);
            if (data.response) {
              accumulated += data.response;
              tokenCount += 1;
              onChunk(accumulated);
            }
          } catch (e) {}
        }
      }
    }
    // 4. Local simulation mode; no model or LangChain chain is executed.
    else {
      const simText = `[Local Prompt Simulation — no model was called]

System Prompt: "${systemPrompt || 'Default System Prompt'}"

Input:
${userPrompt}

This placeholder text was generated locally. It is not an AI-generated answer.`;

      const words = simText.split(' ');
      for (let i = 0; i < words.length; i++) {
        await new Promise((r) => setTimeout(r, 25));
        accumulated += (i === 0 ? '' : ' ') + words[i];
        tokenCount = i + 1;
        onChunk(accumulated);
      }
    }

    const endTime = performance.now();
    const durationMs = Math.round(endTime - startTime);
    const tokensPerSec = Math.round((tokenCount / (durationMs / 1000)) * 10) / 10 || 25.4;

    onFinish({
      text: accumulated,
      durationMs,
      tokensPerSec,
      totalTokens: tokenCount
    });

  } catch (err) {
    onError(err.message || 'An error occurred while generating completion.');
  }
}
