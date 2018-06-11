import os
import yaml
import json
from st2common.runners.base_action import Action
from st2common.content.utils import get_packs_base_paths
from st2common.constants.pack import MANIFEST_FILE_NAME
from st2client.client import Client
from st2client.models import KeyValuePair

class FilterPacksNotInstalled(Action):

    

    '''
    add packs that do not exist in the root_execution_id's to dependencies list as 'install' status
    Return packs that do not exist in the root_execution_id's dependencies list
    '''
    def run(self, packs, dependencies_list_name):
        self.client = Client(base_url='http://localhost')


        # check keystore
        dependencies_list_json = self.client.keys.get_by_name(name=dependencies_list_name)
        dependencies_list = []
        if dependencies_list_json:
            dependencies_list = json.loads(dependencies_list_json.value)


        packs_to_install = []
        for pack in packs:
            if pack not in dependencies_list and pack not in packs_to_install:
                packs_to_install.append(pack)
                dependencies_list.append(pack)

        # add to keystore { "status": "install", "execution_id": execution_id }
        self.client.keys.update(KeyValuePair(name=dependencies_list_name, value=json.dumps(dependencies_list)))

        return packs_to_install

