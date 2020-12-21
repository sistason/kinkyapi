# KinkyAPI

Implements an API for Kink.Com
see src/kinkcom/models.py for the schema

## Docker

build the image and start with docker-compose

## K8s

the helm-directory is just a `helm create` with env added to the deployment and a cronjob for the update_shoots.
so use the provided values.yaml example and adapt to your liking
