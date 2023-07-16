# GitOps и инструменты поставки

Домашнее задание №10

## GitLab

* Инфраструктурный репозиторий
  Согласно методических рекомендаций - инфраструктурный репозиторий размещен в GitLab: [iac-for-kubernetes-gitops](https://gitlab.com/shamrockoo4tune/iac-for-kubernetes-gitops)
* Репозиторий с копией приложения: [microservices-demo](https://gitlab.com/shamrockoo4tune/microservices-demo)

---
<br>

## Создание Helm чартовСоздание Helm чарто

[Helm charts](/kubernetes-gitops/deploy/charts/) - были скопированы из [демонстрационного репозитория](https://gitlab.com/express42/kubernetes-platform-demo/microservices-demo/)

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

### Harbor
Потребуется репо с чартами
1. Добавим в Helm репо с Harbor
  ```bash
  $ helm repo add harbor https://helm.goharbor.io
  ```

2. Установим harbor c кастомизированными [Values](/kubernetes-gitops/harbor-values.yaml)
  ```bash
  $ helm install harbor harbor/harbor -f harbor-values.yaml --namespace harbor --create-namespace
  ``` 

3. В UI создаетм проект, копируем сертификат на машину, устанавливаем локально
  ```bash
  $ sudo cp ~/Downloads/ca.crt /usr/local/share/ca-certificates
  $ sudo update-ca-certificates
  ```
  
---
<br>  