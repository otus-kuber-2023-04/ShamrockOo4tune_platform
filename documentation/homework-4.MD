# Volumes, Storages, StatefulSetStatefulSet  

## Часть 1. Установка и запуск Kind  

1. Установил [statefulset](/kubernetes-volumes/minio-statefulset.yaml) и [service](/kubernetes-volumes/minio-headless-service.yaml) согласно методических указаний.  
2. По ссылки из методических указаний консольный клиент mc не устанавливается, ссылки из репо не открываются, заявленные требования для сборки из исходников не выполняются. Устанавливил по [другой иснтрукции](https://min.io/docs/minio/linux/reference/minio-mc.html).   
---  
<br>  

## Часть 2. Задание со ⭐ 

1. Закодировал строки с "секретными значениями":  
    ```bash
    anduser@shamil:~$ echo -n 'minio' | base64
    bWluaW8=
    anduser@shamil:~$ echo -n 'minio123' | base64
    bWluaW8xMjM=
    ```  
2. Создал манифест для определения секретов:  
    ```bash
    anduser@shamil:~$ k create secret generic minio-keys --from-literal=access_key='bWluaW8=' --from-literal=secret_key='bWluaW8xMjM=' --dry-run=server -o yaml > minio-secrets.yaml 
    ```
3. Отредактировал [minio-secrets.yaml](/kubernetes-volumes/minio-secrets.yaml) и применил его.   

4. Обновил [манифест minio-statefulset.yaml](/kubernetes-volumes/minio-statefulset.yaml) для проброса переменных из секретов.  

5. Проверил наличие переменных внутри **pod**:  
    ```bash
    anduser@shamil:~/ShamrockOo4tune_platform$ k get pods
    NAME      READY   STATUS    RESTARTS   AGE
    minio-0   1/1     Running   0          4m8s
    anduser@shamil:~/ShamrockOo4tune_platform$ k exec -it minio-0 -- sh -c 'env | grep minio'
    HOSTNAME=minio-0
    MINIO_ACCESS_KEY=minio
    MINIO_SECRET_KEY=minio123
    ```  
