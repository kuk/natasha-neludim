IMAGE = natasha-neludim
REGISTRY = cr.yandex/$(REGISTRY_ID)
REMOTE = $(REGISTRY)/$(IMAGE)

test-lint:
	pytest -vv --asyncio-mode=auto --pycodestyle --flakes main.py

test-key:
	pytest -vv --asyncio-mode=auto -s -k $(KEY) test.py

test-cov:
	pytest -vv --asyncio-mode=auto --cov-report html --cov main test.py

image:
	docker build -t $(IMAGE) .

push:
	docker tag $(IMAGE) $(REMOTE)
	docker push $(REMOTE)

deploy:
	yc serverless container revision deploy \
		--container-name default \
		--image $(REGISTRY)/natasha-neludim:latest \
		--cores 1 \
		--memory 256MB \
		--concurrency 16 \
		--execution-timeout 30s \
		--environment BOT_TOKEN=$(BOT_TOKEN) \
		--environment AWS_KEY_ID=$(AWS_KEY_ID) \
		--environment AWS_KEY=$(AWS_KEY) \
		--environment DYNAMO_ENDPOINT=$(DYNAMO_ENDPOINT) \
		--service-account-id $(SERVICE_ACCOUNT_ID) \
		--folder-name natasha-neludim
