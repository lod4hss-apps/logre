import yaml, os


# This scripts needs to be called when code base is updated

def update_config_2_1() -> None:
    # Load the old config
    old_config = yaml.safe_load(open('../logre-config.yaml', 'r'), )

    if 'version' not in old_config: 
        # Prepare the new config object
        new_config = {}
        new_config['data_bundles'] = []
        new_config['prefixes'] = []
        new_config['default_data_bundle'] = None
        new_config['sparql_queries'] = []
        
        # Extract information from old config and put it in new one
        if 'endpoints' in old_config:
            for endpoint in old_config['endpoints']:
                if 'data_bundles' in endpoint:
                    for data_bundle in endpoint['data_bundles']:
                        new_data_bundle = {
                            'base_uri': endpoint['base_uri'],
                            'endpoint_technology': endpoint['technology'],
                            'endpoint_url': endpoint['url'],
                            'graph_data_uri': data_bundle['graph_data_uri'],
                            'graph_metadata_uri': data_bundle['graph_metadata_uri'],
                            'graph_model_uri': data_bundle['graph_ontology_uri'],
                            'model_framework': data_bundle['ontology_framework'],
                            'name': data_bundle['name'],
                            'password': endpoint['password'],
                            'prop_comment_uri': data_bundle['comment_property'],
                            'prop_label_uri': data_bundle['label_property'],
                            'prop_type_uri': data_bundle['type_property'],
                            'username': endpoint['username'],
                        }
                        new_config['data_bundles'].append(new_data_bundle) 
                if 'prefixes' in endpoint:
                    for prefix in endpoint['prefixes']:
                        have = set(p['short'] for p in new_config['prefixes'])
                        if prefix['short'] not in have:
                            new_config['prefixes'].append({'short': prefix['short'], 'long': prefix['long']})
        if 'queries' in old_config:
            for query in old_config['queries']:
                new_config['sparql_queries'].append([query['name'], query['text']])

        new_config['version'] = "2.1"

        # Create the content of the new config file
        new_content = yaml.dump(new_config)

        # And write it to disk
        with open('../logre-config.yaml', 'w') as file:
            file.write(new_content)


############ MAIN ############

update_config_2_1()