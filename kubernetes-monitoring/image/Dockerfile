FROM nginx
USER 1001
COPY app /*.html /var/www/html/
COPY app/nginx.conf /etc/nginx/nginx.conf
COPY app/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 8000