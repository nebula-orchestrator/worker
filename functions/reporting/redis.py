import sys, json, redis, pickle

class RedisConnection:

    def __init__(self, redis_host, redis_port, redis_auth_token, expire_time,topic="nebula-reports"):
        self.topic = topic
        self.expireTime=None
        if expire_time is not None:
            self.expireTime = int(expire_time)
        self.redisObj = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_auth_token)

    @staticmethod
    def on_send_error(excp):
        print("Report delivery to redis failed: " + str(excp))

    def push_report(self, report):
        try:
            key = self.topic+"_"+str(report["report_creation_time"])+"_"+str(report["device_group"])+"@"+str(report["hostname"])
            self.redisObj.set(key, pickle.dumps(report),ex=self.expireTime,)
        except Exception as e:
            print(e, file=sys.stderr)
            print("Report delivery to redis failed")

    def map_container_id(self,report):
        container_info = report["apps_containers"]
        for container in container_info:

            try:
                container_id = container["id"]
                container_name = container["name"].split("-")[0].replace("/","")
                container_time = container["read"]
            except Exception as e:
                print(e, file=sys.stderr)
                print("Error reporting containers on host {}".format(report["hostname"]))
                continue

            try:
                container_map = {}
                container_map["name"] = container_name
                container_map["time"] = container_time

                #keys can be signed here with timestamp for extra protection
                self.redisObj.set("container_"+container_id, pickle.dumps(container_map),)

            except Exception as e:
                print(e, file=sys.stderr)
                print("Container Map push to redis failed for {}".format(container_name))