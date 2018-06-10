import os
import yaml

from st2common.runners.base_action import Action
from st2common.content.utils import get_packs_base_paths
from st2common.constants.pack import MANIFEST_FILE_NAME


class GetPackDependencies(Action):
    '''
    Gets pack dependencies from pack.yml files
    '''
    def run(self, packs, stackstorm_environment="dev"):
        """
        :param pack: Installed Pack Name to get info about
        :type pack: ``str``
        """
        self.stackstorm_environment = stackstorm_environment
        pack_dependencies = []

        for pack in packs:
            deps = self._get_pack_dependencies(pack)
            if deps:
                dep = {
                    "pack": pack,
                    "dependencies": deps
                }
                pack_dependencies.append(dep)

        if not pack_dependencies:
            return (True, [])

        return (True, pack_dependencies)

    def _get_pack_dependencies(self, pack):
        packs_base_paths = get_packs_base_paths()

        pack_path = None
        metadata_file = None
        for packs_base_path in packs_base_paths:
            pack_path = os.path.join(packs_base_path, pack)
            pack_yaml_path = os.path.join(pack_path, MANIFEST_FILE_NAME)

            if os.path.isfile(pack_yaml_path):
                metadata_file = pack_yaml_path
                break

        # Pack doesn't exist, finish execution normally with empty metadata
        if not os.path.isdir(pack_path):
            return []

        if not metadata_file:
            error = ('Pack "%s" doesn\'t contain pack.yaml file.' % (pack))
            raise Exception(error)

        try:
            details = self._parse_yaml_file(metadata_file)
        except Exception as e:
            error = ('Pack "%s" doesn\'t contain a valid pack.yaml file: %s' % (pack, str(e)))
            raise Exception(error)

        # dev mode
        #  if dev_dependencies are specified, use them
        #  else use dependencies
        # else
        #  use dependencies
        deps = []
        if self.stackstorm_environment == "dev":
            if 'dev_dependencies' in details:
                deps = details["dev_dependencies"]
            elif 'dependencies' in details:
                deps = details["dependencies"]
        else:
            if 'dependencies' in details:
                deps = details["dependencies"]

        return deps

    def _parse_yaml_file(self, file_path):
        with open(file_path) as data_file:
            details = yaml.load(data_file)
        return details
