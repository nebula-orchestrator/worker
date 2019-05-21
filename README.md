# Nebula worker

Travis CI unit tests & autobuild: [![Build Status](https://travis-ci.org/nebula-orchestrator/worker.svg?branch=master)](https://travis-ci.org/nebula-orchestrator/worker)

Shippable ARM autobuild: [![Run Status](https://api.shippable.com/projects/5bab745d36c1700700ded430/badge?branch=master)]() 

## Main website available [here](https://nebula-orchestrator.github.io/), refer to the [documentation](http://nebula.readthedocs.io/en/latest/) for more details about how to install & use.

Nebula is a open source distributed Docker orchestrator designed for massive scales (tens of thousands of servers/worker devices), unlike Mesos/Swarm/Kubernetes it has the ability to have workers distributed on high latency connections (such as the internet) yet have the pods(containers) be managed centrally with changes taking affect (almost) immediately, this makes Nebula ideal for managing a vast cluster of servers\devices across the globe, some example use cases are:

* IoT devices
* appliances\virtual appliances located at clients data centers 
* edge computing
* POS systems

Ever wandered how your going to push an update to that smart fridge your company is working on as it's thousands of devices around the globe?
wish you could have the assurance that your service will always use the latest code\envvars\etc in all of it's edge locations?
want the ability to stop\start a globally distributed service with a single command?

Nebula was designed from the ground up to answer all of this needs and much more, refer to the [documentation](http://nebula.readthedocs.io/en/latest/) if your interested in seeing on how to use it.

This repo is the worker component of Nebula container orchestrator, it's what manages individual worker servers in the system. 
 
