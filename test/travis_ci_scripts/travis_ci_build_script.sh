#!/usr/bin/env bash

# auth into docker hub to avoid pull rate limiting
echo "$DOCKER_HUB_PASSWORD" | docker login -u "$DOCKER_HUB_USER" --password-stdin

# run the following to start the API & MongoDB
sudo docker-compose -f test/travis_ci_scripts/docker-compose.yml pull
sudo docker-compose -f test/travis_ci_scripts/docker-compose.yml up -d

# wait until the manager is online
until $(curl --output /dev/null --silent --head --fail -H 'authorization: Basic bmVidWxhOm5lYnVsYQ==' -H 'cache-control: no-cache' http://127.0.0.1/api/v2/status); do
    echo "Waiting on the manager API to become available..."
    sleep 3
done

echo "manager available"
