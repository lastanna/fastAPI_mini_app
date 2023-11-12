# для nginx docker container
FROM nginx:1.21.1-alpine

COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/certificate/server.crt /etc/ssl/certificate/server.crt
COPY nginx/certificate/server.key /etc/ssl/certificate/server.key