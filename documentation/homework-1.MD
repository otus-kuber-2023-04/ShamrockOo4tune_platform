# Домашняя работа №1

## Часть 0. Подготовительная

### Вопрос:  

> *Разберитесь почему все pod в namespace kube-system восстановились
после удаления. Укажите причину в описании PR*  

![screenshot0](./img/hw-1/screenshot0.png)  

### Ответ:    
Поды в пространстве имен kube-system по своей природе делятся на обыкновенные (core-dns и kube-proxy) и на статичные (остальные).  
Статичные поды создаются из манифестов `/etc/kubernetes/manifests/` кублетом и восстанавливаются после удаления им же. Отследеить можно через `# journalctl -u kubelet` изнутри minicube.  
Обыкновенные поды мониторятся controller-manager, и воссоздаются (при необходимости) kubelet`ом.  

---
<br>  

## Часть 1. Веб сервер со статикой

Согласно методических рекомендаций собран веб сервер для раздачи статичных страниц (индексная страница по умолчанию, homework.html)

Сервер на базе официального образа [nginx](https://hub.docker.com/_/nginx) 

Кастомизированы конфигурационные файлы сервера для запуска контейнера с **`UID 1001`**, заменены пути к дефолтным страницам и корню виртуального хоста по умолчанию.


Собирается и запускается локально:
```bash
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-intro$ docker build -t shamrockoo4tune/otus_k8s_hw1:v0.0.2 ../documentation/files/hw-1
Sending build context to Docker daemon  8.192kB
Step 1/6 : FROM nginx
latest: Pulling from library/nginx
9e3ea8720c6d: Pull complete 
bf36b6466679: Pull complete 
15a97cf85bb8: Pull complete 
9c2d6be5a61d: Pull complete 
6b7e4a5c7c7a: Pull complete 
8db4caa19df8: Pull complete 
Digest: sha256:480868e8c8c797794257e2abd88d0f9a8809b2fe956cbfbc05dcc0bca1f7cd43
Status: Downloaded newer image for nginx:latest
 ---> 448a08f1d2f9
Step 2/6 : USER 1001
 ---> Running in 6ead7782070a
Removing intermediate container 6ead7782070a
 ---> 856ce0b9932a
Step 3/6 : COPY app /*.html /var/www/html/
 ---> ab410d507cba
Step 4/6 : COPY app/nginx.conf /etc/nginx/nginx.conf
 ---> 86cf1434a79c
Step 5/6 : COPY app/default.conf /etc/nginx/conf.d/default.conf
 ---> 57c7eace5408
Step 6/6 : EXPOSE 8000
 ---> Running in 7286c06d84d7
Removing intermediate container 7286c06d84d7
 ---> e793a1633a51
Successfully built e793a1633a51
Successfully tagged shamrockoo4tune/otus_k8s_hw1:v0.0.2
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-intro$ 
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-intro$ 
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-intro$ docker run -it --rm --name homework1 -p 8000:8000 shamrockoo4tune/otus_k8s_hw1:v0.0.2 
/docker-entrypoint.sh: /docker-entrypoint.d/ is not empty, will attempt to perform configuration
/docker-entrypoint.sh: Looking for shell scripts in /docker-entrypoint.d/
/docker-entrypoint.sh: Launching /docker-entrypoint.d/10-listen-on-ipv6-by-default.sh
10-listen-on-ipv6-by-default.sh: info: Getting the checksum of /etc/nginx/conf.d/default.conf
10-listen-on-ipv6-by-default.sh: info: /etc/nginx/conf.d/default.conf differs from the packaged version
/docker-entrypoint.sh: Launching /docker-entrypoint.d/20-envsubst-on-templates.sh
/docker-entrypoint.sh: Launching /docker-entrypoint.d/30-tune-worker-processes.sh
/docker-entrypoint.sh: Configuration complete; ready for start up

```

Страницы доступны локально:  
![screenshot1](/documentation/img/hw-1/screenshot1.png)  
<br>  


Собранный образ опубликован в dockerhub registry: [shamrockoo4tune/otus_k8s_hw1](https://hub.docker.com/r/shamrockoo4tune/otus_k8s_hw1)

Спулить:
```bash
$ docker pull shamrockoo4tune/otus_k8s_hw1
```
Деплой контейнеризированного приложения в k8s кластер на низкоуровневой абстракции (pod) через применение манифеста [/kubernetes-intro/web-pod.yaml](/kubernetes-intro/web-pod.yaml). Проброс портов на локальную машину:  

```bash
$ kubectl apply -f ./kubernetes-intro/web-pod.yaml
pod/web created
$ kubectl port-forward --address 0.0.0.0 pods/web 8000:8000
Forwarding from 0.0.0.0:8000 -> 8000
```
Переход на локацию /index.html отдает ожидаемую страницу:  
![screenshot2](/documentation/img/hw-1/screenshot2.png)   
<br>  

Также установил и освоил утилиту **kube-forwarder**  
Пробросил с ее помощью порт и проверил. Штука удобная.  
![screenshot3](/documentation/img/hw-1/screenshot3.png)  

---  
<br>  

## Часть 2. Фронтэнд часть Hipster Shop  

Склонировал [репо с Хипстерским магазином](https://github.com/GoogleCloudPlatform/microservices-demo) и контейреризировал фронтэнд:  
```bash  
~/microservices-demo/src/frontend$ docker build -t shamrockoo4tune/fe-hipstershop .
Sending build context to Docker daemon  4.452MB
Step 1/18 : FROM golang:1.20.
...
...
...
Successfully built 6f57bdf452aa
Successfully tagged shamrockoo4tune/fe-hipstershop:latest

~/microservices-demo/src/frontend$ docker push shamrockoo4tune/fe-hipstershop
...
```
Запуск в k8s:
```bash
~/microservices-demo/src/frontend$ cd ~/ShamrockOo4tune_platform/
~/ShamrockOo4tune_platform$ kubectl apply -f kubernetes-intro/frontend-pod-healthy.yaml 
pod/frontend created
~/ShamrockOo4tune_platform$ k get pods
NAME       READY   STATUS    RESTARTS   AGE
frontend   1/1     Running   0          18s
web        1/1     Running   0          24m
```

Ошибки в запуске контейнера были связаны с тем, что не были засэтены  некоторые переменные окружения. Проблема решается включением раздела **`env`** в спецификацию контейнера:  
```yaml
spec:
  containers:
  - image: shamrockoo4tune/fe-hipstershop
    name: frontend
    resources: {}
    env:
    - name: PRODUCT_CATALOG_SERVICE_ADDR
      value: "productcatalogservice:3550"
    - name: CURRENCY_SERVICE_ADDR
      value: "currencyservice:7000"
    - name: CART_SERVICE_ADDR
      value: "cartservice:7070"
    - name: RECOMMENDATION_SERVICE_ADDR
      value: "recommendationservice:8080"
    - name: SHIPPING_SERVICE_ADDR
      value: "shippingservice:50051"
    - name: CHECKOUT_SERVICE_ADDR
      value: "checkoutservice:5050"
    - name: AD_SERVICE_ADDR
      value: "adservice:9555"
  dnsPolicy: ClusterFirst
  restartPolicy: Never
```  
