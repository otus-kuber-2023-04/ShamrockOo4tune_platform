# Домашняя работа №6. Мониторинг сервиса в кластере k8s

## Сборка кастомного образа  

Образ собирал на основе ДЗ №2.  
Добавил к конфигурации location basic_status  
Собирал образ командой с таким тэгом:  
```bash
docker build -t shamrockoo4tune/otus_k8s_hw1:v0.0.3 ./kubernetes-monitoring/image/
```
И разместил в dockerhub соответственно  

---  
<br>  

## Запуск приложегния в кластере

Через применение манифесов [deployment-nginx.yaml](/kubernetes-monitoring/deployment-nginx.yaml) и [svc-nginx.yaml](/kubernetes-monitoring/svc-nginx.yaml)  
Проверка работы приложения и правильности конфигурации deployment и svc через kubernetes-port-forwarder  
![1.png placeholder](/documentation/img/hw-6/1.png)  
