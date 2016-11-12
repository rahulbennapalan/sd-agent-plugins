"""
  Server Density Plugin
  Aerospike Server

  Version: 1.0.0
"""

import json
import logging
import sys
import time
import aerospike


class Aerospike(object):

    def __init__(self, agent_config, checks_logger, raw_config):

        self.agent_config = agent_config
        self.checks_logger = checks_logger
        self.raw_config = raw_config
        self.host = self.raw_config['Aerospike'].get('host', 'localhost')
        self.port = int(self.raw_config['Aerospike'].get('port', '3000'))
        self.namespaces = []
        if 'namespaces' in self.raw_config['Aerospike'] and len(self.raw_config['Aerospike']['namespaces']) > 0:
            for namespace in self.raw_config['Aerospike'].get('namespaces').split(','):
                self.namespaces.append(namespace.strip())

    def __get_dict(self, data):

        data_dict = {}
        data_splits = data.split(';')
        for data_split in data_splits:
            splits = data_split.split('=')
            name = splits[0]
            value = splits[1]
            converted = False

            # try converting boolean values
            if value == 'true':
                value = True
                converted = True
            elif value == 'false':
                value = False
                converted = True

            if not converted:
                try:
                    # try converting integer values
                    value = int(value)
                except (ValueError, TypeError):
                    # some values are text rather numbers
                    # fail and move on
                    pass

            data_dict[name] = value

        return data_dict

    def run(self):

        aerospike_stats = {
            'failed': False
        }

        try:
            config = {
                'hosts': [(self.host, self.port)]
            }
            client = aerospike.client(config).connect()
            node_statistics = client.info_node(host=(self.host, self.port), command='statistics')
            node_statistics = node_statistics[len('statistics'):].strip()    # remove title
            aerospike_stats.update(self.__get_dict(node_statistics))
            for namespace in self.namespaces:
                namespace_statistics = client.info_node(host=(self.host, self.port), command='namespace/' + namespace)
                namespace_statistics = namespace_statistics[len('namespace/' + namespace):].strip()    # remove title
                aerospike_stats['namespace-' + namespace] = {}
                aerospike_stats['namespace-' + namespace].update(self.__get_dict(namespace_statistics))
        except:
            aerospike_stats['failed'] = True

        return aerospike_stats


if __name__ == '__main__':
    """Standalone test
    """

    raw_agent_config = {
        'Aerospike': {
            'host': 'localhost',
            'port': '3000',
            'namespaces': 'test1,test2'
        }
    }

    main_checks_logger = logging.getLogger('Aerospike')
    main_checks_logger.setLevel(logging.DEBUG)
    main_checks_logger.addHandler(logging.StreamHandler(sys.stdout))
    aerospike_check = Aerospike({}, main_checks_logger, raw_agent_config)

    while True:
        try:
            print json.dumps(aerospike_check.run(), indent=4, sort_keys=True)
        except:
            main_checks_logger.exception('Unhandled exception')
        finally:
            time.sleep(60)
