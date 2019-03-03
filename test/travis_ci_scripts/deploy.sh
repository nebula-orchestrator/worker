#!/usr/bin/env bash

echo "$DOCKER_HUB_PASSWORD" | docker login -u "$DOCKER_HUB_USER" --password-stdin

if [ "$TRAVIS_BRANCH" == "master" ] && [ "$TRAVIS_PULL_REQUEST" == false ]; then
    docker build -t $DOCKER_HUB_ORG/$DOCKER_HUB_REPO .
    docker push $DOCKER_HUB_ORG/$DOCKER_HUB_REPO
elif [ "$TRAVIS_BRANCH" != "master" ] && [ "$TRAVIS_PULL_REQUEST" == false ]; then
    docker build -t $DOCKER_HUB_ORG/$DOCKER_HUB_REPO:$TRAVIS_BRANCH .
    docker push $DOCKER_HUB_ORG/$DOCKER_HUB_REPO:$TRAVIS_BRANCH
else
    echo "something is wrong with the deployment"
    exit 2
fi
