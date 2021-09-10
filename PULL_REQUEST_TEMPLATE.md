Fixes #

## Proposed Changes

  - Added support of Redis worker report caching as an alternative to Kafka.
  - Supports Redis cache expire time with a default of ```2*nebula_manager_check_in_time```.
  - Log caching flag must be enabled to report logs to the Redis server.
