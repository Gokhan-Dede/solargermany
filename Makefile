TESTS = tests

# Local Docker build and run
install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest

docker_build_local:
	docker build --tag=solargermany.streamlit.app:local .

docker_run_local:
	docker run \
		-e PORT=8501 -p 8501:8501 \
		--env-file .env \
		solargermany.streamlit.app:local

docker_run_local_interactively:
	docker run -it \
		-e PORT=8501 -p 8501:8501 \
		--env-file .env \
		solargermany.streamlit.app:local \
		bash

# Cloud images - linux/amd64 architecture is needed
gar_creation:
	gcloud auth configure-docker ${GCP_REGION}-docker.pkg.dev
	gcloud artifacts repositories create ${GAR_REPO} --repository-format=docker \
	--location=${GCP_REGION} --description="Repository for storing ${GAR_REPO} images"

docker_build:
	docker build --platform linux/amd64 -t ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPO}/solargermany.streamlit.app:prod .

docker_push:
	docker push ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPO}/solargermany.streamlit.app:prod

docker_run:
	docker run -e PORT=8080 -p 8080:8080 --env-file .env ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPO}/${GAR_IMAGE}:prod

docker_interactive:
	docker run -it --env-file .env ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPO}/solargermany.streamlit.app:prod /bin/bash

docker_deploy:
	gcloud run deploy --image ${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT}/${GAR_REPO}/solargermany.streamlit.app:prod --memory ${GAR_MEMORY} --region ${GCP_REGION}
