from kafka import KafkaProducer
import sys, json


class KafkaConnection:

    def __init__(self, bootstrap_servers, security_protocol="PLAINTEXT", sasl_mechanism=None, sasl_plain_username=None,
                 sasl_plain_password=None,
                 ssl_keyfile=None, ssl_password=None, ssl_certfile=None, ssl_cafile=None, ssl_crlfile=None,
                 sasl_kerberos_service_name="kafka", sasl_kerberos_domain_name="kafka",  topic="nebula-reports"):
        self.topic = topic
        self.producer = KafkaProducer(value_serializer=lambda m: json.dumps(m).encode('ascii'),
                                      bootstrap_servers=bootstrap_servers, security_protocol=security_protocol,
                                      sasl_mechanism=sasl_mechanism, sasl_plain_username=sasl_plain_username,
                                      sasl_plain_password=sasl_plain_password, ssl_keyfile=ssl_keyfile,
                                      ssl_password=ssl_password, ssl_certfile=ssl_certfile, ssl_cafile=ssl_cafile,
                                      ssl_crlfile=ssl_crlfile, sasl_kerberos_service_name=sasl_kerberos_service_name,
                                      sasl_kerberos_domain_name=sasl_kerberos_domain_name)

    @staticmethod
    def on_send_error(excp):
            print("Report delivery to kafka failed: " + str(excp))

    def push_report(self, report):
        try:
            self.producer.send(self.topic, report).add_errback(self.on_send_error)
        except Exception as e:
            print(e, file=sys.stderr)
            print("Report delivery to kafka failed")
