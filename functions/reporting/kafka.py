from confluent_kafka import Producer
import sys


class KafkaConnection:

    def __init__(self, bootstrap_servers, security_protocol="plaintext", sasl_mechanism="GSSAPI", sasl_username=None,
                 sasl_password=None, ssl_cipher_suites=None, ssl_curves_list=None, ssl_sigalgs_list=None,
                 ssl_key_location=None, ssl_key_password=None, ssl_certificate_location=None, ssl_ca_location=None,
                 ssl_crl_location=None, ssl_keystore_location=None, ssl_keystore_password=None, retries=2,
                 sasl_kerberos_service_name="kafka", sasl_kerberos_principal="kafkaclient", queue_buffering_max_ms=0,
                 queue_buffering_max_messages=100000, queue_buffering_max_kbytes=1048576):
        self.producer = Producer(
            {
                'bootstrap.servers': bootstrap_servers,
                'security.protocol': security_protocol,
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': sasl_username,
                'sasl.password': sasl_password,
                'ssl.cipher.suites': ssl_cipher_suites,
                'ssl.curves.list': ssl_curves_list,
                'ssl.sigalgs.list': ssl_sigalgs_list,
                'ssl.key.location': ssl_key_location,
                'ssl.key.password': ssl_key_password,
                'ssl.certificate.location': ssl_certificate_location,
                'ssl.ca.location': ssl_ca_location,
                'ssl.crl.location': ssl_crl_location,
                'ssl.keystore.location': ssl_keystore_location,
                'ssl.keystore.password': ssl_keystore_password,
                'sasl.kerberos.service.name': sasl_kerberos_service_name,
                'sasl.kerberos.principal': sasl_kerberos_principal,
                'retries': retries,
                'queue.buffering.max.messages': queue_buffering_max_messages,
                'queue.buffering.max.kbytes': queue_buffering_max_kbytes,
                'queue.buffering.max.ms': queue_buffering_max_ms
            }
        )

    @staticmethod
    def delivery_report(err, msg):
        if err is not None:
            print('Report delivery to kafka failed: {}'.format(err))

    def push_report(self, report, topic="nebula_reports"):
        try:
            self.producer.poll(0)
            self.producer.produce(topic, report.encode('utf-8'), callback=self.delivery_report)
            self.producer.flush()
        except Exception as e:
            print(e, file=sys.stderr)
            print("Report delivery to kafka failed")
