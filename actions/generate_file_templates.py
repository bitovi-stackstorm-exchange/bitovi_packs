import os
import yaml
import json
import hashlib
from st2common.runners.base_action import Action
from st2common.content.utils import get_packs_base_paths
from st2common.constants.pack import MANIFEST_FILE_NAME
from st2client.client import Client
from st2client.models import KeyValuePair

class GenerateFileTemplates(Action):
    '''
    preps files from '/opt/stackstorm/bitovi_packs/actions/pack_templates'
    to be staged for upload to github

    Returns [{
        filename,        # the file name (full path from project root)"
        commit_message,  # the commit message
        content          # the file content to upload
    }]
    new_repo.create_file("new_file.txt", "init commit", "file_content ------ ")
    '''

    

    def run(self, repo, user, homepage, description, pack_yaml_data):
        self.client = Client(base_url='http://localhost')

        self.templates_dir = '/opt/stackstorm/bitovi_packs/actions/pack_templates'
        self.temp_templates_dir = "/opt/stackstorm/tmp_create_" + repo

        # Copy template files from {templates_dir} to {temp_templates_dir}
        os.system(f"cp -rf {self.templates_dir} {self.temp_templates_dir}")


        staged_uploads = [{
            "filename": "/pack.yaml",
            "commit_message": "Bootstrap a Bitovi StackStorm Exchange pack repository for pack ${PACK}."
            "content": self.obj_to_yaml_content(pack_yaml_data)
        },{
            "filename": "/.gitignore",
            "commit_message": "Bootstrap process: add gitignore"
            "content": self.get_file_contents(self.temp_templates_dir + "/.gitignore")
        },{
            "filename": "/rules/watch_pack_commit.yaml",
            "commit_message": "Bootstrap process: add /rules/watch_pack_commit.yaml (speeds up pack development)"
            "content": self.obj_to_yaml_content(self.get_watch_pack_commit_rule(self.temp_templates_dir, repo))
        },{
            "filename": "/README.md",
            "commit_message": "Bootstrap process: add readme"
            "content": self.get_readme(repo, user, description)
        }]

        # Remove the template files
        os.system(f"rm -rf {self.temp_templates_dir}")

        return staged_uploads

    def get_file_contents(self, file):
        with open(file, 'r') as myfile:
            data=myfile.read()
        return data

    def obj_to_yaml_content(self, yaml_obj):
        tmp_yaml_file = self.temp_templates_dir + "/obj_to_yaml_content/" + self.hash_obj(yaml_obj) + ".yaml"
        with open(tmp_yaml_file, 'w') as yaml_file:
            yaml.dump(yaml_obj, yaml_file, default_flow_style=False)
        data = self.get_file_contents(tmp_yaml_file)
        os.system(f"rm -rf {tmp_yaml_file}")
        return data



    def get_readme(self, repo, org, description):
        return f"""
        # {repo} pack

        {description}

        ## Actions

        ### foo
        Sample action.  Returns `bar`

        ## Installation
        - Use `bitovi_packs.install` to install `{repo}` from [GitHub](https://github.com/{org}/{repo})        
        """

    def get_watch_pack_commit_rule(self, temp_templates_dir, repo):
        watch_pack_commit_path = temp_templates_dir + "/rules/watch_pack_commit.yaml"
        rule_web_pack_commit = self._parse_yaml_file(watch_pack_commit_path)
        trigger_filepath = "/opt/stackstorm/bitovi-stackstorm-exchange/" + repo + "/.git/logs/refs/heads/dev"
        rule_watch_pack_commit["trigger"]["parameters"]["file_path"] = trigger_filepath
        return rule_watch_pack_commit

    def _parse_yaml_file(self, file_path):
        with open(file_path) as data_file:
            details = yaml.load(data_file)
        return details

    def hash_obj(self, obj):
        h = hashlib.new('ripemd160')
        h.update(json.dumps(obj))
        return h.hexdigest()