IMAGE = natasha-neludim
REGISTRY = cr.yandex/$(REGISTRY_ID)
REMOTE = $(REGISTRY)/$(IMAGE)

test-lint:
	pytest -vv --pycodestyle --flakes --ignore neludim/tests neludim

test-key:
	pytest -vv -s -k $(KEY) neludim

test-cov:
	pytest -vv --cov-report html --cov neludim neludim

image:
	docker build -t $(IMAGE) .

push:
	docker tag $(IMAGE) $(REMOTE)
	docker push $(REMOTE)

deploy-bot:
	yc serverless container revision deploy \
		--container-name bot \
		--image $(REGISTRY)/natasha-neludim:latest \
		--args bot-webhook \
		--cores 1 \
		--memory 256MB \
		--concurrency 16 \
		--execution-timeout 30s \
		--environment BOT_TOKEN=$(BOT_TOKEN) \
		--environment AWS_KEY_ID=$(AWS_KEY_ID) \
		--environment AWS_KEY=$(AWS_KEY) \
		--environment DYNAMO_ENDPOINT=$(DYNAMO_ENDPOINT) \
		--environment ADMIN_USER_ID=$(ADMIN_USER_ID) \
		--service-account-id $(SERVICE_ACCOUNT_ID) \
		--folder-name natasha-neludim

deploy-trigger:
	yc serverless container revision deploy \
		--container-name trigger \
		--image $(REGISTRY)/natasha-neludim:latest \
		--args trigger-webhook \
		--cores 1 \
		--memory 256MB \
		--concurrency 16 \
		--execution-timeout 30s \
		--environment BOT_TOKEN=$(BOT_TOKEN) \
		--environment AWS_KEY_ID=$(AWS_KEY_ID) \
		--environment AWS_KEY=$(AWS_KEY) \
		--environment DYNAMO_ENDPOINT=$(DYNAMO_ENDPOINT) \
		--environment ADMIN_USER_ID=$(ADMIN_USER_ID) \
		--service-account-id $(SERVICE_ACCOUNT_ID) \
		--folder-name natasha-neludim

clean:
	find . \
		-name '*.pyc' \
		-o -name __pycache__ \
		-o -name .ipynb_checkpoints \
		-o -name .DS_Store \
		| xargs rm -rf

	rm -rf dist/ build/ .pytest_cache/ .cache/ .coverage
