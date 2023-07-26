# Хранилище секретов для приложений. Vault 

Домашнее задание №11  

## Инсталляция hashicorp vault HA в k8sHA в k8s  

Cклонируем репозитории c consul и vault, подготовим consul-values.yaml и vault-values.yaml и произведем установку    
```bash
$ git clone https://github.com/hashicorp/consul-helm.git
$ helm upgrade --install consul consul-helm -f consul-values.yaml --atomic --create-namespace -n consul
$ git clone https://github.com/hashicorp/vault-helm.git
$ helm upgrade --install vault vault-helm -f vault-values.yaml --atomic --create-namespace -n vault

# Проверака:  
$ helm status vault -n vault
NAME: vault
LAST DEPLOYED: Wed Jul 26 18:43:40 2023
NAMESPACE: vault
STATUS: deployed
REVISION: 1
...

$ kubectl -n vault logs vault-0
==> Vault server configuration:

             Api Address: http://172.17.133.71:8200
                     Cgo: disabled
         Cluster Address: https://vault-0.vault-internal:8201
   Environment Variables: GODEBUG, HOME, HOSTNAME, HOST_IP, KUBERNETES_PORT, KUBERNETES_PORT_443_TCP, KUBERNETES_PORT_443_TCP_ADDR, KUBERNETES_PORT_443_TCP_PORT, KUBERNETES_PORT_443_TCP_PROTO, KUBERNETES_SERVICE_HOST, KUBERNETES_SERVICE_PORT, KUBERNETES_SERVICE_PORT_HTTPS, NAME, PATH, POD_IP, PWD, SHLVL, SKIP_CHOWN, SKIP_SETCAP, VAULT_ACTIVE_PORT, VAULT_ACTIVE_PORT_8200_TCP, VAULT_ACTIVE_PORT_8200_TCP_ADDR, VAULT_ACTIVE_PORT_8200_TCP_PORT, VAULT_ACTIVE_PORT_8200_TCP_PROTO, VAULT_ACTIVE_PORT_8201_TCP, VAULT_ACTIVE_PORT_8201_TCP_ADDR, VAULT_ACTIVE_PORT_8201_TCP_PORT, VAULT_ACTIVE_PORT_8201_TCP_PROTO, VAULT_ACTIVE_SERVICE_HOST, VAULT_ACTIVE_SERVICE_PORT, VAULT_ACTIVE_SERVICE_PORT_HTTP, VAULT_ACTIVE_SERVICE_PORT_HTTPS_INTERNAL, VAULT_ADDR, VAULT_AGENT_INJECTOR_SVC_PORT, VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP, VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_ADDR, VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_PORT, VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_PROTO, VAULT_AGENT_INJECTOR_SVC_SERVICE_HOST, VAULT_AGENT_INJECTOR_SVC_SERVICE_PORT, VAULT_AGENT_INJECTOR_SVC_SERVICE_PORT_HTTPS, VAULT_API_ADDR, VAULT_CLUSTER_ADDR, VAULT_K8S_NAMESPACE, VAULT_K8S_POD_NAME, VAULT_PORT, VAULT_PORT_8200_TCP, VAULT_PORT_8200_TCP_ADDR, VAULT_PORT_8200_TCP_PORT, VAULT_PORT_8200_TCP_PROTO, VAULT_PORT_8201_TCP, VAULT_PORT_8201_TCP_ADDR, VAULT_PORT_8201_TCP_PORT, VAULT_PORT_8201_TCP_PROTO, VAULT_SERVICE_HOST, VAULT_SERVICE_PORT, VAULT_SERVICE_PORT_HTTP, VAULT_SERVICE_PORT_HTTPS_INTERNAL, VAULT_STANDBY_PORT, VAULT_STANDBY_PORT_8200_TCP, VAULT_STANDBY_PORT_8200_TCP_ADDR, VAULT_STANDBY_PORT_8200_TCP_PORT, VAULT_STANDBY_PORT_8200_TCP_PROTO, VAULT_STANDBY_PORT_8201_TCP, VAULT_STANDBY_PORT_8201_TCP_ADDR, VAULT_STANDBY_PORT_8201_TCP_PORT, VAULT_STANDBY_PORT_8201_TCP_PROTO, VAULT_STANDBY_SERVICE_HOST, VAULT_STANDBY_SERVICE_PORT, VAULT_STANDBY_SERVICE_PORT_HTTP, VAULT_STANDBY_SERVICE_PORT_HTTPS_INTERNAL, VAULT_UI_PORT, VAULT_UI_PORT_8200_TCP, VAULT_UI_PORT_8200_TCP_ADDR, VAULT_UI_PORT_8200_TCP_PORT, VAULT_UI_PORT_8200_TCP_PROTO, VAULT_UI_SERVICE_HOST, VAULT_UI_SERVICE_PORT, VAULT_UI_SERVICE_PORT_HTTP, VERSION
              Go Version: go1.20.5
              Listener 1: tcp (addr: "[::]:8200", cluster address: "[::]:8201", max_request_duration: "1m30s", max_request_size: "33554432", tls: "disabled")
               Log Level: 
                   Mlock: supported: true, enabled: false
           Recovery Mode: false
                 Storage: consul (HA available)
                 Version: Vault v1.14.0, built 2023-06-19T11:40:23Z
             Version Sha: 13a649f860186dffe3f3a4459814d87191efc321

2023-07-26T15:44:02.749Z [INFO]  proxy environment: http_proxy="" https_proxy="" no_proxy=""
2023-07-26T15:44:02.749Z [WARN]  storage.consul: appending trailing forward slash to path
2023-07-26T15:44:02.754Z [INFO]  core: Initializing version history cache for core
==> Vault server started! Log data will stream in below:

2023-07-26T15:44:10.292Z [INFO]  core: security barrier not initialized
2023-07-26T15:44:10.293Z [INFO]  core: seal configuration missing, not initialized
...

```

---
<br>

## Инициализируем vault
### * 🐍 поэкспериментируйте с разными значениями --key-shares --key-threshold

```bash
$ k exec -n vault -it vault-0 -- vault operator init --key-shares=3 --key-threshold=2
Unseal Key 1: C2vhGijP/T8Zdz9D+sDHoZaL5LT9UmY5JcouS3LUvbaF
Unseal Key 2: Rqmr+PfXh6OwhEOnOLwUbprPAVOS9KmXN2NdYUTDGzvG
Unseal Key 3: 16u7z5mGNUXJei5POtHflz/Gt1mKylBvHBp3LjnVJRRO

Initial Root Token: <вывод скрыт>

Vault initialized with 3 key shares and a key threshold of 2. Please securely
distribute the key shares printed above. When the Vault is re-sealed,
restarted, or stopped, you must supply at least 2 of these keys to unseal it
before it can start servicing requests.

Vault does not store the generated root key. Without at least 2 keys to
reconstruct the root key, Vault will remain permanently sealed!

It is possible to generate new unseal keys, provided you have a quorum of
existing unseal keys shares. See "vault operator rekey" for more information.
```

---
<br>

## Проверим состояние vault'а

```bash
$ k -n vault logs vault-0
...
2023-07-26T15:51:40.684Z [INFO]  core: security barrier initialized: stored=1 shares=3 threshold=2
2023-07-26T15:51:40.778Z [INFO]  core: post-unseal setup starting
2023-07-26T15:51:40.827Z [INFO]  core: loaded wrapping token key
2023-07-26T15:51:40.827Z [INFO]  core: successfully setup plugin catalog: plugin-directory=""
2023-07-26T15:51:40.830Z [INFO]  core: no mounts; adding default mount table
2023-07-26T15:51:40.867Z [INFO]  core: successfully mounted: type=cubbyhole version="v1.14.0+builtin.vault" path=cubbyhole/ namespace="ID: root. Path: "
2023-07-26T15:51:40.868Z [INFO]  core: successfully mounted: type=system version="v1.14.0+builtin.vault" path=sys/ namespace="ID: root. Path: "
2023-07-26T15:51:40.868Z [INFO]  core: successfully mounted: type=identity version="v1.14.0+builtin.vault" path=identity/ namespace="ID: root. Path: "
2023-07-26T15:51:40.942Z [INFO]  core: successfully mounted: type=token version="v1.14.0+builtin.vault" path=token/ namespace="ID: root. Path: "
2023-07-26T15:51:40.999Z [INFO]  rollback: starting rollback manager
2023-07-26T15:51:41.000Z [INFO]  core: restoring leases
2023-07-26T15:51:41.002Z [INFO]  expiration: lease restore complete
2023-07-26T15:51:41.020Z [INFO]  identity: entities restored
2023-07-26T15:51:41.021Z [INFO]  identity: groups restored
2023-07-26T15:51:41.029Z [INFO]  core: usage gauge collection is disabled
2023-07-26T15:51:41.102Z [INFO]  core: Recorded vault version: vault version=1.14.0 upgrade time="2023-07-26 15:51:41.028956186 +0000 UTC" build date=2023-06-19T11:40:23Z
2023-07-26T15:51:41.400Z [INFO]  core: post-unseal setup complete
2023-07-26T15:51:41.431Z [INFO]  core: root token generated
2023-07-26T15:51:41.431Z [INFO]  core: pre-seal teardown starting
2023-07-26T15:51:41.432Z [INFO]  rollback: stopping rollback manager
2023-07-26T15:51:41.432Z [INFO]  core: pre-seal teardown complete

# Обратим внимание на параметры Initialized, Sealed
$ k exec -n vault -it vault-0 -- vault status
Key                Value
---                -----
Seal Type          shamir
Initialized        true
Sealed             true
Total Shares       3
Threshold          2
Unseal Progress    0/2
Unseal Nonce       n/a
Version            1.14.0
Build Date         2023-06-19T11:40:23Z
Storage Type       consul
HA Enabled         true

```

---
<br>

## Распечатаем vault

### Обращаем внимание на переменные окружения в подах
```bash
$ k exec -n vault -it vault-0 -- env | grep VAULT
VAULT_K8S_NAMESPACE=vault
VAULT_ADDR=http://127.0.0.1:8200
VAULT_API_ADDR=http://172.17.133.71:8200
VAULT_K8S_POD_NAME=vault-0
VAULT_CLUSTER_ADDR=https://vault-0.vault-internal:8201
VAULT_PORT_8201_TCP=tcp://172.18.231.187:8201
VAULT_SERVICE_HOST=172.18.231.187
VAULT_PORT_8200_TCP=tcp://172.18.231.187:8200
VAULT_STANDBY_PORT_8200_TCP_PROTO=tcp
VAULT_STANDBY_PORT_8200_TCP_ADDR=172.18.213.132
VAULT_STANDBY_PORT_8201_TCP_PORT=8201
VAULT_STANDBY_PORT_8201_TCP=tcp://172.18.213.132:8201
VAULT_ACTIVE_SERVICE_PORT_HTTPS_INTERNAL=8201
VAULT_ACTIVE_PORT_8201_TCP=tcp://172.18.136.192:8201
VAULT_UI_SERVICE_PORT=8200
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP=tcp://172.18.210.142:443
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_PORT=443
VAULT_ACTIVE_PORT_8200_TCP_PROTO=tcp
VAULT_AGENT_INJECTOR_SVC_SERVICE_HOST=172.18.210.142
VAULT_SERVICE_PORT_HTTP=8200
VAULT_STANDBY_PORT_8201_TCP_PROTO=tcp
VAULT_ACTIVE_SERVICE_HOST=172.18.136.192
VAULT_ACTIVE_PORT_8201_TCP_PROTO=tcp
VAULT_AGENT_INJECTOR_SVC_SERVICE_PORT=443
VAULT_PORT_8200_TCP_PROTO=tcp
VAULT_ACTIVE_PORT_8200_TCP_PORT=8200
VAULT_ACTIVE_PORT_8201_TCP_PORT=8201
VAULT_UI_PORT_8200_TCP_PROTO=tcp
VAULT_UI_PORT_8200_TCP_PORT=8200
VAULT_SERVICE_PORT=8200
VAULT_STANDBY_SERVICE_PORT_HTTP=8200
VAULT_STANDBY_PORT_8200_TCP=tcp://172.18.213.132:8200
VAULT_PORT_8200_TCP_PORT=8200
VAULT_PORT_8201_TCP_PROTO=tcp
VAULT_PORT_8201_TCP_PORT=8201
VAULT_STANDBY_SERVICE_PORT=8200
VAULT_ACTIVE_PORT_8200_TCP=tcp://172.18.136.192:8200
VAULT_UI_PORT=tcp://172.18.156.250:8200
VAULT_AGENT_INJECTOR_SVC_PORT=tcp://172.18.210.142:443
VAULT_PORT=tcp://172.18.231.187:8200
VAULT_PORT_8200_TCP_ADDR=172.18.231.187
VAULT_STANDBY_PORT_8200_TCP_PORT=8200
VAULT_ACTIVE_PORT_8200_TCP_ADDR=172.18.136.192
VAULT_SERVICE_PORT_HTTPS_INTERNAL=8201
VAULT_STANDBY_SERVICE_HOST=172.18.213.132
VAULT_ACTIVE_SERVICE_PORT_HTTP=8200
VAULT_UI_PORT_8200_TCP=tcp://172.18.156.250:8200
VAULT_AGENT_INJECTOR_SVC_SERVICE_PORT_HTTPS=443
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_ADDR=172.18.210.142
VAULT_STANDBY_SERVICE_PORT_HTTPS_INTERNAL=8201
VAULT_ACTIVE_PORT=tcp://172.18.136.192:8200
VAULT_ACTIVE_PORT_8201_TCP_ADDR=172.18.136.192
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_PROTO=tcp
VAULT_UI_SERVICE_HOST=172.18.156.250
VAULT_UI_PORT_8200_TCP_ADDR=172.18.156.250
VAULT_PORT_8201_TCP_ADDR=172.18.231.187
VAULT_STANDBY_PORT=tcp://172.18.213.132:8200
VAULT_STANDBY_PORT_8201_TCP_ADDR=172.18.213.132
VAULT_ACTIVE_SERVICE_PORT=8200
VAULT_UI_SERVICE_PORT_HTTP=8200
```  
<br>

### Распечатываем каждый под

```bash
# vault-0 первый ключ из 2х необходимых
$ k exec -n vault -it vault-0 -- vault operator unseal 'C2vhGijP/T8Zdz9D+sDHoZaL5LT9UmY5JcouS3LUvbaF'
Key                Value
---                -----
Seal Type          shamir
Initialized        true
Sealed             true
Total Shares       3
Threshold          2
Unseal Progress    1/2
Unseal Nonce       423d73c9-3c8e-68b8-d702-de75c466b8f8
Version            1.14.0
Build Date         2023-06-19T11:40:23Z
Storage Type       consul
HA Enabled         true

# vault-0 второй ключ из 2х необходимых
$ k exec -n vault -it vault-0 -- vault operator unseal 'Rqmr+PfXh6OwhEOnOLwUbprPAVOS9KmXN2NdYUTDGzvG'
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false
Total Shares    3
Threshold       2
Version         1.14.0
Build Date      2023-06-19T11:40:23Z
Storage Type    consul
Cluster Name    vault-cluster-817f0e1a
Cluster ID      66430059-08bf-d17c-d9e2-73d25d51ff6d
HA Enabled      true
HA Cluster      https://vault-0.vault-internal:8201
HA Mode         active
Active Since    2023-07-26T16:05:38.381162059Z

# vault-1 первый ключ из 2х необходимых
$ k exec -n vault -it vault-1 -- vault operator unseal 'Rqmr+PfXh6OwhEOnOLwUbprPAVOS9KmXN2NdYUTDGzvG'
Key                Value
---                -----
Seal Type          shamir
Initialized        true
Sealed             true
Total Shares       3
Threshold          2
Unseal Progress    1/2
Unseal Nonce       c3f9c3bf-8871-9956-0dfe-22434e3fe920
Version            1.14.0
Build Date         2023-06-19T11:40:23Z
Storage Type       consul
HA Enabled         true

# vault-1 второй ключ из 2х необходимых
$ k exec -n vault -it vault-1 -- vault operator unseal '16u7z5mGNUXJei5POtHflz/Gt1mKylBvHBp3LjnVJRRO'
Key                    Value
---                    -----
Seal Type              shamir
Initialized            true
Sealed                 false
Total Shares           3
Threshold              2
Version                1.14.0
Build Date             2023-06-19T11:40:23Z
Storage Type           consul
Cluster Name           vault-cluster-817f0e1a
Cluster ID             66430059-08bf-d17c-d9e2-73d25d51ff6d
HA Enabled             true
HA Cluster             https://vault-0.vault-internal:8201
HA Mode                standby
Active Node Address    http://172.17.133.71:8200

# vault-2 первый ключ из 2х необходимых
$ k exec -n vault -it vault-2 -- vault operator unseal '16u7z5mGNUXJei5POtHflz/Gt1mKylBvHBp3LjnVJRRO'
Key                Value
---                -----
Seal Type          shamir
Initialized        true
Sealed             true
Total Shares       3
Threshold          2
Unseal Progress    1/2
Unseal Nonce       a8035f0b-cff4-c38a-7507-13e0c8ba7735
Version            1.14.0
Build Date         2023-06-19T11:40:23Z
Storage Type       consul
HA Enabled         true

# vault-2 второй ключ из 2х необходимых
$ k exec -n vault -it vault-2 -- vault operator unseal 'C2vhGijP/T8Zdz9D+sDHoZaL5LT9UmY5JcouS3LUvbaF'
Key                    Value
---                    -----
Seal Type              shamir
Initialized            true
Sealed                 false
Total Shares           3
Threshold              2
Version                1.14.0
Build Date             2023-06-19T11:40:23Z
Storage Type           consul
Cluster Name           vault-cluster-817f0e1a
Cluster ID             66430059-08bf-d17c-d9e2-73d25d51ff6d
HA Enabled             true
HA Cluster             https://vault-0.vault-internal:8201
HA Mode                standby
Active Node Address    http://172.17.133.71:8200

# vault status
$ k exec -n vault -it vault-2 -- vault status
Key                    Value
---                    -----
Seal Type              shamir
Initialized            true
Sealed                 false
Total Shares           3
Threshold              2
Version                1.14.0
Build Date             2023-06-19T11:40:23Z
Storage Type           consul
Cluster Name           vault-cluster-817f0e1a
Cluster ID             66430059-08bf-d17c-d9e2-73d25d51ff6d
HA Enabled             true
HA Cluster             https://vault-0.vault-internal:8201
HA Mode                standby
Active Node Address    http://172.17.133.71:8200

$ k exec -n vault -it vault-1 -- vault status
Key                    Value
---                    -----
Seal Type              shamir
Initialized            true
Sealed                 false
Total Shares           3
Threshold              2
Version                1.14.0
Build Date             2023-06-19T11:40:23Z
Storage Type           consul
Cluster Name           vault-cluster-817f0e1a
Cluster ID             66430059-08bf-d17c-d9e2-73d25d51ff6d
HA Enabled             true
HA Cluster             https://vault-0.vault-internal:8201
HA Mode                standby
Active Node Address    http://172.17.133.71:8200

$ k exec -n vault -it vault-0 -- vault status
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false
Total Shares    3
Threshold       2
Version         1.14.0
Build Date      2023-06-19T11:40:23Z
Storage Type    consul
Cluster Name    vault-cluster-817f0e1a
Cluster ID      66430059-08bf-d17c-d9e2-73d25d51ff6d
HA Enabled      true
HA Cluster      https://vault-0.vault-internal:8201
HA Mode         active
Active Since    2023-07-26T16:05:38.381162059Z
```

---
<br>

## Посмотрим список доступных авторизаций

```bash
$ k exec -n vault -it vault-0 -- vault auth list
Error listing enabled authentications: Error making API request.

URL: GET http://127.0.0.1:8200/v1/sys/auth
Code: 403. Errors:

* permission denied
command terminated with exit code 2
```

---
<br>

## Залогинимся в vault (у нас есть root token)

```bash
$ k exec -n vault -it vault-0 -- vault login
Token (will be hidden): 
Success! You are now authenticated. The token information displayed below
is already stored in the token helper. You do NOT need to run "vault login"
again. Future Vault requests will automatically use this token.

Key                  Value
---                  -----
token                <вывод скрыт>
token_accessor       <вывод скрыт>
token_duration       ∞
token_renewable      false
token_policies       ["root"]
identity_policies    []
policies             ["root"]

# Повторно запросим список авторизаций
$ k exec -n vault -it vault-0 -- vault auth list
Path      Type     Accessor               Description                Version
----      ----     --------               -----------                -------
token/    token    auth_token_671f5b59    token based credentials    n/a
```

---
<br>

## Заведем секреты

```bash
$ k exec -n vault -it vault-0 -- vault secrets enable --path=otus kv
Success! Enabled the kv secrets engine at: otus/
$ k exec -n vault -it vault-0 -- vault secrets list --detailed
Path          Plugin       Accessor              Default TTL    Max TTL    Force No Cache    Replication    Seal Wrap    External Entropy Access    Options    Description                                                UUID                                    Version    Running Version          Running SHA256    Deprecation Status
----          ------       --------              -----------    -------    --------------    -----------    ---------    -----------------------    -------    -----------                                                ----                                    -------    ---------------          --------------    ------------------
cubbyhole/    cubbyhole    cubbyhole_9151b50f    n/a            n/a        false             local          false        false                      map[]      per-token private secret storage                           de1fe2af-8d2b-6d43-a5dd-ae2a56ced3d1    n/a        v1.14.0+builtin.vault    n/a               n/a
identity/     identity     identity_4ec654aa     system         system     false             replicated     false        false                      map[]      identity store                                             f7d1539a-b92b-9203-213f-52524ee4f927    n/a        v1.14.0+builtin.vault    n/a               n/a
otus/         kv           kv_e1bb8252           system         system     false             replicated     false        false                      map[]      n/a                                                        3083aa06-4790-1827-78bb-1f816ec4367d    n/a        v0.15.0+builtin          n/a               supported
sys/          system       system_6750861b       n/a            n/a        false             replicated     true         false                      map[]      system endpoints used for control, policy and debugging    e7b2ebad-9e87-a157-1b10-0e4242735189    n/a        v1.14.0+builtin.vault    n/a               n/a

$ k exec -n vault -it vault-0 -- vault kv put otus/otus-ro/config username='otus' password='asajkjkahs'
Success! Data written to: otus/otus-ro/config

$ k exec -n vault -it vault-0 -- vault read otus/otus-ro/config
Key                 Value
---                 -----
refresh_interval    768h
password            asajkjkahs
username            otus

$ k exec -n vault -it vault-0 -- vault kv get otus/otus-ro/config
====== Data ======
Key         Value
---         -----
password    asajkjkahs
username    otus
```

---
<br>

## Включим авторизацию черерз k8s

```bash
$ k exec -n vault -it vault-0 -- vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

$ k exec -n vault -it vault-0 -- vault auth list
Path           Type          Accessor                    Description                Version
----           ----          --------                    -----------                -------
kubernetes/    kubernetes    auth_kubernetes_a4c990c2    n/a                        n/a
token/         token         auth_token_671f5b59         token based credentials    n/a
```

---
<br>

### yaml для ClusterRoleBinding  

[crb-vault-auth.yaml](/kubernetes-vault/crb-vault-auth.yaml)  

### Service Account vault-auth  

[sa-vault-auth.yaml](/kubernetes-vault/sa-vault-auth.yaml)  

```bash
$ k apply -f sa-vault-auth.yaml 
serviceaccount/vault-auth created

$ k apply -f crb-vault-auth.yaml 
clusterrolebinding.rbac.authorization.k8s.io/role-tokenreview-binding created
```

---
<br>

## Подготовим переменные для записи в конфиг кубер авторизации

$ kubectl -n vault get sa vault-auth -o jsonpath="{.secrets[*]['name']}"
vault-auth-token-4wrws
