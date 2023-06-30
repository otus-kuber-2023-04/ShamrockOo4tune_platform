# Домашняя работа №3. Сетевое взаимодействие Pod,взаимодействие Pod, сервисы  

## Часть 1. Работа с тестовым веб-приложением  
---  

> 1. Почему следующая конфигурация валидна, но не имеет смысла?  
>     ```yaml
>     livenessProbe:  
>       exec:  
>         command:  
>           - 'sh'  
>           - '-c'  
>           - 'ps aux | grep my_web_server_process  
>     ```
>>>      Ответ:  Потому что и без нее стандартная проверка liveness направдена на выяснение того факта, работает ли процесс с pid 1 - обычно он и есть my_web_server_process
   
> 2. Бывают ли ситуации, когда она все-таки имеет смысл?
>>>      Ответ:  Когда my_web_server_process не первый процесс в контейнере  

**`!!! Nota bene !!!` Хотелось бы получить эталонный ответ на эти вопросы**   

Выполнил:
1. Добавил probes в [web-pod.yaml](/kubernetes-networks/web-pod.yaml)
2. Создал deployment [web-deploy.yaml](/kubernetes-networks/web-deploy.yaml), исправил порт для **liveness probe**
3. Попрактиковал различные стратегии обновлений **RollingUpdate** c различными значениями **maxUnavailable** и **maxSurge**. Использовал [kubespy](/documentation/img/hw-3/1.png) для наблюдения
4. Создал [service web-svc-cip.yaml](/kubernetes-networks/web-svc-cip.yaml) типа ClusterIP  
5. Подключился по ssh в minikube  
5.1. Запросил индексную страницу по ClusterIP адресу сервиса;  
5.2. Убедился что ping в ClusterIP не будет работать;  
5.3. Доустановил в minikube пакет net-tools, проверил arp таблицы;  
5.4. проверил iptables и увидел там ClusterIP
6. Весь раздел "Включение IPVS" не осилил. Инструкции совершенно непонятные для неподготовленного по сетевой части человека. 
--- 
<br>  

## Часть 2. Работа с LoadBalancer и Ingress  

1. Руководствовался [официальной документацией MetalLB](https://metallb.org/)  
1.1. Установил режим IPVS для кластера: https://metallb.org/installation/#preparation  
1.2. Создал ресурсы MetalLB из [манифеста](https://raw.githubusercontent.com/metallb/metallb/v0.13.9/config/manifests/metallb-native.yaml)  
1.3. Создал пул IP адресов для назначения службам типа LoadBalancer из применением [манифеста объекта](/kubernetes-networks/metallb-ipaddresspool.yaml) типа IPAddressPool  
1.4. Создал сервис LoadBalancer для подов деплоймента
1.5. Проверил назначение внещнего IP:  
![/documents/img/hw-3/2.png placeholder](/documentation/img/hw-3/2.png)  
1.6. Определил IP адрес minikube:  
    ```bash
    anduser@shamil:~$ minikube ssh
    Last login: Sun May 21 08:52:03 2023 from 192.168.49.1
    docker@minikube:~$ ip addr show eth0
    48: eth0@if49: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
        link/ether 02:42:c0:a8:31:02 brd ff:ff:ff:ff:ff:ff link-netnsid 0
        inet 192.168.49.2/24 brd 192.168.49.255 scope global eth0
           valid_lft forever preferred_lft forever
    ```
    1.7. Добавил маршрут:  
    ```bash
    anduser@shamil:~$ sudo ip r a 172.17.255.0/24 via 192.168.49.2
    anduser@shamil:~$ ip r s
    default via 192.168.1.1 dev wlp1s0 proto dhcp metric 600 
    ... 
    172.17.255.0/24 via 192.168.49.2 dev br-9aef1587061f 
    ...  
    ```
    ![/documents/img/hw-3/3.png placeholder](/documentation/img/hw-3/3.png)    
---  
<br>  

## Часть 3. Задания со ⭐ DNS через MetalLB  
### Оригинальная формулировка задания:    
> * Сделайте сервис LoadBalancer, который откроет доступ к CoreDNS снаружи кластера (позволит получать записи через внешний IP). Например, nslookup web.default.cluster.local 172.17.255.10.  
> * Поскольку DNS работает по TCP и UDP протоколам - учтите это в
конфигурации. Оба протокола должны работать по одному и тому же IP-
адресу балансировщика.
> * Полученные манифесты положите в подкаталог ./coredns 

### Как я понял задание:  
> Получить разрешение доменного имени какого-либо сервиса в кластере при помощи утилиты nslookup находяь при этом вне кластера. Т.е. утилите nslookup нужно передать два параметра:
> 1. имя сервиса в кластере (пусть будет в FQDN формате)
> 2. внешне доступный IP сервиса "кластерного dns сервера" т.е. нужно прикрутить внешний IP к сервису kube-dns
>    ```bash
>    anduser@shamil:~$ k get svc --all-namespaces
>    NAMESPACE        NAME              TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)                  AGE
>    ...
>    kube-system      kube-dns          ClusterIP      10.96.0.10      <none>         53/UDP,53/TCP,9153/TCP   147m
>    ...
>    ```  

### Решение:  
1. Создаем сервис типа LoadBalancer с селектором как у сервиса kube-dns : **k8s-app: kube-dns** и аннотацией для назначения IP диапазона пула ранее заданных IP адресов: **metallb.universe.tf/loadBalancerIPs: 172.17.255.2** из подготовленного манифеста [kube-dns-lb-svc.yaml](/kubernetes-networks/coredns/kube-dns-lb-svc.yaml)  
2. Тестируем nslookup из хостовой системы:  
![/documents/img/hw-3/4.png placeholder](/documentation/img/hw-3/4.png)
---  
<br>  

## Часть 4. Создание Ingress  

1. Создал объекты из базового [манифеста](https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/baremetal/deploy.yaml)  
2. Создал сервис типа LoadBalancer для ingress из [манифеста nginx-lb.yaml](/kubernetes-networks/nginx-lb.yaml)  
3. Создал правило ингреса на основе [официальной документации](https://kubernetes.io/docs/concepts/services-networking/ingress/) из [манифеста web-ingress.yaml](/kubernetes-networks/web-ingress.yaml)    
![/documents/img/hw-3/5.png placeholder](/documentation/img/hw-3/5.png)  
---  
<br>  

## Часть 5. Задания со ⭐ | Ingress для Dashboard  

1. Установил Dashboard из [манифеста](kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml)  
2. Создаел сервисный аккаунт для доступа в дэшборд из манифеста [admin-user-sa.yaml](/kubernetes-networks/dashboard/admin-user-sa.yaml)  
3. Создал привязку кластерной роли [admin-user-crb.yaml](/kubernetes-networks/dashboard/admin-user-crb.yaml)  
4. Создал токен для пользователя admin-user:  
    ```bash
    anduser@shamil:~/ShamrockOo4tune_platform/kubernetes-networks$ k -n kubernetes-dashboard create token admin-user
    <вывод на экран: длинный токен>
    ```  
5. В отдельной сессии проксируем кластер на локальную машину для проверки: 
    ```bash
    anduser@shamil:~$ kubectl proxy
    Starting to serve on 127.0.0.1:8001
    ```
    ![/documents/img/hw-3/6.png placeholder](/documentation/img/hw-3/6.png)  
6. Применил правило ингресса [dashboard-ingress.yaml](/kubernetes-networks/dashboard/dashboard-ingress.yaml)  
7. Получается прокинуть дэшборд с пустым uri "/", но с /dashboard не открывается  

Нужен разбор  

---  
<br>  

## Часть 6. Задания со ⭐ | Canary 

Не осилил  
