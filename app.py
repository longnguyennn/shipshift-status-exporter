from prometheus_client import start_http_server, Metric, REGISTRY
import json
import requests
import sys
import time
import os

class JsonCollector(object):
    def __init__(self,endpoint):
        self._endpoint = endpoint

    def collect(self):
        # Fetch the JSON
        token = os.getenv('token')
        headers = { 'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(token) }
        response = requests.get(self._endpoint,headers=headers,verify=False).json()
        pods = response['items']

        # Parse result and expose metrics
        shipshift_status = 1
        for pod in pods:
            pod_name = pod['metadata']['name']
            containers = pod['status']['containerStatuses']
            # Expose status for every container in the pod
            for container in containers:
                state = container['state']
                container_name = container['name']
                if ('running' in state):
                    current_val = 1
                else:
                    shipshift_status = 0
                    current_val = 0
                metric_name = '{}_{}_status'.format(pod_name,container_name)
                metric_description = 'Current status of container {} in pod {}'.format( container_name,
                        pod_name)
                metric = Metric(metric_name, metric_description, 'summary')
                metric.add_sample(metric_name, value=current_val, labels={})
                yield metric

        # Shipshift up/down status
        metric = Metric('Shipshift_status', 'Current status of Shipshift', 'summary')
        metric.add_sample('Shipshift_status', value=shipshift_status, labels={})
        yield metric

if __name__ == '__main__':
    # Usage: json_exporter.py port endpoint
    # expose on fixed port 9100
    start_http_server(9100)
    # direct endpoint to Shipshift on Upshift
    shipshift_endpoint = 'https://upshift.engineering.redhat.com/api/v1/namespaces/dh-stage-shipshift/pods'
    REGISTRY.register(JsonCollector(shipshift_endpoint))

    while True: time.sleep(1)
