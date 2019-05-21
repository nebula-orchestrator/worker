# Change Log

## [2.6.1](https://github.com/nebula-orchestrator/worker/tree/2.6.1) (2019-05-21)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/2.5.0...2.6.1)

**Implemented enhancements:**

- Add cron jobs management support [\#42](https://github.com/nebula-orchestrator/worker/issues/42)
- Self update worker container on deployed remote devices [\#41](https://github.com/nebula-orchestrator/worker/issues/41)
- Bump docker from 3.7.2 to 4.0.1 [\#50](https://github.com/nebula-orchestrator/worker/pull/50) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump nebulapythonsdk from 2.5.1 to 2.5.2 [\#49](https://github.com/nebula-orchestrator/worker/pull/49) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump parse-it from 0.5.11 to 0.7.0 [\#48](https://github.com/nebula-orchestrator/worker/pull/48) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump requests from 2.21.0 to 2.22.0 [\#47](https://github.com/nebula-orchestrator/worker/pull/47) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump parse-it from 0.5.5 to 0.5.11 [\#46](https://github.com/nebula-orchestrator/worker/pull/46) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump websocket-client from 0.54.0 to 0.56.0 [\#45](https://github.com/nebula-orchestrator/worker/pull/45) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump backports-ssl-match-hostname from 3.5.0.1 to 3.7.0.1 [\#44](https://github.com/nebula-orchestrator/worker/pull/44) ([dependabot[bot]](https://github.com/apps/dependabot))

## [2.5.0](https://github.com/nebula-orchestrator/worker/tree/2.5.0) (2019-04-21)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/2.4.0...2.5.0)

**Implemented enhancements:**

- have worker have the option to connect to the managers with a UUID token instead of basic auth [\#40](https://github.com/nebula-orchestrator/worker/issues/40)

## [2.4.0](https://github.com/nebula-orchestrator/worker/tree/2.4.0) (2019-03-12)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/2.3.0...2.4.0)

**Fixed bugs:**

- Support for multiple authenticated registries  [\#26](https://github.com/nebula-orchestrator/worker/issues/26)

## [2.3.0](https://github.com/nebula-orchestrator/worker/tree/2.3.0) (2019-03-05)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/2.2.0...2.3.0)

**Implemented enhancements:**

- Move automatic Docker imags build from Docker Hub to Travis-CI [\#39](https://github.com/nebula-orchestrator/worker/issues/39)

## [2.2.0](https://github.com/nebula-orchestrator/worker/tree/2.2.0) (2019-02-27)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/2.1.0...2.2.0)

**Implemented enhancements:**

- Migrate to Python 3.x [\#32](https://github.com/nebula-orchestrator/worker/issues/32)

## [2.1.0](https://github.com/nebula-orchestrator/worker/tree/2.1.0) (2019-02-17)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/2.0.1...2.1.0)

## [2.0.1](https://github.com/nebula-orchestrator/worker/tree/2.0.1) (2019-01-15)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/2.0.0...2.0.1)

## [2.0.0](https://github.com/nebula-orchestrator/worker/tree/2.0.0) (2019-01-14)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.6.0...2.0.0)

**Implemented enhancements:**

-  Rename worker-manager to worker [\#33](https://github.com/nebula-orchestrator/worker/issues/33)
- Add SSL support for RabbitMQ connections [\#17](https://github.com/nebula-orchestrator/worker/issues/17)
- pod like stracture option [\#9](https://github.com/nebula-orchestrator/worker/issues/9)

**Fixed bugs:**

- host network leaves container with no network [\#35](https://github.com/nebula-orchestrator/worker/issues/35)
- Allow starting the worker with no conf.json file present [\#34](https://github.com/nebula-orchestrator/worker/issues/34)

**Merged pull requests:**

- 2.0.0a [\#37](https://github.com/nebula-orchestrator/worker/pull/37) ([naorlivne](https://github.com/naorlivne))

## [1.6.0](https://github.com/nebula-orchestrator/worker/tree/1.6.0) (2018-12-06)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.5.0...1.6.0)

**Implemented enhancements:**

- Add the option to not automatically --rm docker images and auto pull on every nebula app change  [\#24](https://github.com/nebula-orchestrator/worker/issues/24)

**Fixed bugs:**

- Registry login should only happen once at start  [\#23](https://github.com/nebula-orchestrator/worker/issues/23)

## [1.5.0](https://github.com/nebula-orchestrator/worker/tree/1.5.0) (2018-10-07)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.4.0...1.5.0)

**Implemented enhancements:**

- Integrate with Dockerfile based healthchecks [\#28](https://github.com/nebula-orchestrator/worker/issues/28)
- Add ARM version of the worker-manager [\#22](https://github.com/nebula-orchestrator/worker/issues/22)

## [1.4.0](https://github.com/nebula-orchestrator/worker/tree/1.4.0) (2018-08-21)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.3.0...1.4.0)

**Implemented enhancements:**

- Update prereqs [\#30](https://github.com/nebula-orchestrator/worker/issues/30)
- Intial worker sync should be done via RabbitMQ & not via a direct connection to MongoDB [\#29](https://github.com/nebula-orchestrator/worker/issues/29)
- MongoDB should only disconnect after getting the required data for all needed apps on boot [\#27](https://github.com/nebula-orchestrator/worker/issues/27)

**Fixed bugs:**

- RabbitMQ connections are not closed properly  [\#31](https://github.com/nebula-orchestrator/worker/issues/31)
- MongoDB should only disconnect after getting the required data for all needed apps on boot [\#27](https://github.com/nebula-orchestrator/worker/issues/27)

## [1.3.0](https://github.com/nebula-orchestrator/worker/tree/1.3.0) (2018-07-24)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.2.0...1.3.0)

**Implemented enhancements:**

- add multiple DB backend-support - MySQL/MariaDB [\#3](https://github.com/nebula-orchestrator/worker/issues/3)
- Registry Auth from .docker standard config file [\#1](https://github.com/nebula-orchestrator/worker/issues/1)

**Fixed bugs:**

- add protection against missing fanout exchanges [\#14](https://github.com/nebula-orchestrator/worker/issues/14)

## [1.2.0](https://github.com/nebula-orchestrator/worker/tree/1.2.0) (2017-10-24)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.1.1...1.2.0)

**Implemented enhancements:**

-  Version lock all required pip dependencies in the Dockerfile [\#15](https://github.com/nebula-orchestrator/worker/issues/15)
- Some Nebula config paramters should be optional/have default [\#13](https://github.com/nebula-orchestrator/worker/issues/13)
- get rolling restart rolling [\#2](https://github.com/nebula-orchestrator/worker/issues/2)

**Fixed bugs:**

- Remove unneeded modules from requirements.txt file [\#11](https://github.com/nebula-orchestrator/worker/issues/11)
- get rolling restart rolling [\#2](https://github.com/nebula-orchestrator/worker/issues/2)

## [1.1.1](https://github.com/nebula-orchestrator/worker/tree/1.1.1) (2017-09-18)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.1.0...1.1.1)

**Implemented enhancements:**

- add support for user networks [\#20](https://github.com/nebula-orchestrator/worker/issues/20)

## [1.1.0](https://github.com/nebula-orchestrator/worker/tree/1.1.0) (2017-09-18)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/1.0.0...1.1.0)

**Implemented enhancements:**

- add "nebula" user-network by default [\#21](https://github.com/nebula-orchestrator/worker/issues/21)
- add support for docker devices \(equivilent to docker run --device\) [\#16](https://github.com/nebula-orchestrator/worker/issues/16)
- Add support for running an app as privileged [\#5](https://github.com/nebula-orchestrator/worker/issues/5)

## [1.0.0](https://github.com/nebula-orchestrator/worker/tree/1.0.0) (2017-08-16)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/0.9.0...1.0.0)

**Implemented enhancements:**

- Add support for mounting [\#8](https://github.com/nebula-orchestrator/worker/issues/8)

## [0.9.0](https://github.com/nebula-orchestrator/worker/tree/0.9.0) (2017-08-03)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/0.8.0...0.9.0)

**Implemented enhancements:**

- Refactor to use newest version of docker-py [\#7](https://github.com/nebula-orchestrator/worker/issues/7)

## [0.8.0](https://github.com/nebula-orchestrator/worker/tree/0.8.0) (2017-06-14)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/0.7...0.8.0)

## [0.7](https://github.com/nebula-orchestrator/worker/tree/0.7) (2017-05-29)
[Full Changelog](https://github.com/nebula-orchestrator/worker/compare/v0.7...0.7)

## [v0.7](https://github.com/nebula-orchestrator/worker/tree/v0.7) (2017-05-29)


\* *This Change Log was automatically generated by [github_changelog_generator](https://github.com/skywinder/Github-Changelog-Generator)*