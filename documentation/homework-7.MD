# Операторы, CustomResourceDefinition

Домашнее задание №7  
Выполнил базу + 🐍 python KOPF логику. Также первое задание со 🌟  

---  
<br>  

## Подготовка  
Создал структуру каталогов и файлов в папке с домашим заданием (/kubernetes-controllers):  
.  
├── build  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── Dockerfile  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── mysql-operator.py  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── templates  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── backup-job.yml.j2  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── backup-pvc.yml.j2  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── backup-pv.yml.j2  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── mysql-deployment.yml.j2  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── mysql-pvc.yml.j2  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── mysql-pv.yml.j2  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ├── mysql-service.yml.j2  
│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; └── restore-job.yml.j2  
└── deploy  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── crd.yml  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── cr.yml  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── deploy-operator.yml  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── role-binding.yml  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── role.yml  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── service-account.yml  


Согласно методических указаний наполнил файлы содержимым c учетом обновлений `apiVersion`, запустил `minikube`  

---
<br>  

## Задание по CRD  
> "Если сейчас из описания mysql убрать строчку из спецификации, то
манифест будет принят API сервером. Для того, чтобы этого избежать,
добавьте описание обязательный полей в CustomResourceDefinition"

Добавил обязательные поля в описание [CRD](/kubernetes-operators/deploy/crd.yml):  
```yaml
...
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                database:
                  type: string
                  description: database name
                image:
                  type: string
                  description: image for MySQL
                password:
                  type: string
                  description: password for DB
                storage_size:
                  type: string
                  description: storage size
              required:
              - image
              - database
              - password
              - storage_size
...
```  

---
<br>  

## Операторы
Реализовывал на 🐍 по образцу из методических указаний с доработкой.  
Исходник: [mysql-operator.py](/kubernetes-operators/build/mysql-operator.py)  
Готовый образ оператора на DockerHub:  
```bash
$ docker pull shamrockoo4tune/mysqloperator:v1.1
```  
Применил манифесты [crd.yml](/kubernetes-operators/deploy/crd.yml) и [cr.yml](/kubernetes-operators/deploy/cr.yml), после запустил контролер:  
![img 1.png placeholder](/documentation/img/hw-7/1.png)  

> "Вопрос: почему объект создался, хотя мы создали CR, до того, как
запустили контроллер?"

> "Ответ: потому что контролер ищет соответствующие ему объекты  ('otus.homework', 'v1', 'mysqls') через API сервер и проверяет наличие своих аннотаций в метаданных подходящих объектов. После обработки ранее необработанных объектов добавляет свою аннотацию: `[default/mysql-instance] Patching with: {'metadata': {'finalizers': ['kopf.zalando.org/KopfFinalizerMarker']}}`"  

---
<br>  

## Проверка работы контролера  
1. Заполнение БД тестовыми данными
2. Удаление ресурса MySQL
3. Прверка удаления pv ресурса
4. Создание нового экземпляра MySQL
5. Ожидание восстановления состояния БД из бэкапа
![img 2.png placeholder](/documentation/img/hw-7/2.png)  

Аналогичная проверка при контролере, запущенным через deployment:  
![img 3.png placeholder](/documentation/img/hw-7/3.png)  

---
<br>  

## 🐍 Задание со 🌟 (1)

В коде [контролера](/kubernetes-operators/build/mysql-operator.py) добавил вывод переменной `message` в возврате из функции `mysql_on_create`:  
```py
return {'Message': message}
```  
`kopf` будет складывать в `Status` объекта любой `return` из соответствующим образом декорированных функций.

`message` определяется как резульат постановки джобы восстановления из бэкапа в очередь на исполнение:  
```py
    # Пытаемся восстановиться из backup
    api = kubernetes.client.BatchV1Api()
    try:
        api.create_namespaced_job('default', restore_job)
        message = 'mysql-instance created with restore-job'
    except kubernetes.client.rest.ApiException:
        message = 'mysql-instance created without restore-job'
        pass
```  
Проверяем значение `Status` экземпляра mysql:  
![img 4.png placeholder](/documentation/img/hw-7/4.png) 

---
<br>  

## 🐍 Задание со 🌟 (2)

Полностью не реализовано. 
Замена значения пароля в темплэйте связанных объектов происходит, но сам инстанс mysql продолжает пользоваться старым.

Реализовал в коде контролера как обработку события обновления через декоратор `@kopf.on.update`:  
```py
@kopf.on.update('otus.homework', 'v1', 'mysqls')
# Функция, которая будет запускаться при обновлении объектов типа MySQL:
def mysql_on_update_password(body, spec, status, **kwargs):
    password = spec.get('password', None)
    if not password:
        raise kopf.PermanentError(f"Password must be set. Got {password!r}.")
    name = status['mysql_on_create']['mysql-name']
    image = body['spec']['image']
    database = body['spec']['database']
    
    deployment = render_template(
        'mysql-deployment.yml.j2',
        {
            'name': name,
            'image': image,
            'password': password,
            'database': database
        }
    )

    api = kubernetes.client.AppsV1Api()
    obj = api.patch_namespaced_deployment(name=name, namespace='default', body=deployment)

    logging.info(f"MySQL deployment child is updated: {obj}")
```
