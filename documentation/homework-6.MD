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

## Кластер
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ kind create cluster --config ./.ignore/kind.yml 
Creating cluster "kind" ...
 ✓ Ensuring node image (kindest/node:v1.26.3) 🖼
 ✓ Preparing nodes 📦 📦 📦 📦  
 ✓ Writing configuration 📜 
 ✓ Starting control-plane 🕹️ 
 ✓ Installing CNI 🔌 
 ✓ Installing StorageClass 💾 
 ✓ Joining worker nodes 🚜 
Set kubectl context to "kind-kind"
You can now use your cluster with:

kubectl cluster-info --context kind-kind

Thanks for using kind! 😊
```

---  
<br>  

## Запуск приложения в кластере

Через применение манифесов [deployment-nginx.yaml](/kubernetes-monitoring/deployment-nginx.yaml) и [svc-nginx.yaml](/kubernetes-monitoring/svc-nginx.yaml)  
Проверка работы приложения и правильности конфигурации deployment и svc через kubernetes-port-forwarder  
![1.png placeholder](/documentation/img/hw-6/1.png)  

```bash
anduser@shamil:~/ShamrockOo4tune_platform$ k apply -f ./kubernetes-monitoring/deployment-nginx.yaml 
deployment.apps/nginx created
anduser@shamil:~/ShamrockOo4tune_platform$ k apply -f ./kubernetes-monitoring/svc-nginx.yaml 
service/nginx created
```
---  
<br>  

## Запуск nginx-prometheus-exporter

В манифесте прописываем источник метрик - по **имени:порту** [сервиса nginx](/kubernetes-monitoring/svc-nginx.yaml)   
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ k apply -f ./kubernetes-monitoring/deployment-exporter.yaml 
deployment.apps/nginx-prometheus-exporter created
anduser@shamil:~/ShamrockOo4tune_platform$ k apply -f ./kubernetes-monitoring/svc-exporter.yaml 
service/nginx-prometheus-exporter created
```
---  
<br>  

## Prometheus operator
Применил манифест развертывания prometheus operator и сопутствующих ресурсов [С официального сайта](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md)

```bash
anduser@shamil:~/ShamrockOo4tune_platform$ LATEST=$(curl -s https://api.github.com/repos/prometheus-operator/prometheus-operator/releases/latest | jq -cr .tag_name)
prometheus-operator/prometheus-operator/releases/download/${LATEST}/bundle.yaml | kubectl create -f -anduser@shamil:~/ShamrockOo4tune_platform$ curl -sL https://github.com/prometheus-operator/prometheus-operator/releases/download/${LATEST}/bundle.yaml | kubectl create -f -
customresourcedefinition.apiextensions.k8s.io/alertmanagerconfigs.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/alertmanagers.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/podmonitors.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/probes.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/prometheusagents.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/prometheuses.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/prometheusrules.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/scrapeconfigs.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/servicemonitors.monitoring.coreos.com created
customresourcedefinition.apiextensions.k8s.io/thanosrulers.monitoring.coreos.com created
clusterrolebinding.rbac.authorization.k8s.io/prometheus-operator created
clusterrole.rbac.authorization.k8s.io/prometheus-operator created
deployment.apps/prometheus-operator created
serviceaccount/prometheus-operator created
service/prometheus-operator created
anduser@shamil:~/ShamrockOo4tune_platform$ kubectl wait --for=condition=Ready pods -l  app.kubernetes.io/name=prometheus-operator -n default
pod/prometheus-operator-6b8d85bc4c-5t4ph condition met
```
---  
<br>  

## Объект service monitor  

Натравливается на экспортера метрик по ярлыкам сервиса  
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ k apply -f ./kubernetes-monitoring/service-monitor.yaml 
servicemonitor.monitoring.coreos.com/nginx-prometheus-exporter created
```
---  
<br>  

## Установил объекты prometheus  

```bash
anduser@shamil:~/ShamrockOo4tune_platform$ k apply -f ./kubernetes-monitoring/prometheus.yaml 
serviceaccount/prometheus created
clusterrole.rbac.authorization.k8s.io/prometheus created
clusterrolebinding.rbac.authorization.k8s.io/prometheus created
prometheus.monitoring.coreos.com/prometheus created
service/prometheus created
```
![4.png placeholder](/documentation/img/hw-6/4.png)  

---  
<br>  

## Grafana, port-forwarder  
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ k apply -f ./kubernetes-monitoring/grafana.yaml 
persistentvolumeclaim/grafana-pvc created
deployment.apps/grafana created
service/grafana created
```

В UI Grafana указал url по имени сервиса:порту **http://prometheus:9090**  
Установил [официальный дэшборд](https://grafana.com/grafana/dashboards/12708-nginx/)  

Пробросил все сервисы на хост при помощи **kubernetes-port-forwarder**  
![3.png placeholder](/documentation/img/hw-6/3.png)  

Посоздавал нагрузку, наблюдал дэшборд:  
![2.png placeholder](/documentation/img/hw-6/2.png)
