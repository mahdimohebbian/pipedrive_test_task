docker rmi pipedrive_pipeline:latest
docker build -t pipedrive_pipeline .
docker run --rm --env-file .env pipedrive_pipeline