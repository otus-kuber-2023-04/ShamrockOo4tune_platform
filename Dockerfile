FROM nginx
USER 1001
COPY app /app
COPY app/nginx.conf /etc/nginx/nginx.conf
EXPOSE 80