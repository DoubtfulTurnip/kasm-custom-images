FROM node:26-alpine

WORKDIR /usr/src/app

COPY package*.json ./
RUN apk add --no-cache firefox-esr && \
    npm ci --omit=dev --loglevel=error

COPY . .

ENV PORT=9005
EXPOSE 9005
ENTRYPOINT ["npm", "start", "--", "--docker"]
