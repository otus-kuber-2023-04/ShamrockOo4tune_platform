# Курсовая работа

Инфраструктурная платформа на основе kubernetes

## Создание кластера кубернетес

Создание кластера автоматизировано с использованием подхода IAC  
Установка производится терраформом из [репо](https://gitlab.com/shamrockoo4tune/iac-for-kubernetes-gitops) при помощи gitlab ci  
![img 1.png placeholder](/documentation/img/kursovoy_proekt/1.png)

Состояние tfstate хранится в s3

---
<br>

## cert-manager

cert-manager будет использован для выпуска сертификатов, обеспечение TLS 

```bash
# Установка cert-manager из чартов
$ helm repo add jetstack https://charts.jetstack.io
$ helm repo update
$ helm install cert-manager jetstack/cert-manager \
  -n cert-manager \
  --create-namespace \
  --version v1.12.0 \
  --set installCRDs=true

# Делегируем управление зоной в Selectel, 
# Создадим API ключ: https://my.selectel.ru/profile/apikeys
$ k apply -f kursovoy-proekt/SelectelSecret.yaml

# Selectel acme DNS webhook provider
$ helm repo add selectel https://selectel.github.io/cert-manager-webhook-selectel
$ helm repo update
$ helm install cert-manager-webhook-selectel selectel/cert-manager-webhook-selectel --namespace cert-manager --create-namespace

# cluster issuer с dns solver selectel
$ k apply -f kursovoy-proekt/ClusterIssuer.yaml
```

---
<br>

## Istio

Скачал и разархивировал [репо с Istio](https://github.com/istio/istio/releases/tag/1.18.2)  

Добавил бинарники Istio в $PATH:  
```bash
$ export PATH=$PATH:/home/anduser/ShamrockOo4tune_platform/kursovoy-proekt/istio-installation/istio-1.18.2/bin
$ istioctl version
no ready Istio pods in "istio-system"
1.18.2
```

Установка Istio с помощью istioctl:  
```bash
$ istioctl install
This will install the Istio 1.18.2 default profile with ["Istio core" "Istiod" "Ingress gateways"] components into the cluster. Proceed? (y/N) y
✔ Istio core installed                                                                                                          
✔ Istiod installed                                                                                                              
✔ Ingress gateways installed                                                                                                                                                  
✔ Installation complete                                                                                                                                                        Making this installation the default for injection and validation.
```

Istio IngressGateway в кластер:  
```bash
$ k -n istio-system get svc -l app=istio-ingressgateway
NAME                   TYPE           CLUSTER-IP       EXTERNAL-IP       PORT(S)                                      AGE
istio-ingressgateway   LoadBalancer   172.18.235.239   158.160.106.147   15021:32144/TCP,80:32130/TCP,443:31253/TCP   8m13s

# Доменное имя для кластера
$ host sgumerov.site
sgumerov.site has address 158.160.106.147
```

Всопользуемся примером микросервисного [приложения](https://github.com/GoogleCloudPlatform/microservices-demo/blob/main/release/kubernetes-manifests.yaml). Поместим манифесты в папку с istio-instalaltion

```bash
# Устанавливаем метку для размещения сайдкаров Istio в default namespace
$ k label ns default istio-injection=enabled
namespace/default labeled

# Деплоим приложение
$ k apply -f ./kursovoy-proekt/istio-installation/kubernetes-manifests.yaml 
deployment.apps/emailservice created
service/emailservice created
deployment.apps/checkoutservice created
service/checkoutservice created
deployment.apps/recommendationservice created
service/recommendationservice created
deployment.apps/frontend created
service/frontend created
service/frontend-external created
deployment.apps/paymentservice created
service/paymentservice created
deployment.apps/productcatalogservice created
service/productcatalogservice created
deployment.apps/cartservice created
service/cartservice created
deployment.apps/loadgenerator created
deployment.apps/currencyservice created
service/currencyservice created
deployment.apps/shippingservice created
service/shippingservice created
deployment.apps/redis-cart created
service/redis-cart created
deployment.apps/adservice created
service/adservice created
anduser@shamil:~/ShamrockOo4tune_platform$ 

# И убеждаемся что сайдкары Istio понялись
$ k get pods
NAME                                     READY   STATUS    RESTARTS   AGE
adservice-76b448fddf-l2lzr               2/2     Running   0          61s
cartservice-6969c94d94-fdrlk             2/2     Running   0          62s
checkoutservice-6d6f4d7cc7-w5g78         2/2     Running   0          63s
currencyservice-ccbc788bc-xzph5          2/2     Running   0          62s
emailservice-9f8578d69-q2zrh             2/2     Running   0          63s
frontend-846c85c54c-xtg9s                2/2     Running   0          63s
loadgenerator-7f8f5d8fb6-c6dh9           2/2     Running   0          62s
paymentservice-78549bfd9c-rq6jv          2/2     Running   0          63s
productcatalogservice-6b5dd45849-wpkgh   2/2     Running   0          63s
recommendationservice-cc746f6c7-nlfkq    2/2     Running   0          63s
redis-cart-6997b66668-w2rzb              2/2     Running   0          62s
shippingservice-7ccdfd8767-9xqg2         2/2     Running   0          62s
```  

Установка дополнений Istio:  
```bash
$ k apply -f kursovoy-proekt/istio-installation/istio-1.18.2/samples/addons
serviceaccount/grafana created
configmap/grafana created
service/grafana created
deployment.apps/grafana created
configmap/istio-grafana-dashboards created
configmap/istio-services-grafana-dashboards created
deployment.apps/jaeger created
service/tracing created
service/zipkin created
service/jaeger-collector created
serviceaccount/kiali created
configmap/kiali created
clusterrole.rbac.authorization.k8s.io/kiali-viewer created
clusterrole.rbac.authorization.k8s.io/kiali created
clusterrolebinding.rbac.authorization.k8s.io/kiali created
role.rbac.authorization.k8s.io/kiali-controlplane created
rolebinding.rbac.authorization.k8s.io/kiali-controlplane created
service/kiali created
deployment.apps/kiali created
serviceaccount/loki created
configmap/loki created
configmap/loki-runtime created
service/loki-memberlist created
service/loki-headless created
service/loki created
statefulset.apps/loki created
serviceaccount/prometheus created
configmap/prometheus created
clusterrole.rbac.authorization.k8s.io/prometheus created
clusterrolebinding.rbac.authorization.k8s.io/prometheus created
service/prometheus created
deployment.apps/prometheus created
```

---
<br>

## Выпуск tls сертификатов
Доступ в кластер организован через istio ingress gateway
Объект Gateway для кластера буду создавать в нэймспейсе istio-system, соответственно tls сертификаты нужно будет разместить там же
Платформенных сервисов будет много, поэтому выпускаем wildcard сертификат  
```bash
$ k apply -f kursovoy-proekt/Certificate.yaml

# Проверка
$ k -n istio-system get certificate
$ k -n istio-system get certificaterequests.cert-manager.io 
$ k -n istio-system get orders.acme.cert-manager.io
$ k -n istio-system get challenge
```

Убеждаемся что acme запись в зоне домена появилась  
![placeholder for img 2.png](/documentation/img/kursovoy_proekt/2.png)  

И ждем выпуска сертификата  
DNS challenge от letsencrypt может занять до часа времени  

```bash
k -n istio-system get certificate
NAME             READY   SECRET           AGE
sgumerov-certs   True    sgumerov-certs   78m

$ k -n istio-system get secrets
NAME              TYPE                DATA   AGE
istio-ca-secret   istio.io/ca-root    5      4h27m
sgumerov-certs    kubernetes.io/tls   2      22m
```

---
<br>

## Gateway и Virtual Services

Создаю в неймспейсе istio-system. Там же уже лежат сертификаты
```bash
$ k apply -f kursovoy-proekt/Gateway.yaml
```

Создаю виртуальные сервисы для различных сервисов плаформы:  
```bash
$ k apply -f kursovoy-proekt/vs-fronend.yaml
$ k apply -f kursovoy-proekt/vs-grafana.yaml
$ k apply -f kursovoy-proekt/vs-prometheus.yaml
$ k apply -f kursovoy-proekt/vs-kiali.yaml
```
Проверяем что сервисы доступны по https и что редайрект http --> https отрабатывает:  
![img 3.png placeholder](/documentation/img/kursovoy_proekt/3.png)
