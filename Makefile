start-docker:
	docker run --rm -p 49999:49999 -p 6080:6080 -it $$(docker build . -q -f ./e2b.Dockerfile)