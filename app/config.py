# configuration settings for application
# LIST_VIEW_FIELDS can be used to set email fields to display in list view.
LIST_VIEW_FIELDS = ['Subject', 'From', 'To', 'Date', 'CC', 'BCC', 'Message-ID']
CSRF_ENABLED = True
SECRET_KEY = ''

# ES settings
INDEX = 'test_kaminski'
SETTINGS_BODY = {
                    'index': {
                        'analysis': {
                            'analyzer': {
                                'primary': {
                                    'tokenizer': 'uax_url_email',
                                    'filter': ['standard', 'lowercase']
                                    }, 
                                'folder': {
                                    'tokenizer': 'path_hierarchy'
                                    }
                                }
                            }
                        }
                    }

MAPPING_BODY = {
                'email': {
                    'properties': {
                        'body': {
                            'store': True, 
                            'term_vector': 'with_positions_offsets', 
                            'type': 'string', 
                            'index': 'analyzed', 
                            'analyzer': 'primary'
                            }, 
                        'X-Folder': {
                            'store': True, 
                            'type': 'string', 
                            'index': 'analyzed', 
                            'analyzer': 'folder'}, 
                        'To': {
                            'type': 'string', 
                            'store': True, 
                            'index': 'analyzed', 
                            'analyzer': 'primary'}, 
                        'From': {
                            'type': 'string', 
                            'store': True, 
                            'index': 'analyzed', 
                            'analyzer': 'primary'}, 
                        'CC': {
                            'type': 'string', 
                            'store': True, 
                            'index': 'analyzed', 
                            'analyzer': 'primary'}, 
                        'BCC': {
                            'type': 'string', 
                            'store': True, 
                            'index': 'analyzed', 
                            'analyzer': 'primary'
                            }
                        },
                    'suggest': {
                        'type': 'completion',
                        'index_analyzer': 'simple',
                        'search_analyzer': 'simple',
                        'preserve_separators': False
                        }
                    }
                }
