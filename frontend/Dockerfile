FROM node:20-alpine

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm install

# Copy application source code
COPY . .

# Expose Next.js dev/prod port
EXPOSE 3000

# Run Next.js in development mode with hot reload
CMD ["npm", "run", "dev"]
