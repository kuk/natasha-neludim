
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

Дать права сервисному аккаунту читать из реестра. Интеграция с YC Serverless Container.

```bash
yc container registry add-access-binding default \
  --role container-registry.images.puller \
  --service-account-name natasha-neludim \
  --folder-name natasha-neludim
```

Создать Serverless Container. Записать `id` в `.env`.

```bash
yc serverless container create --name default --folder-name natasha-neludim

id: {CONTAINER_ID}
```

Разрешить без токена. Телеграм дергает вебхук.

```bash
yc serverless container allow-unauthenticated-invoke default \
  --folder-name natasha-neludim
```

Логи.

```bash
yc log read default --follow --folder-name natasha-neludim
```

Прицепить вебхук.

```bash
WEBHOOK_URL=https://${CONTAINER_ID}.containers.yandexcloud.net/
curl --url https://api.telegram.org/bot${BOT_TOKEN}/setWebhook\?url=${WEBHOOK_URL}
```

Трюк чтобы загрузить окружение из `.env`.

```bash
export $(cat .env | xargs)
```

Установить зависимости для тестов.

```bash
pip install \
  pytest-aiohttp \
  pytest-asyncio \
  pytest-cov \
  pytest-flakes \
  pytest-pycodestyle
```

Прогнать линтер, тесты.

```bash
make test-lint test-key KEY=test
```

Собрать образ, загрузить его в реестр, задеплоить

```bash
make image push deploy
```
