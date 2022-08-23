
# Бот организует random coffee для сообщества @natural_language_processing

## Разработка

Создать директорию в YC.

```bash
yc resource-manager folder create --name natasha-neludim
```

Создать сервисный аккаунт в YC. Записать `id` в `.env`.

```bash
yc iam service-accounts create natasha-neludim --folder-name natasha-neludim

id: {SERVICE_ACCOUNT_ID}
```

Сгенерить ключи для DynamoDB, добавить их в `.env`.

```bash
yc iam access-key create \
  --service-account-name natasha-neludim \
  --folder-name natasha-neludim

key_id: {AWS_KEY_ID}
secret: {AWS_KEY}
```

Назначить роли, сервисный аккаунт может только писать и читать YDB.

```bash
for role in ydb.viewer ydb.editor
do
  yc resource-manager folder add-access-binding natasha-neludim \
    --role $role \
    --service-account-name natasha-neludim \
    --folder-name natasha-neludim \
    --async
done
```

Создать базу YDB. Записать эндпоинт для DynamoDB в `.env`.

```bash
yc ydb database create default --serverless --folder-name natasha-neludim

document_api_endpoint: {DYNAMO_ENDPOINT}
```

Установить, настроить `aws`.

```bash
pip install awscli
aws configure --profile natasha-neludim

{AWS_KEY_ID}
{AWS_KEY}
ru-central1
```

Создать табличку.

```bash
aws dynamodb create-table \
  --table-name chats \
  --attribute-definitions \
    AttributeName=id,AttributeType=N \
  --key-schema \
    AttributeName=id,KeyType=HASH \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim

aws dynamodb create-table \
  --table-name users \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=N \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim

aws dynamodb create-table \
  --table-name contacts \
  --attribute-definitions \
    AttributeName=key,AttributeType=S \
  --key-schema \
    AttributeName=key,KeyType=HASH \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim
```

Удалить таблички.

```bash
aws dynamodb delete-table --table-name chats \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim

aws dynamodb delete-table --table-name users \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim

aws dynamodb delete-table --table-name contacts \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim
```

Список таблиц.

```bash
aws dynamodb list-tables \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim
```

Прочитать табличку.

```bash
aws dynamodb scan \
  --table-name chats \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim

aws dynamodb scan \
  --table-name users \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim

aws dynamodb scan \
  --table-name contacts \
  --endpoint $DYNAMO_ENDPOINT \
  --profile natasha-neludim
```

Создать реестр для контейнера в YC. Записать `id` в `.env`.

```bash
yc container registry create default --folder-name natasha-neludim
id: {REGISTRY_ID}
```

Дать права сервисному аккаунту читать из реестра. Интеграция с YC Serverless Containers.

```bash
yc container registry add-access-binding default \
  --role container-registry.images.puller \
  --service-account-name natasha-neludim \
  --folder-name natasha-neludim
```

Создать Serverless Containers. Записать `id` в `.env`.

```bash
yc serverless container create --name bot --folder-name natasha-neludim

id: {BOT_CONTAINER_ID}

yc serverless container create --name trigger --folder-name natasha-neludim

id: {TRIGGER_CONTAINER_ID}
```

Разрешить `bot` без токена. Телеграм дергает вебхук.

```bash
yc serverless container allow-unauthenticated-invoke bot \
  --folder-name natasha-neludim
```

Сделать `trigger` приватным.

```bash
yc serverless container deny-unauthenticated-invoke trigger \
  --folder-name natasha-neludim
```

Только у сервисного аккаунта право вызывать.

```bash
yc serverless container add-access-binding trigger \
  --role serverless.containers.invoker \
  --service-account-name natasha-neludim \
  --folder-name natasha-neludim
```

Логи.

```bash
yc log read default --follow --folder-name natasha-neludim
```

Прицепить вебхук.

```bash
WEBHOOK_URL=https://${BOT_CONTAINER_ID}.containers.yandexcloud.net/
curl --url https://api.telegram.org/bot${BOT_TOKEN}/setWebhook\?url=${WEBHOOK_URL}
```

Создать триггер.

```bash
yc serverless trigger create timer default \
  --cron-expression "* * * * ? *" \
  --invoke-container-name trigger \
  --invoke-container-service-account-name natasha-neludim \
  --folder-name natasha-neludim
```

Остановить, запустить триггер.

```bash
yc serverless trigger pause default \
  --folder-name natasha-neludim

yc serverless trigger resume default \
  --folder-name natasha-neludim
```

Создать окружение, установить зависимости.

```bash
pyenv virtualenv 3.9.10 neludim
pyenv activate neludim

pip install \
  -r requirements/test.txt \
  -r requirements/main.txt

pip install -e .
```

Трюк чтобы загрузить окружение из `.env`.

```bash
export $(cat .env | xargs)
```

Прогнать линтер, тесты.

```bash
make test-lint test-key KEY=test
```

Собрать образ, загрузить его в реестр, задеплоить

```bash
make image push
make deploy-bot
make deploy-trigger
```
