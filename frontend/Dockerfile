FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 7070
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


#FROM node:lts-alpine
#WORKDIR /app
#ENV PATH /app/node_modules/.bin:$PATH
#
#RUN npm install @vue/cli@5.0.8 -g
#
#COPY package.json .
#COPY package-lock.json .
#RUN npm install
#
#CMD ["npm", "run", "serve"]
