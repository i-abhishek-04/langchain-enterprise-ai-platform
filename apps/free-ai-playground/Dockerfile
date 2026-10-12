FROM node:20-alpine

WORKDIR /app

COPY . .

RUN if [ -f package.json ]; then \
        npm ci || npm install; \
    elif [ -f apps/free-ai-playground/package.json ]; then \
        cp -r apps/free-ai-playground/* . && \
        (npm ci || npm install); \
    fi

ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

EXPOSE 3000

CMD ["sh", "-c", "npm run preview -- --host 0.0.0.0 --port ${PORT:-3000} --strictPort"]
