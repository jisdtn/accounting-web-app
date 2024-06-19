FROM node:19.5.0-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 7070
CMD ["npm", "run", "dev"]
