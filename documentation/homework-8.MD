# Шаблонизация манифестов Kubernetes

Домашнее задание №8  

## Intro
Managed kubernetes кластер создал на YC облаке  
и настроил kubectl для работы с ним  
![img 1.png placeholder](/documentation/img/hw-8/1.png)  

---
<br>  

## Подготовка  
Установил HELM 3 и добавил `stable` репо  
![img 2.png placeholder](/documentation/img/hw-8/2.png)  

---
<br>  

## nginx-ingress

Установка по [официальной документации](https://kubernetes.github.io/ingress-nginx/deploy/):  
1. Установка реализации ингресс контроллера:
   ```bash
   $ helm upgrade --install ingress-nginx ingress-nginx \
      --repo https://kubernetes.github.io/ingress-nginx \
      --namespace ingress-nginx --create-namespace
   ```  
2. Создание тестового деплоймента и сервиса для проверки:  
   ```bash
   $ kubectl create deployment demo --image=httpd --port=80
   $ kubectl expose deployment demo
   ```
3. Получение IP облачного балансировщика ингресса:  
   ```bash
   $ kubectl -n ingress-nginx get svc ingress-nginx-controller 
   NAME                       TYPE           CLUSTER-IP     EXTERNAL-IP     PORT(S)                      AGE
   ingress-nginx-controller   LoadBalancer   10.96.193.10   158.160.46.90   80:30452/TCP,443:31596/TCP   21m
   ```
4. Привязываем доменное имя к внешнему IP  балансировщика: 
   ```bash
   $ host shamrockoo4tune.ru
   shamrockoo4tune.ru has address 158.160.46.90
   ```
5. Создаем правило ингресса на домене:
   ```bash
   $ kubectl create ingress demo --class=nginx --rule="shamrockoo4tune.ru/*=demo:80"
   ```
6. Проверяем исправность ингресса:
   ```bash
   $ curl http://shamrockoo4tune.ru
   <html><body><h1>It works!</h1></body></html>
   ```

---
<br>  

## cert-manager
Устанавливается согласно [официальной документации](https://cert-manager.io/docs/installation/helm/)  
1. Добавляем репо
   ```bash
   $ helm repo add jetstack https://charts.jetstack.io
   "jetstack" has been added to your repositories  
   $ helm repo update  
   Hang tight while we grab the latest from your chart repositories...  
   ...Successfully got an update from the "jetstack" chart repository
   ...Successfully got an update from the "ingress-nginx" chart repository
   ...Successfully got an update from the "stable" chart repository
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

---
<br>  

## Самостоятельное задание
Дополнительные ресурсы для работы с cert-manager  
1. Удалим ранее созданное правилло ингресса чтобы сделать вместо него новое, с tls.  
   ```bash
   $ kubectl delete ingress/demo
   ```
2. Необходимо создать объект [issuer](/kubernetes-templating/cert-manager/issuer.yaml), который выпускает сертификаты (для начала будем использовать самоподписные)  
   ```bash
   $ kubectl apply -f kubernetes-templating/cert-manager/issuer.yaml
   ```
3. Затем необходимо создать [правило ингресса](/kubernetes-templating/cert-manager/shamrockoo4tune-demo-ingress.yaml) (с указанием планируемого TLS - hostname и планируемого имени сертификата) и аннотировать его объектом issuer.    
   Issuer непрерывно мониторит ингрессы и при обнаружении правила ингресса с его именем в аннотации произведет выпуск сертификата на основании данных hosts и secretName из определения tls правила ингресса.  
4. Проверяем создание сертификата:  
   ```bash
   $ k get ingress/demo -o yaml
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     annotations:
       cert-manager.io/issuer: selfsigned-issuer
       kubectl.kubernetes.io/last-applied-configuration: |
         {"apiVersion":"networking.k8s.io/v1","kind":"Ingress","metadata":{"annotations":{"cert-manager.io/issuer":"selfsigned-issuer"},"name":"demo","namespace":"default"},"spec":{"ingressClassName":"nginx","rules":[{"host":"shamrockoo4tune.ru","http":{"paths":[{"backend":{"service":{"name":"demo","port":{"number":80}}},"path":"/","pathType":"Prefix"}]}}],"tls":[{"hosts":["shamrockoo4tune.ru"],"secretName":"shamrockoo4tune-selfsigned-cert"}]},"status":{"loadBalancer":{}}}
     creationTimestamp: "2023-06-18T08:06:47Z"
     generation: 1
     name: demo
     namespace: default
     resourceVersion: "2770316"
     uid: 96bb78e0-c368-4f29-9e28-a7feefcf2dde
   spec:
     ingressClassName: nginx
     rules:
     - host: shamrockoo4tune.ru
       http:
         paths:
         - backend:
             service:
               name: demo
               port:
                 number: 80
           path: /
           pathType: Prefix
     tls:
     - hosts:
       - shamrockoo4tune.ru
       secretName: shamrockoo4tune-selfsigned-cert
   status:
     loadBalancer:
       ingress:
       - ip: 158.160.46.90
   
   $ k get secrets
   NAME                              TYPE                                  DATA   AGE
   default-token-52p52               kubernetes.io/service-account-token   3      16d
   shamrockoo4tune-selfsigned-cert   kubernetes.io/tls                     3      23m
   ```
5. Проверяем доступ через ингресс по https:  
   ```bashm
   $ curl -k https://shamrockoo4tune.ru
   <html><body><h1>It works!</h1></body></html>
   ```

---
<br>  

## chartmuseum

1. Создаем ClusterIssuer для выпуска сертификатов LetsEncript из [манифеста](/kubernetes-templating/chartmuseum/cluster-issuer.yaml) 
   ```bash
   k apply -f kubernetes-templating/chartmuseum/cluster-issuer.yaml
   ```
2. Добавляем репо 
   ```bash
   $ helm repo add chartmuseum https://chartmuseum.github.io/charts
   $ helm repo update
   ```
2. Создаем кастомизированный [values.yaml](/kubernetes-templating/chartmuseum/values.yaml)
3. Устанавливаем chartmuseum с использованием values.yaml:  
   ```bash
   $ helm upgrade --install chartmuseum chartmuseum/chartmuseum --wait --namespace=chartmuseum -f kubernetes-templating/chartmuseum/values.yaml
   ```
4. Проверяем что chartmuseum установился и работает:  
   ![img 3.png placeholder](/documentation/img/hw-8/3.png)

---
<br>  

## chartmuseum | Задание со ⭐
Для того, чтобы можно было пользоваться самостоятельно задеплоенным chartmuseum репо, нужно добавить в [values файл](/kubernetes-templating/chartmuseum/values.yaml) явое разрешение на обработку локации **/api**:  
```yaml
env:
  open:
    # disable all routes prefixed with /api
    DISABLE_API: false
```
После деплоя с таким изменением, можно публиковать. Понадобится какой-нибудь готовый chart: 
```bash
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum$ helm create example-chart
Creating example-chart

anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum$ cd example-chart/

anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum/example-chart$ helm lint
==> Linting .
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum/example-chart$ helm package .
Successfully packaged chart and saved it to: /home/anduser/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum/example-chart/example-chart-0.1.0.tgz

anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum/example-chart$ curl --data-binary "@example-chart-0.1.0.tgz" https://chartmuseum.158.160.46.90.nip.io/api/charts
{"saved":true} 
```
Можно установить свой репо:  
```bash
$ helm repo add my-chartmuseum https://chartmuseum.158.160.46.90.nip.io/
"my-chartmuseum" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "my-chartmuseum" chart repository
...Successfully got an update from the "chartmuseum" chart repository
...Successfully got an update from the "jetstack" chart repository
...Successfully got an update from the "ingress-nginx" chart repository
...Successfully got an update from the "prometheus-community" chart repository
...Successfully got an update from the "stable" chart repository
Update Complete. ⎈Happy Helming!⎈
```  
И теперь его можно задеплоить:  
```bash
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum/example-chart$ k create ns example-chart
namespace/example-chart created

anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum/example-chart$ helm install example-chart my-chartmuseum/example-chart --namespace example-chart
/NAME: example-chart
LAST DEPLOYED: Sun Jun 18 17:15:03 2023
NAMESPACE: example-chart
STATUS: deployed
REVISION: 1
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace example-chart -l "app.kubernetes.io/name=example-chart,app.kubernetes.io/instance=example-chart" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace example-chart $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace example-chart port-forward $POD_NAME 8080:$CONTAINER_PORT

anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/chartmuseum/example-chart$ helm ls --namespace example-chart
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
example-chart   example-chart   1               2023-06-18 17:15:03.439317315 +0600 +06 deployed        example-chart-0.1.0     1.16.0  
```
Просмотреть хранящиеся чарты можно обращаясь к api
![img 4.png placeholder](/documentation/img/hw-8/4.png)

---
<br>  

## harbor
Самостоятельное задание  
Установить определенной версии (VERSION 1.1.2) харбор из определенного [репо](https://github.com/goharbor/harbor-helm)  
Т.к. версия чарта 1.1.2 использует устаревшие определения ресурсов:
```bash
anduser@shamil:~$ helm install harbor harbor/harbor -f ShamrockOo4tune_platform/kubernetes-templating/harbor/values.yaml --version 1.1.2 --namespace harbor
Error: INSTALLATION FAILED: unable to build kubernetes objects from release manifest: resource mapping not found for name: "harbor-harbor-ingress" namespace: "" from "": no matches for kind "Ingress" in version "extensions/v1beta1"
ensure CRDs are installed first
```
То устанавим актуальную версию:  
```bash
anduser@shamil:~$ helm repo add harbor https://helm.goharbor.io
"harbor" has been added to your repositories
anduser@shamil:~$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "chartmuseum" chart repository
...Successfully got an update from the "jetstack" chart repository
...Successfully got an update from the "ingress-nginx" chart repository
...Successfully got an update from the "harbor" chart repository
...Successfully got an update from the "prometheus-community" chart repository
...Successfully got an update from the "stable" chart repository
...Successfully got an update from the "my-chartmuseum" chart repository
Update Complete. ⎈Happy Helming!⎈ 
```

Устанавливаем harbor с кастомизированным [values](/kubernetes-templating/harbor/values.yaml)
```bash
anduser@shamil:~$ helm install harbor harbor/harbor -f ShamrockOo4tune_platform/kubernetes-templating/harbor/values.yaml --namespace harbor
NAME: harbor
LAST DEPLOYED: Mon Jun 19 20:55:10 2023
NAMESPACE: harbor
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Please wait for several minutes for Harbor deployment to complete.
Then you should be able to visit the Harbor portal at https://core.harbor.158.160.46.90.nip.io
For more details, please visit https://github.com/goharbor/harbor

anduser@shamil:~$ kubectl get pods -n harbor 
NAME                                 READY   STATUS    RESTARTS        AGE
harbor-core-69b684ccd-q9pgm          1/1     Running   0               5m6s
harbor-database-0                    1/1     Running   0               5m6s
harbor-jobservice-6bfcff6497-gtkqj   1/1     Running   2 (4m31s ago)   5m6s
harbor-portal-755ff69979-8t7px       1/1     Running   0               5m6s
harbor-redis-0                       1/1     Running   0               5m5s
harbor-registry-644cf6c886-ksjsm     2/2     Running   0               5m6s
harbor-trivy-0                       1/1     Running   0               5m5s
```
![img 5.png](/documentation/img/hw-8/5.png)

---
<br>

## Используем helmfile | Задание со ⭐

Скачиваем и устанавливаем бинарник helmfile:  
```bash
$ wget https://github.com/helmfile/helmfile/releases/download/v0.154.0/helmfile_0.154.0_linux_amd64.tar.gz
$ tar -xvzf tar -xvzf helmfile_0.154.0_linux_amd64.tar.gz
$ sudo chmod u+x helmfile
$ sudo mv helmfile /usr/local/bin/
```
Подготавливается helmfile, проверяем
```bash
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/helmfile$ helmfile list
NAME            NAMESPACE       ENABLED INSTALLED       LABELS  CHART                   VERSION
ingress-nginx   ingress-nginx   true    true                    ingress-nginx                  
cert-manager    cert-manager    true    true                    jetstack/cert-manager   v1.12.0
chartmuseum     chartmuseum     true    true                    chartmuseum/chartmuseum        
harbor          harbor          true    true                    harbor/harbor           1.12.2 
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/helmfile$ helmfile status
Getting status ingress-nginx
Getting status harbor
Getting status cert-manager
Getting status chartmuseum
NAME: chartmuseum
LAST DEPLOYED: Sun Jun 18 16:37:32 2023
NAMESPACE: chartmuseum
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
** Please be patient while the chart is being deployed **

Get the ChartMuseum URL by running:

  export POD_NAME=$(kubectl get pods --namespace chartmuseum -l "app=chartmuseum" -l "release=chartmuseum" -o jsonpath="{.items[0].metadata.name}")
  echo http://127.0.0.1:8080/
  kubectl port-forward $POD_NAME 8080:8080 --namespace chartmuseum

NAME: harbor
LAST DEPLOYED: Mon Jun 19 21:51:27 2023
NAMESPACE: harbor
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Please wait for several minutes for Harbor deployment to complete.
Then you should be able to visit the Harbor portal at https://core.harbor.158.160.46.90.nip.io
For more details, please visit https://github.com/goharbor/harbor

NAME: ingress-nginx
LAST DEPLOYED: Sun Jun 18 12:12:14 2023
NAMESPACE: ingress-nginx
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
The ingress-nginx controller has been installed.
It may take a few minutes for the LoadBalancer IP to be available.
You can watch the status by running 'kubectl --namespace ingress-nginx get services -o wide -w ingress-nginx-controller'

An example Ingress that makes use of the controller:
  apiVersion: networking.k8s.io/v1
  kind: Ingress
  metadata:
    name: example
    namespace: foo
  spec:
    ingressClassName: nginx
    rules:
      - host: www.example.com
        http:
          paths:
            - pathType: Prefix
              backend:
                service:
                  name: exampleService
                  port:
                    number: 80
              path: /
    # This section is only required if TLS is to be enabled for the Ingress
    tls:
      - hosts:
        - www.example.com
        secretName: example-tls

If TLS is enabled for the Ingress, a Secret containing the certificate and key must also be provided:

  apiVersion: v1
  kind: Secret
  metadata:
    name: example-tls
    namespace: foo
  data:
    tls.crt: <base64 encoded cert>
    tls.key: <base64 encoded key>
  type: kubernetes.io/tls

NAME: cert-manager
LAST DEPLOYED: Sun Jun 18 12:55:10 2023
NAMESPACE: cert-manager
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
cert-manager v1.12.0 has been deployed successfully!

In order to begin issuing certificates, you will need to set up a ClusterIssuer
or Issuer resource (for example, by creating a 'letsencrypt-staging' issuer).

More information on the different types of issuers and how to configure them
can be found in our documentation:

https://cert-manager.io/docs/configuration/

For information on how to configure cert-manager to automatically provision
Certificates for Ingress resources, take a look at the `ingress-shim`
documentation:

https://cert-manager.io/docs/usage/ingress/
```

---
<br>

## Создаем свой helm chart
Инициализируем структуру
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ helm create kubernetes-templating/hipster-shop
```
Шаблоны из templates удаляем, копируем all-hipster-shop.yaml из [интернетов](https://github.com/express42/otus-platform-snippets/blob/master/Module-04/05-Templating/manifests/all-hipster-shop.yaml)  
```bash
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating$ k create ns hipster-shop
namespace/hipster-shop created

anduser@shamil:~/ShamrockOo4tune_platform$ helm upgrade --install hipster-shop kubernetes-templating/hipster-shop --namespace hipster-shop
Release "hipster-shop" does not exist. Installing it now.
NAME: hipster-shop
LAST DEPLOYED: Thu Jun 22 17:30:15 2023
NAMESPACE: hipster-shop
STATUS: deployed
REVISION: 1
TEST SUITE: None

anduser@shamil:~/ShamrockOo4tune_platform$ k get nodes -o wide
NAME                        STATUS   ROLES    AGE   VERSION    INTERNAL-IP   EXTERNAL-IP      OS-IMAGE             KERNEL-VERSION      CONTAINER-RUNTIME
cl138kugqqnmku6vu9lj-olaf   Ready    <none>   21d   v1.23.14   10.128.0.32   158.160.100.69   Ubuntu 20.04.5 LTS   5.4.0-139-generic   containerd://1.6.18
```
![img 6.png placeholder](/documentation/img/hw-8/6.png)

### Вынесение frontend в отдельный чарт
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ helm create kubernetes-templating/frontend
Creating kubernetes-templating/frontend

anduser@shamil:~/ShamrockOo4tune_platform$ rm -rf ./kubernetes-templating/frontend/templates/* && rm ./kubernetes-templating/frontend/values.yaml
anduser@shamil:~/ShamrockOo4tune_platform$ touch ./kubernetes-templating/frontend/templates/{deployment.yaml,service.yaml,ingress.yaml}

# выносим определения микросервиса frontend во вновь созданные файлы

anduser@shamil:~/ShamrockOo4tune_platform$ helm upgrade --install hipster-shop kubernetes-templating/hipster-shop --namespace hipster-shop
Release "hipster-shop" has been upgraded. Happy Helming!
NAME: hipster-shop
LAST DEPLOYED: Thu Jun 22 17:53:47 2023
NAMESPACE: hipster-shop
STATUS: deployed
REVISION: 2
TEST SUITE: None

anduser@shamil:~/ShamrockOo4tune_platform$ helm upgrade --install frontend kubernetes-templating/frontend --namespace hipster-shop
Release "frontend" does not exist. Installing it now.
NAME: frontend
LAST DEPLOYED: Thu Jun 22 17:54:54 2023
NAMESPACE: hipster-shop
STATUS: deployed
REVISION: 1
TEST SUITE: None
```
![img 7.png placeholder](/documentation/img/hw-8/7.png)

Используем if conditional в определении сервиса для задания ключа nodePort только если тип сервиса определен как NodePort  
```yaml
    {{ if eq .Values.service.type "NodePort"  }}nodePort: {{ .Values.service.nodePort }}{{ end }}
```

---
<br>  

## Работа с helm-secrets | Необязательное задание

Установил sops - бинарник, helm-secrets плагин helm
Генерация ключа:  
```bash
gpg --full-generate-key
```
Просмотр ключей:  
```bash  
anduser@shamil:~/ShamrockOo4tune_platform$ gpg -k
/home/anduser/.gnupg/pubring.kbx
--------------------------------
pub   rsa3072 2023-06-26 [SC] [expires: 2024-06-25]
      < мой ID хэш >
uid           [ultimate] Shamil (-) <shamusg12345@gmail.com>
sub   rsa3072 2023-06-26 [E] [expires: 2024-06-25]
```  
создал [secrets.yaml](/kubernetes-templating/frontend/secrets.yaml)  
зашифровал:  
```bash
$ sops -e -i --pgp < мой ID хэш > secrets.yaml
```
Проверил что файл зашифрован  
Cоздал [манифест](/kubernetes-templating/frontend/templates/secret.yaml) с вызовом к секрету  

Практиковал установку с использованием secrets.yaml как values файла:  
```bash
$ helm secrets upgrade --install frontend kubernetes-templating/frontend --namespace
hipster-shop \
-f kubernetes-templating/frontend/values.yaml \
-f kubernetes-templating/frontend/secrets.yaml
```  
* Проверьте, что секрет создан, и его содержимое соответствует нашим
ожиданиям - ok  
* Предложите способ использования плагина helm-secrets в CI/CD - передавать пароли к базам данных при раскатки сервисов которые в эти БД должны ходить  
* Про что необходимо помнить, если используем helm-secrets (например, как обезопасить себя от коммита файлов с секретами, которые забыл зашифровать)? - нешифрованные файлы именовать по специальному шаблону (регулярке), который держать в .gitignore. После шифрованния файлы сохранять с именем, не подпадающим под регулярку.  

---
<br>

## Проверка
Создал файл [repo.sh](/kubernetes-templating/repo.sh)  

Публикация своих чартов в harbor:
```bash
$ helm package .
$ curl --data-binary "@<name>-chart-0.1.0.tgz" https://chartmuseum.158.160.46.90.nip.io/api/charts
```
В пользовательском интерфейсе harbor  создал пользователя, новый проект my-project и назначил в него этого пользователя.  
Скопировал сертификат из репозитория:
![img 8.png placeholder](/documentation/img/hw-8/8.png)

Произвел манипуляции с скопированным сертификатом:
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ sudo cp ~/Downloads/ca.crt /usr/local/share/ca-certificates
anduser@shamil:~/ShamrockOo4tune_platform$ sudo update-ca-certificates
Updating certificates in /etc/ssl/certs...
rehash: warning: skipping allianz.pem,it does not contain exactly one certificate or CRL
rehash: warning: skipping YandexInternalRootCA.pem,it does not contain exactly one certificate or CRL
rehash: warning: skipping ca-certificates.crt,it does not contain exactly one certificate or CRL
rehash: warning: skipping allianz.crt,it does not contain exactly one certificate or CRL
1 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...

Adding debian:ca.pem
done.
done.
anduser@shamil:~/ShamrockOo4tune_platform$ docker login core.harbor.158.160.46.90.nip.io
Username: shamil
Password: 
WARNING! Your password will be stored unencrypted in /home/anduser/.docker/config.json.
Configure a credential helper to remove this warning. See
https://docs.docker.com/engine/reference/commandline/login/#credentials-store

Login Succeeded
```
После этого стало возможным пушить чарты в harbor:
```bash
anduser@shamil:~/ShamrockOo4tune_platform$ helm push hipster-shop-0.1.0.tgz oci://core.harbor.158.160.46.90.nip.io/my-project
Pushed: core.harbor.158.160.46.90.nip.io/my-project/hipster-shop:0.1.0
Digest: sha256:0580ae8c1dc87b76410715ab3ef4d2970ef55a250a68caebf734cb926caa1e9f
anduser@shamil:~/ShamrockOo4tune_platform$ helm package kubernetes-templating/frontend/
Successfully packaged chart and saved it to: /home/anduser/ShamrockOo4tune_platform/frontend-0.1.0.tgz
anduser@shamil:~/ShamrockOo4tune_platform$ helm push frontend-0.1.0.tgz oci://core.harbor.158.160.46.90.nip.io/my-project
Pushed: core.harbor.158.160.46.90.nip.io/my-project/frontend:0.1.0
Digest: sha256:cefb4d7e556edf130a98f066c451e4e75b19ec6dc1ab677b7021412d10781fbf
```
---
<br>

## Kubecfg

Установил бинарник kubecfg  
Согдасно методических указаний создал [services.jsonnet](/kubernetes-templating/kubecfg/services.jsonnet)

Проапдейтил сервисы:
```bash
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/kubecfg$ kubecfg show services.jsonnet
---
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations: {}
  labels:
    name: paymentservice
  name: paymentservice
spec:
  minReadySeconds: 30
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      name: paymentservice
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      annotations: {}
      labels:
        name: paymentservice
    spec:
      containers:
      - args: []
        env:
        - name: PORT
          value: "50051"
        image: gcr.io/google-samples/microservices-demo/paymentservice:v0.1.3
        imagePullPolicy: IfNotPresent
        livenessProbe:
          exec:
            command:
            - /bin/grpc_health_probe
            - -addr=:50051
          initialDelaySeconds: 20
          periodSeconds: 15
        name: server
        ports:
        - containerPort: 50051
        readinessProbe:
          exec:
            command:
            - /bin/grpc_health_probe
            - -addr=:50051
          initialDelaySeconds: 20
          periodSeconds: 15
        resources:
          limits:
            cpu: 200m
            memory: 128Mi
          requests:
            cpu: 100m
            memory: 128Mi
        securityContext:
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 10001
        stdin: false
        tty: false
        volumeMounts: []
      imagePullSecrets: []
      initContainers: []
      terminationGracePeriodSeconds: 30
      volumes: []
---
apiVersion: v1
kind: Service
metadata:
  annotations: {}
  labels:
    name: paymentservice
  name: paymentservice
spec:
  ports:
  - name: grpc
    port: 50051
    targetPort: 5051
  selector:
    name: paymentservice
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations: {}
  labels:
    name: shippingservice
  name: shippingservice
spec:
  minReadySeconds: 30
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      name: shippingservice
  strategy:
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    type: RollingUpdate
  template:
    metadata:
      annotations: {}
      labels:
        name: shippingservice
    spec:
      containers:
      - args: []
        env:
        - name: PORT
          value: "50051"
        image: gcr.io/google-samples/microservices-demo/shippingservice:v0.1.3
        imagePullPolicy: IfNotPresent
        livenessProbe:
          exec:
            command:
            - /bin/grpc_health_probe
            - -addr=:50051
          initialDelaySeconds: 20
          periodSeconds: 15
        name: server
        ports:
        - containerPort: 50051
        readinessProbe:
          exec:
            command:
            - /bin/grpc_health_probe
            - -addr=:50051
          initialDelaySeconds: 20
          periodSeconds: 15
        resources:
          limits:
            cpu: 200m
            memory: 128Mi
          requests:
            cpu: 100m
            memory: 128Mi
        securityContext:
          readOnlyRootFilesystem: true
          runAsNonRoot: true
          runAsUser: 10001
        stdin: false
        tty: false
        volumeMounts: []
      imagePullSecrets: []
      initContainers: []
      terminationGracePeriodSeconds: 30
      volumes: []
---
apiVersion: v1
kind: Service
metadata:
  annotations: {}
  labels:
    name: shippingservice
  name: shippingservice
spec:
  ports:
  - name: grpc
    port: 50051
    targetPort: 5051
  selector:
    name: shippingservice
  type: ClusterIP
anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-templating/kubecfg$ kubecfg update services.jsonnet --namespace hipster-shop
INFO  Validating deployments paymentservice
INFO  validate object "apps/v1, Kind=Deployment"
INFO  Validating services paymentservice
INFO  validate object "/v1, Kind=Service"
INFO  Validating deployments shippingservice
INFO  validate object "apps/v1, Kind=Deployment"
INFO  Validating services shippingservice
INFO  validate object "/v1, Kind=Service"
INFO  Fetching schemas for 4 resources
INFO  Creating services paymentservice
INFO  Creating services shippingservice
INFO  Creating deployments paymentservice
INFO  Creating deployments shippingservice
```

---
<br>

## Kustomize 
сам не осилил, скопировано
