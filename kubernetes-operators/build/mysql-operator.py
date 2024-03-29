import kopf
import yaml
import kubernetes
import time
from jinja2 import Environment, FileSystemLoader
from yaml.loader import SafeLoader
import logging
import time

def render_template(filename, vars_dict):
    env = Environment(loader=FileSystemLoader('./templates'))
    template = env.get_template(filename)
    yaml_manifest = template.render(vars_dict)
    json_manifest = yaml.load(yaml_manifest, Loader=yaml.SafeLoader)
    return json_manifest

def delete_success_jobs(mysql_instance_name):
    api = kubernetes.client.BatchV1Api()
    jobs = api.list_namespaced_job('default')
    for job in jobs.items:
        jobname = job.metadata.name
        if (jobname == f"backup-{mysql_instance_name}-job") or (jobname == f"restore-{mysql_instance_name}-job"):
            if job.status.succeeded:
                api.delete_namespaced_job(
                    jobname,
                    'default',
                    propagation_policy='Background'
                )

def wait_until_job_end(jobname):
    api = kubernetes.client.BatchV1Api()
    job_finished = False
    jobs = api.list_namespaced_job('default')
    while (not job_finished) and any(job.metadata.name == jobname for job in jobs.items):
        time.sleep(1)
        jobs = api.list_namespaced_job('default')
        for job in jobs.items:
            if job.metadata.name == jobname:
                if job.status.succeeded == 1:
                    job_finished = True

@kopf.on.create('otus.homework', 'v1', 'mysqls')
# Функция, которая будет запускаться при создании объектов тип MySQL:
def mysql_on_create(body, spec, **kwargs):
    name = body['metadata']['name']
    image = body['spec']['image'] # cохраняем в переменные содержимое описания MySQL из CR
    password = body['spec']['password']
    database = body['spec']['database']
    storage_size = body['spec']['storage_size']
    logging.info(f"A handler is called with body: {body}")

    # Генерируем JSON манифесты для деплоя
    persistent_volume = render_template(
        'mysql-pv.yml.j2',
        {
            'name': name,
            'storage_size': storage_size
        }
    )
    persistent_volume_claim = render_template(
        'mysql-pvc.yml.j2',
        {
            'name': name,
            'storage_size': storage_size
        }
    )
    service = render_template(
        'mysql-service.yml.j2',
        {
            'name': name
        }
    )
    deployment = render_template(
        'mysql-deployment.yml.j2',
        {
            'name': name,
            'image': image,
            'password': password,
            'database': database
        }
    )
    restore_job = render_template(
        'restore-job.yml.j2',
        {
            'name': name,
            'image': image,
            'password': password,
            'database': database
        }
    )
    backup_pv = render_template(
        'backup-pv.yml.j2',
        {
            'name': name
        }
    )
    backup_pvc = render_template(
        'backup-pvc.yml.j2',
        {
            'name': name,
            'storage_size': storage_size
        }
    )

    # Определяем, что созданные ресурсы являются дочерними к управляемому CustomResource:
    kopf.append_owner_reference(persistent_volume_claim, owner=body) # addopt
    kopf.append_owner_reference(service, owner=body)
    kopf.append_owner_reference(deployment, owner=body)
    kopf.append_owner_reference(persistent_volume, owner=body)
    kopf.append_owner_reference(restore_job, owner=body)
    # ^ Таким образом при удалении CR удалятся все, связанные с ним pv,pvc,svc, deployments
    
    api = kubernetes.client.CoreV1Api()
    # Создаем mysql PV:
    api.create_persistent_volume(persistent_volume)
    # Создаем mysql PVC:
    api.create_namespaced_persistent_volume_claim('default', persistent_volume_claim)
    # Создаем mysql SVC:
    api.create_namespaced_service('default', service)
    # Создаем mysql Deployment:
    api = kubernetes.client.AppsV1Api()
    obj = api.create_namespaced_deployment('default', deployment)
    # Cоздаем PVC и PV для бэкапов:
    api = kubernetes.client.CoreV1Api()
    try:    
        api.create_persistent_volume(backup_pv)
    except kubernetes.client.rest.ApiException:
        pass
    try:
        api.create_namespaced_persistent_volume_claim('default', backup_pvc)
    except kubernetes.client.rest.ApiException:
        pass
    
    # Пытаемся восстановиться из backup
    api = kubernetes.client.BatchV1Api()
    try:
        api.create_namespaced_job('default', restore_job)
        message = 'mysql-instance created with restore-job'
    except kubernetes.client.rest.ApiException:
        message = 'mysql-instance created without restore-job'
        pass
    
    return {
        'Message': message,
        'mysql-name': obj.metadata.name
    }

@kopf.on.delete('otus.homework', 'v1', 'mysqls')
def delete_object_make_backup(body, **kwargs):
    name = body['metadata']['name']
    image = body['spec']['image']
    password = body['spec']['password']
    database = body['spec']['database']

    persistent_volume = render_template(
        'mysql-pv.yml.j2',
        {
            'name': name
        }
    )
    delete_success_jobs(name)

    # Cоздаем backup job:
    api = kubernetes.client.BatchV1Api()
    backup_job = render_template(
        'backup-job.yml.j2',
        {
            'name': name,
            'image': image,
            'password': password,
            'database': database
        }
    )
    api.create_namespaced_job('default', backup_job)
    wait_until_job_end(f"backup-{name}-job")

    api = kubernetes.client.CoreV1Api()
    api.delete_persistent_volume(persistent_volume['metadata']['name'])

    return {'message': "mysql and its children resources deleted"}

# Такое решение поменяет deployment и дочерние объекты, т.о. что переменные окружения будут содержать новый пароль, но
# в базе пароль не изменился. как заходит со старым, так и заходит
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
