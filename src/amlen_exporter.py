''' MessageSight exporter for prometheus '''
import json
import sys
import time
import requests
from prometheus_client import start_http_server, Metric, REGISTRY

class JsonServerCollector():
    ''' Collector for Server endpoint '''
    def __init__(self, endpoint):
        self._endpoint = f'http://{endpoint}/ima/v1/monitor/Server'
    def collect(self):
        ''' Collect metrics'''
        try:
            response = json.loads(requests.get(self._endpoint, timeout=10).content.decode('UTF-8'))
        except Exception as ex:
            print(f'Cannot make a request to {self._endpoint} : {type(ex).__name__}')
            return None

        metric = Metric('amlen_server_connections',
                        'Connections to the server', 'gauge')
        # Currently active connections
        metric.add_sample('amlen_server_connections_active', {},
                          response['Server']['ActiveConnections'])
        yield metric

        metric = Metric('amlen_server_connections_total',
                        'Connections to the server', 'counter')
        # Count of connections that succeeded to connect since reset.
        metric.add_sample('amlen_connections_total', {},
                          response['Server']['TotalConnections'])
        # Count of connections that failed to connect since reset.
        metric.add_sample('amlen_connections_total_bad', {},
                          response['Server']['BadConnCount'])
        yield metric

        metric = Metric('amlen_server_messages',
                        'Messages on the server', 'gauge')
        # This statistic provides an approximate count of the number of messages
        # (including inflight messages) that are currently buffered on queues
        # and subscriptions on the IBM IoT MessageSight server.
        metric.add_sample('amlen_server_messages_buffered', {},
                          response['Server']['BufferedMessages'])
        # This statistic provides an approximate count of the number of retained messages (including
        # inflight messages) that are currently waiting on topics on the IBM IoT MessageSight
        # server. The messages are waiting to be delivered to new subscribers on those topics
        # when their subscription is created for the first time.
        # The RetainedMessages statistic does not represent the number of topics with a retained
        # message, as a single topic might have multiple retained messages that are inflight.
        metric.add_sample('amlen_server_messages_retained', {},
                          response['Server']['RetainedMessages'])
        yield metric

        metric = Metric('amlen_server_client_session',
                        'Client sessions', 'gauge')
        # The number of clients for which the server has state. Includes all connected
        # clients and disconnected clients that have a session which is not ended.
        metric.add_sample('amlen_client_session_active', {},
                          response['Server']['ClientSessions'])
        # The number of client sessions that have been removed since the IBM IoT MessageSight
        # server restarted. Sessions are expired because of the SessionExpiry interval that is set
        # by an MQTTv5 client, or because of the MaxSessionExpiryInterval of a connection policy.
        metric.add_sample('amlen_server_client_session_expired', {},
                          response['Server']['ExpiredClientSessions'])
        yield metric

        metric = Metric('amlen_server_subscriptions',
                        'Server subscriptions', 'gauge')
        # Total number of subscriptions that are in the system.
        metric.add_sample('amlen_server_subscriptions', {},
                          response['Server']['Subscriptions'])
        yield metric
        return None

class JsonMemoryCollector():
    ''' Collector for Memory endpoint '''
    def __init__(self, endpoint):
        self._endpoint = f'http://{endpoint}/ima/v1/monitor/Memory'
    def collect(self):
        ''' Collect metrics'''
        try:
            response = json.loads(requests.get(self._endpoint, timeout=10).content.decode('UTF-8'))
        except Exception as ex:
            print(f'Cannot make a request to {self._endpoint} : {type(ex).__name__}')
            return None
        memory = response['Memory']
        metric = Metric('amlen_memory', 'Memory metrics', 'gauge')
        # Total amount of physical memory on IBM IoT MessageSight
        metric.add_sample('amlen_memory_total_bytes', {}, memory['MemoryTotalBytes'])
        # Amount of physical memory that is available.
        metric.add_sample('amlen_memory_free_bytes', {}, memory['MemoryFreeBytes'])
        # The amount of free memory as a percentage of total physical memory
        metric.add_sample('amlen_memory_free_percent', {}, memory['MemoryFreePercent'])
        # The amount of physical memory that is being used by IBM IoT MessageSight.
        metric.add_sample('amlen_memory_resident_set_bytes', {}, memory['ServerResidentSetBytes'])
        # The amount of virtual memory that is being used by IBM IoT MessageSight.
        metric.add_sample('amlen_memory_virt_bytes', {}, memory['ServerVirtualMemoryBytes'])
        # The amount of memory that is being used for message payloads.
        # It shows the amount of memory that is used to store messages on IBM IoT MessageSight.
        metric.add_sample('amlen_memory_message_payloads', {}, memory['MessagePayloads'])
        # The amount of memory that is being used for publish/subscribe messaging.
        metric.add_sample('amlen_memory_publish_subscribe', {}, memory['PublishSubscribe'])
        # the amount of memory that is being used by IBM IoT MessageSight for destinations.
        # That is, for queues and topics. The memory that is allocated in this category is used to
        # organize messages into the queues and subscriptions that are used by clients.
        metric.add_sample('amlen_memory_destinations', {}, memory['Destinations'])
        # This category shows the amount of memory that is being used by IBM IoT MessageSight
        # for current activity. Memory that is allocated in this category includes sessions,
        # transactions, message acknowledgments, and monitoring request information.
        metric.add_sample('amlen_memory_current_activity', {}, memory['CurrentActivity'])
        # This category shows the amount of memory that is being used by IBM IoT MessageSight
        # for connected and disconnected clients. The server allocates memory in this category
        # for each client that is connected to the server. For MQTT clients that use cleanSession=0,
        # the memory allocation continues after the client disconnects.The server also allocates
        # memory in this category to track message acknowledgments for MQTT.
        metric.add_sample('amlen_memory_client_state', {}, memory['ClientStates'])
        yield metric
        return None

class JsonSubscriptionCollector():
    ''' Collector for Subscription endpoint '''
    def __init__(self, endpoint):
        self._endpoint = f'http://{endpoint}/ima/v1/monitor/Subscription'
    def collect(self):
        ''' Collect metrics'''
        metric = Metric('amlen_subscription_message',
                        'Messages in subscriptions', 'gauge')
        try:
            response = json.loads(requests.get(self._endpoint, timeout=10, params={})
                                .content.decode('UTF-8'))
        except Exception as ex:
            print(f'Cannot make a request to {self._endpoint} : {type(ex).__name__}')
            return None

        try:
            for subscription in response['Subscription']:
                labels = {
                    'MessagingPolicy': subscription['MessagingPolicy'],
                    'ClientID': subscription['ClientID'],
                    'SubName': subscription['SubName']
                }
                metric.add_sample('amlen_subscription_message_published', labels,
                                  subscription['PublishedMsgs'])

                metric.add_sample('amlen_subscription_message_buffered', labels,
                                  subscription['BufferedMsgs'])

                metric.add_sample('amlen_subscription_message_buffered_percent', labels,
                                  subscription['BufferedPercent'])

                metric.add_sample('amlen_subscription_message_buffered_peak', labels,
                                  subscription['BufferedMsgsHWM'])
            yield metric
        except KeyError:
            print('Error collecting Subscription data: No Subscription key')
        return None

class JsonEndpointCollector():
    ''' Collector for Endpoint endpoint '''
    def __init__(self, endpoint):
        self._endpoint = f'http://{endpoint}/ima/v1/monitor/Endpoint'
    def collect(self):
        ''' Collect metrics'''

        try:
            params = {'StatType':'ReadMsgs', 'SubType':'History', 'Duration':6}
            response = json.loads(requests.get(self._endpoint, timeout=10, params=params)
                                  .content.decode('UTF-8'))
            metric = Metric('amlen_endpoint_message_rate',
                            'Messages per second', 'gauge')
            msgs_list = response['Endpoint']['Data'].split(',')
            msg_rate = (int(msgs_list[0])-int(msgs_list[1]))/5
            # Specifies the number of messages per second, counted from last 5 seconds
            metric.add_sample('amlen_endpoint_message_rate_incoming', {}, msg_rate)
            yield metric

            response = json.loads(requests.get(self._endpoint, timeout=10).content.decode('UTF-8'))
            endpoints = response['Endpoint']

            metric = Metric('amlen_endpoint', 'Endpoint counters', 'counter')
            for endpoint in endpoints:
                labels = {'endpoint_name': endpoint['Name']}
                # The number of bytes that are sent and received since configuration time.
                metric.add_sample('amlen_endpoint_bytes', labels, endpoint['Bytes'])
                # The number of messages that are sent or received since configuration time.
                metric.add_sample('amlen_endpoint_messages', labels, endpoint['Messages'])
                # Specifies the total number of connections.
                metric.add_sample('amlen_endpoint_total_connections', labels, endpoint['Total'])
                # Specifies the number of connections that failed to connect since reset.
                metric.add_sample('amlen_endpoint_bad_connections', labels,
                                   endpoint['BadConnections'])
            yield metric

            metric = Metric('amlen_endpoint_active', 'Endpoint active connections', 'gauge')
            for endpoint in endpoints:
                labels = {'endpoint_name': endpoint['Name']}
                # Specifies the number of currently active connections.
                metric.add_sample('amlen_endpoint_active_connections', labels, endpoint['Active'])
            yield metric

            metric = Metric('amlen_endpoint_enabled', 'Endpoint is enabled', 'gauge')
            for endpoint in endpoints:
                labels = {'endpoint_name': endpoint['Name']}
                # Specifies whether the endpoint is enabled. If the endpoint is enabled and
                # the LastErrorCode is 0, this indicates that the endpoint is accepting connections.
                metric.add_sample('amlen_endpoint_enabled', labels, endpoint['Enabled'])
            yield metric

            # metric = Metric('amlen_endpoint_info', 'Endpoint information', 'info')
            # for endpoint in endpoints:
            #     labels = {'endpoint_name': endpoint['Name']}
            #     # Specifies the number of microseconds since the unix epoch.
            #     metric.add_sample('amlen_endpoint_info_config_time',
            #                       labels, str(endpoint['ConfigTime']))
            #yield metric

        except KeyError as keyerr:
            print(f'Error collecting Endpoint data: No Endpoint key {keyerr}')
        except Exception as ex:
            print(f'Cannot make a request to {self._endpoint} : {type(ex).__name__}')


class JsonInfoCollector():
    ''' Collector for Status endpoint '''
    def __init__(self, endpoint):
        self._endpoint = f'http://{endpoint}/ima/v1/service/status/Server'
    def collect(self):
        ''' Collect metrics'''
        try:
            response = json.loads(requests.get(self._endpoint, timeout=10)
                              .content.decode('UTF-8'))
        except Exception as ex:
            print(f'Cannot make a request to {self._endpoint} : {type(ex).__name__}')
            return None
        metric = Metric('amlen_info', 'Status metrics counters', 'info')
        try:
            info = response['Server']
            #metric.add_sample('amlen_info_name', {}, info['Name'])
            #metric.add_sample('amlen_info_uid', {}, info['UID'])
            #metric.add_sample('amlen_info_status', {}, info['Status'])
            #metric.add_sample('amlen_info_state', {}, info['State'])
            #metric.add_sample('amlen_info_state_description', {}, info['StateDescription'])
            #metric.add_sample('amlen_info_server_time', {}, info['ServerTime'])
            metric.add_sample('amlen_info_uptime_seconds', {}, info['UpTimeSeconds'])
            #metric.add_sample('amlen_info_uptime_description', {}, info['UpTimeDescription'])
            #metric.add_sample('amlen_info_version', {}, info['Version'])
            #metric.add_sample('amlen_info_error_code', {}, info['ErrorCode'])
            # metric.add_sample('amlen_info_error_message', {}, info['ErrorMessage'])

        except KeyError as keyerr:
            print(f'Error collecting Endpoint data: No Endpoint key: {keyerr}')


        yield metric
        return None


if __name__ == '__main__':
    # Usage: json_exporter.py port endpoint
    start_http_server(int(sys.argv[1]))
    REGISTRY.register(JsonServerCollector(sys.argv[2]))
    REGISTRY.register(JsonMemoryCollector(sys.argv[2]))
    REGISTRY.register(JsonEndpointCollector(sys.argv[2]))
    REGISTRY.register(JsonSubscriptionCollector(sys.argv[2]))
    REGISTRY.register(JsonInfoCollector(sys.argv[2]))
    while True:
        time.sleep(1)
