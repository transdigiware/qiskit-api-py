'''
Configuration Variables to use in test mode
'''

import os

if 'QX_API_TOKEN' in os.environ:
    API_TOKEN = os.environ['QX_API_TOKEN']
else:
    API_TOKEN = 'YOUR_API_TOKEN'
