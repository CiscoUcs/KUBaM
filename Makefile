.phony: build push

all: build push

build:
	docker build -t kubam/kubam:v2 . 

push:
	docker push kubam/kubam:v2
