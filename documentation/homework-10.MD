# GitOps и инструменты поставки

Домашнее задание №10

## GitLab

* Инфраструктурный репозиторий
  Согласно методических рекомендаций - инфраструктурный репозиторий размещен в GitLab: [iac-for-kubernetes-gitops](https://gitlab.com/shamrockoo4tune/iac-for-kubernetes-gitops)
* Репозиторий с копией приложения: [microservices-demo](https://gitlab.com/shamrockoo4tune/microservices-demo)   
  Dockerfiles приложений были дополнены утилитой **grpc_health_probe** для реализации probes  

---
<br>

## Создание Helm чартов

[Helm charts](/kubernetes-gitops/deploy/charts/) - были скопированы из [демонстрационного репозитория](https://gitlab.com/express42/kubernetes-platform-demo/microservices-demo/) и немного подрихтованы  

---
<br>

## Подготовка Kubernetes кластера | задание со ⭐

Кластер подготовлен в YC, раскатка производится terraform из [gitlab-ci пайплайна](https://gitlab.com/shamrockoo4tune/iac-for-kubernetes-gitops/-/blob/master/.gitlab-ci.yml) инфраструктурного репо

---
<br>

## Continuous Integration

Собрал и поместил в Docker Hub образы приложений с тегами на основе симантических версий:
![image 1.png placeholder](/documentation/img/hw-10/1.png)  

---
<br>

## Continuous Integration | задание со ⭐

Написал написал пайплайн для сборки новых образов приложений с тэгом по хешу коммита или по git tag - если есть. CI запускается только для тех сервисов, в директориях с которыми были измененеия  
![image 4.png placeholder](/documentation/img/hw-10/4.png)  
![image 5.png placeholder](/documentation/img/hw-10/5.png)  

---
<br>

## GitOps

### nginx-ingress

Установка по [официальной документации](https://kubernetes.github.io/ingress-nginx/deploy/):  
1. Установка реализации ингресс контроллера:
   ```bash
   $ helm upgrade --install ingress-nginx ingress-nginx \
      --repo https://kubernetes.github.io/ingress-nginx \
      --namespace ingress-nginx --create-namespace
   ```  
2. Получение IP облачного балансировщика ингресса:  
   ```bash
   $ kubectl -n ingress-nginx get svc ingress-nginx-controller 
   NAME                       TYPE           CLUSTER-IP       EXTERNAL-IP      PORT(S)                      AGE
   ingress-nginx-controller   LoadBalancer   172.18.240.113   158.160.44.211   80:30910/TCP,443:31706/TCP   2m20s
   ```
3. Привязываем доменное имя к внешнему IP балансировщика: 
   ```bash
   $ host shamrockoo4tune.ru
   shamrockoo4tune.ru has address 158.160.44.211
   ```
   
### cert-manager

Устанавливается согласно [официальной документации](https://cert-manager.io/docs/installation/helm/)  
1. Добавляем репо
   ```bash
   $ helm repo add jetstack https://charts.jetstack.io
   "jetstack" has been added to your repositories  
   $ helm repo update  
   ...
   Update Complete. ⎈Happy Helming!⎈
   ```
2. Установка CRD для cert-manager:
   ```bash
   $ kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.crds.yaml
   customresourcedefinition.apiextensions.k8s.io/certificaterequests.cert-manager.io created
   customresourcedefinition.apiextensions.k8s.io/certificates.cert-manager.io created
   customresourcedefinition.apiextensions.k8s.io/challenges.acme.cert-manager.io created
   customresourcedefinition.apiextensions.k8s.io/clusterissuers.cert-manager.io created
   customresourcedefinition.apiextensions.k8s.io/issuers.cert-manager.io created
   customresourcedefinition.apiextensions.k8s.io/orders.acme.cert-manager.io created
   ```
3. Установка чартов с cert-manager:
   ```bash
   $ helm install cert-manager jetstack/cert-manager \
      --namespace cert-manager \
      --create-namespace \
      --version v1.12.0
   ```
4. Проверка установки из чартов:
   ```bash
   $ kubectl get pods -n cert-manager
   NAME                                       READY   STATUS    RESTARTS   AGE
   cert-manager-584f85f6cf-q4h86              1/1     Running   0          4m18s
   cert-manager-cainjector-6c58576757-58svj   1/1     Running   0          4m18s
   cert-manager-webhook-75d68f6fb9-ppntn      1/1     Running   0          4m18s
   ```

5. Создаем ClusterIssuer для выпуска сертификатов LetsEncript из [манифеста](/kubernetes-gitops/cluster-issuer.yaml)
   ```bash
   k apply -f kubernetes-templating/chartmuseum/cluster-issuer.yaml 
   ```

### Тест правильности конфигурации ingress-nginx м certificate-manager

1. Создание тестового деплоймента и сервиса для проверки:  
   ```bash
   $ kubectl create ns demo
   $ kubectl create deployment demo -n demo --image=httpd --port=80
   $ kubectl expose deployment demo
   ```
2. Создаем правило ингресса на домене:
   ```bash
   $ kubectl apply -f kubernetes-gitops/demo_ingress_rule.yaml
   ```

3. Проверяем исправность ингресса:
   ```bash
   $ curl https://shamrockoo4tune.ru/demo
   <html><body><h1>It works!</h1></body></html>
   ```

### ArgoCD
1. Устанавливаем по [официальной документации](https://argo-cd.readthedocs.io/en/stable/getting_started/)
   ```bash
   $ kubectl create namespace argocd
   $ kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```
2. Без отделльного clusterIssuer выставить ингресс не получилось, поэтому применяем [манифест](/kubernetes-gitops/argocd-cluster-issuer.yaml)
   ```bash
   $ kubectl apply -f argocd-cluster-issuer.yaml
   ``` 

3. Создаем [правило ингресса](/kubernetes-gitops/argocd_ingress_rule.yaml) для доступа ArgoCD согласно ~~[официальной документации](https://argo-cd.readthedocs.io/en/stable/operator-manual/ingress/)~~ [примера из github](https://github.com/argoproj/argo-cd/discussions/11052#discussioncomment-4045945)
   ```bash
   $ kubectl apply -f argocd_ingress_rule.yaml
   ```

4. Установка ArgoCD cli  
  Согласно [официальной документации](https://argo-cd.readthedocs.io/en/stable/cli_installation/) 
   ```bash
   $ curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
   $ chmod u+x argocd-linux-amd64
   $ sudo mv argocd-linux-amd64 /usr/local/bin/argocd
   ```

5. Логин и смена пароля
   ````bash
   anduser@shamil:~$ argocd admin initial-password -n argocd
   wRljjylOMNytIrGL
  
    This password must be only used for first time login. We strongly recommend you update the password using `argocd account update-password`.
   anduser@shamil:~$ argocd login argocd.shamrockoo4tune.ru
   WARNING: server certificate had error: x509: certificate is valid for ingress.local, not argocd.shamrockoo4tune.ru. Proceed insecurely (y/n)? y
   WARN[0009] Failed to invoke grpc call. Use flag --grpc-web in grpc calls. To avoid this warning message, use flag --grpc-web. 
   Username: admin
   Password: 
   'admin:login' logged in successfully
   Context 'argocd.shamrockoo4tune.ru' updated
   anduser@shamil:~$ argocd account update-password
   WARN[0000] Failed to invoke grpc call. Use flag --grpc-web in grpc calls. To avoid this warning message, use flag --grpc-web. 
   *** Enter password of currently logged in user (admin): 
   *** Enter new password for user admin: 
   *** Confirm new password for user admin: 
   Password updated
   Context 'argocd.shamrockoo4tune.ru' updated
   ```
6. Применяем ресурсы [AppProject](/kubernetes-gitops/project.yaml) и  манифесты Application для приложений

7. Наблюдаем UI ArgoCD
   ![img 7.png placeholder](/documentation/img/hw-10/7.png)  

8. Идем в магазин
   ![img 8.png placeholder](/documentation/img/hw-10/8.png)
   
---
<br>

### Настройка автоматики CD 

Пайплайн CI после сборки и публикации образов, сборка которых была вызвана тэг пушем, публикует 

---
<br>

## Canary deployments с Flagger и Istio

### Установка istio при помощи istioctl
```bash
anduser@shamil:~/istio-1.18.1$ istioctl install --set profile=demo -y

The Kubernetes version v1.23.14 is not supported by Istio 1.18.1. The minimum supported Kubernetes version is 1.24.
Proceeding with the installation, but you might experience problems. See https://istio.io/latest/docs/setup/platform-setup/ for a list of supported versions.

✔ Istio core installed                                                          
✔ Istiod installed                                                              
✔ Egress gateways installed                                                     
✔ Ingress gateways installed                                                    
✔ Installation complete                                                         Making this installation the default for injection and validation.
```
---
<br>

### Установка Istio | Задание со ⭐  

Удаление istio установленного ранее  
```bash
anduser@shamil:~/istio-1.18.1$ istioctl uninstall --purge

The Kubernetes version v1.23.14 is not supported by Istio 1.18.1. The minimum supported Kubernetes version is 1.24.
Proceeding with the installation, but you might experience problems. See https://istio.io/latest/docs/setup/platform-setup/ for a list of supported versions.

All Istio resources will be pruned from the cluster
Proceed? (y/N) y
  ...
✔ Uninstall complete               
```

---
<br>

### Установка istio альтернативным способом 
Добавляем helm repo  
```bash
$ helm repo add istio https://istio-release.storage.googleapis.com/charts
$ helm repo update
$ kubectl create namespace istio-system
$ helm install istio-base istio/base -n istio-system --set defaultRevision=default

# проверка установки базовых сущностей (CRD): 
$ helm ls -n istio-system
NAME      	NAMESPACE   	REVISION	UPDATED                                	STATUS  	CHART      	APP VERSION
istio-base	istio-system	1       	2023-07-23 11:09:15.713386344 +0300 MSK	deployed	base-1.18.1	1.18.1     

# Установка дискавери чарта, который будет устанавливать istiod:
$ helm install istiod istio/istiod -n istio-system --wait

# проверка:
$ helm ls -n istio-system
NAME      	NAMESPACE   	REVISION	UPDATED                                	STATUS  	CHART        	APP VERSION
istio-base	istio-system	1       	2023-07-23 11:09:15.713386344 +0300 MSK	deployed	base-1.18.1  	1.18.1     
istiod    	istio-system	1       	2023-07-23 11:12:34.518371667 +0300 MSK	deployed	istiod-1.18.1	1.18.1 

$ helm status istiod -n istio-system
NAME: istiod
LAST DEPLOYED: Sun Jul 23 11:12:34 2023
NAMESPACE: istio-system
STATUS: deployed

# istio-ingressgateway
$ kubectl create namespace istio-ingress
$ helm install istio-ingressgateway istio/gateway -n istio-ingress
...

$ kubectl get deployments -n istio-system --output wide
NAME     READY   UP-TO-DATE   AVAILABLE   AGE     CONTAINERS   IMAGES                         SELECTOR
istiod   1/1     1            1           2m52s   discovery    docker.io/istio/pilot:1.18.1   istio=pilot

# prometheus
$ kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.18/samples/addons/prometheus.yaml
```

---
<br>

### Установка flagger  
```bash
$ helm repo add flagger https://flagger.app
"flagger" has been added to your repositories

$ k apply -f https://raw.githubusercontent.com/weaveworks/flagger/master/artifacts/flagger/crd.yaml
customresourcedefinition.apiextensions.k8s.io/canaries.flagger.app created
customresourcedefinition.apiextensions.k8s.io/metrictemplates.flagger.app created
customresourcedefinition.apiextensions.k8s.io/alertproviders.flagger.app created

$ helm upgrade --install flagger flagger/flagger \
> --namespace=istio-system \
> --set crd.create=false \
> --set meshProvider=istio \
> --set metricsServer=http://prometheus:9090
Release "flagger" does not exist. Installing it now.
NAME: flagger
LAST DEPLOYED: Sun Jul 23 11:19:43 2023
NAMESPACE: istio-system
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Flagger installed
```

Изменим маркировку namespace с приложением для istion sidecar injection:  
```bash
kubectl edit ns shop
namespace/shop edited

kubectl get ns shop --show-labels
NAME   STATUS   AGE     LABELS
shop   Active   7d18h   argocd=true,istio-injection=enabled,kubernetes.io/metadata.name=shop,project=shop
```

Обнулим поды 
```bash
$ kubectl delete pods --all -n shop
pod "adservice-c85458999-t2dfk" deleted
pod "cartservice-85d5764c66-zcfcd" deleted
pod "checkoutservice-757fdbdbf7-w2dzj" deleted
pod "currencyservice-56c754ff9f-rbmfv" deleted
pod "emailservice-6b75dc7b6c-mdcqr" deleted
pod "frontend-584b48d9c6-nqdsg" deleted
pod "loadgenerator-5bf59b7c57-pd9cf" deleted
pod "loadgenerator-7f9966dd67-r5xqh" deleted
pod "ob-cartservice-redis-master-0" deleted
pod "paymentservice-767d6bbff9-sdmms" deleted
pod "productcatalogservice-7dbbddf7dc-kf9jx" deleted
pod "recommendationservice-6d8ddf6f49-vg99s" deleted
pod "shippingservice-5c45fcdb77-vh4dx" deleted
```

---
<br> 

## Доступ к frontend 

Чтобы настроить маршрутизацию трафика к приложению с использованием Istio, необходимо добавить [ресурсы](/kubernetes-gitops/play_with_flagger/deploy/istio/) (frontend-vs.yaml, frontend-gw.yaml)  

Также предварительно (при установке istio в кластер) должен быть создан ресурс istio-ingressgateway   

Проверяем его наличие:
```bash
$ kubectl get svc istio-ingressgateway -n istio-ingress
NAME                   TYPE           CLUSTER-IP       EXTERNAL-IP     PORT(S)                                      AGE
istio-ingressgateway   LoadBalancer   172.18.188.205   130.193.48.92   15021:31111/TCP,80:31855/TCP,443:30139/TCP   3m37s
```
Его создание вызовет создание внешнего (облачного балансировщика)  
Теперь в shop можно зайти по http://\<EXTERNAL-IP\>  
![img 11.png placeholder](/documentation/img/hw-10/11.png)

Для экспериментов с flagger и istio изменим ресолвинг shop.shamrockoo4tune.ru на IP нового балансировщика   
```bash
$ nslookup shop.shamrockoo4tune.ru
Server:		127.0.0.53
Address:	127.0.0.53#53

Non-authoritative answer:
Name:	shop.shamrockoo4tune.ru
Address: 130.193.48.92
```

---
<br>

## Istio | Самостоятельное задание

Переносим ресурсы istio frontend-vs.yaml, frontend-gw.yaml в [чарты фронтэнда](https://gitlab.com/shamrockoo4tune/microservices-demo-cd/-/tree/main/deploy/charts/frontend) т.к. они логически являются частью инфраструктурного кода, описывающего окружение микросервиса frontend    
файлы c именами  
- gateway.yaml  
- virtualService.yaml  

Также не забыть внести ресурсы VirtualService и Gateway группы networking.istio.io как разрешенные в [appproject argocd](/kubernetes-gitops/project.yaml)  
После коммита ждем синхронизации и убеждаемся в подхвате новых типов ресурсов:  
![img 12.png placeholder](/documentation/img/hw-10/12.png)  

И проверяем сайт:  
![img 13.png placeholder](/documentation/img/hw-10/13.png)  

---
<br>

## Flagger | Canary
Создаем и применяем [манифест с canary](https://gitlab.com/shamrockoo4tune/microservices-demo-cd/-/tree/main/deploy/charts/frontend/templates/canary.yaml)  

Убеждаемся что проинициализирован:  
```bash
$ k get canary -n shop
NAME       STATUS        WEIGHT   LASTTRANSITIONTIME
frontend   Initialized   0        2023-07-23T13:36:16Z
```
Убеждаемся что canary добавил постфиксы подам фронтэнда:
```bash
$ kubectl get pods -n shop -l app=frontend-primary
NAME                               READY   STATUS    RESTARTS   AGE
frontend-primary-97c4d459c-96br2   2/2     Running   0          4m44s
```

И охоже что argocd не работает с флаггером вместе как надо
статус не меняется:  

![img 14.png placeholder](/documentation/img/hw-10/14.png)
```bash
$ kubectl describe canary frontend -n shop
Name:         frontend
Namespace:    shop
Labels:       app.kubernetes.io/instance=ob-frontend
Annotations:  <none>
API Version:  flagger.app/v1beta1
Kind:         Canary
Metadata:
  Creation Timestamp:  2023-07-23T15:45:36Z
  Generation:          1
  Managed Fields:
    API Version:  flagger.app/v1beta1
    Fields Type:  FieldsV1
    fieldsV1:
      f:metadata:
        f:annotations:
          .:
          f:kubectl.kubernetes.io/last-applied-configuration:
        f:labels:
          .:
          f:app.kubernetes.io/instance:
      f:spec:
        .:
        f:analysis:
          .:
          f:interval:
          f:maxWeight:
          f:metrics:
          f:stepWeight:
          f:threshold:
        f:provider:
        f:service:
          .:
          f:gateways:
          f:hosts:
          f:port:
          f:targetPort:
          f:trafficPolicy:
            .:
            f:tls:
              .:
              f:mode:
        f:targetRef:
          .:
          f:apiVersion:
          f:kind:
          f:name:
    Manager:      argocd-controller
    Operation:    Update
    Time:         2023-07-23T15:45:36Z
    API Version:  flagger.app/v1beta1
    Fields Type:  FieldsV1
    fieldsV1:
      f:status:
        .:
        f:canaryWeight:
        f:conditions:
        f:failedChecks:
        f:iterations:
        f:lastAppliedSpec:
        f:lastPromotedSpec:
        f:lastTransitionTime:
        f:phase:
        f:trackedConfigs:
    Manager:         flagger
    Operation:       Update
    Subresource:     status
    Time:            2023-07-23T15:46:16Z
  Resource Version:  357875
  UID:               09f22bf3-1a69-4b62-bf2a-cfd7d5025644
Spec:
  Analysis:
    Interval:    30s
    Max Weight:  30
    Metrics:
      Interval:   30s
      Name:       request-success-rate
      Threshold:  99
    Step Weight:  5
    Threshold:    5
  Provider:       istio
  Service:
    Gateways:
      frontend
    Hosts:
      *
    Port:         80
    Target Port:  8080
    Traffic Policy:
      Tls:
        Mode:  DISABLE
  Target Ref:
    API Version:  apps/v1
    Kind:         Deployment
    Name:         frontend
Status:
  Canary Weight:  5
  Conditions:
    Last Transition Time:  2023-07-23T15:47:16Z
    Last Update Time:      2023-07-23T15:47:16Z
    Message:               New revision detected, progressing canary analysis.
    Reason:                Progressing
    Status:                Unknown
    Type:                  Promoted
  Failed Checks:           0
  Iterations:              0
  Last Applied Spec:       7c8ff8db48
  Last Promoted Spec:      67565c8c6c
  Last Transition Time:    2023-07-23T15:52:46Z
  Phase:                   Progressing
  Tracked Configs:
Events:
  Type     Reason  Age                    From     Message
  ----     ------  ----                   ----     -------
  Warning  Synced  7m12s                  flagger  frontend-primary.shop not ready: waiting for rollout to finish: 0 out of 1 new replicas have been updated
  Normal   Synced  6m43s (x2 over 7m12s)  flagger  all the metrics providers are available!
  Normal   Synced  6m42s                  flagger  Initialization done! frontend.shop
  Normal   Synced  5m42s                  flagger  New revision detected! Scaling up frontend.shop
  Normal   Synced  42s (x10 over 5m12s)   flagger  Advance frontend.shop canary weight 5
  Normal   Synced  12s (x11 over 5m12s)   flagger  Starting canary analysis for frontend.shop

```



