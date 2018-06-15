import os
import yaml
import pyaml
import json
import hashlib
from st2common.runners.base_action import Action
from st2common.content.utils import get_packs_base_paths
from st2common.constants.pack import MANIFEST_FILE_NAME
from st2client.client import Client
from st2client.models import KeyValuePair

class GenerateFileTemplates(Action):
    def __init__(self, config):
        super(GenerateFileTemplates, self).__init__(config=config)
        token = self.config.get('github_token', None)
        self.github_token = token or None
        self.github_user = self.config.get('github_user', None)

    '''
    preps files from '/opt/stackstorm/bitovi_packs/actions/pack_template'
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

        self.templates_folder = 'pack_template'
        self.templates_dir = '/opt/stackstorm/packs/bitovi_packs/actions/' + self.templates_folder
        self.temp_templates_root = "/opt/stackstorm/tmp_create_{repo}".format(repo=repo)
        self.temp_templates_dir = "{a}/{b}".format(a=self.temp_templates_root, b=self.templates_folder)

        # Prep he tmp directory template files
        os.system("rm -rf {dir}".format(dir=self.temp_templates_root))
        self.makedirs(self.temp_templates_dir)

        # Copy template files from {templates_dir} to {temp_templates_root}
        os.system("cp -rf {a} {b}".format(a=self.templates_dir, b=self.temp_templates_root))

        self._save_obj_to_yaml_file(self.temp_templates_dir, 'pack.yaml', pack_yaml_data)
        self._save_obj_to_yaml_file(self.temp_templates_dir + '/rules', 'watch_pack_commit.yaml', self.get_watch_pack_commit_rule(repo))
        self._save_file_contents(self.temp_templates_dir, 'README.md', self.get_readme(repo, user, description))

        commit_message = "Bootstrap a Bitovi StackStorm Exchange pack repository for pack {repo}".format(repo=repo)
        os.chdir(self.temp_templates_root)
        os.system("git init")
        os.system("git config user.email '{email}'".format(email="mick@bitovi.com"))
        os.system("git config user.name '{name}'".format(name=self.github_user))
        os.system("git add .")
        os.system("git commit -m '{message}'".format(message=commit_message))
        os.system("git remote add origin https://{gu}:{gt}@github.com/{user}/{repo}.git".format(gu=self.github_user, gt=self.github_token, user=user,repo=repo))
        os.system("git push -u origin master")
        os.system("git checkout -b dev")
        os.system("git push -u origin HEAD")

        # Remove the template files
        os.system("rm -rf {dir}".format(dir=self.temp_templates_root))

        return True

    # def run(self, repo, user, homepage, description, pack_yaml_data):
    #     self.client = Client(base_url='http://localhost')

    #     self.templates_folder = 'pack_templates'
    #     self.templates_dir = '/opt/stackstorm/bitovi-stackstorm-exchange/bitovi_packs/actions/' + self.templates_folder
    #     self.temp_templates_root = "/opt/stackstorm/tmp_create_{repo}".format(repo=repo)
    #     self.temp_templates_dir = "{a}/{b}".format(a=self.temp_templates_root, b=self.templates_folder)

    #     # Prep he tmp directory template files
    #     os.system("rm -rf {dir}".format(dir=self.temp_templates_root))
    #     self.makedirs(self.temp_templates_dir)

    #     # Copy template files from {templates_dir} to {temp_templates_dir}
    #     os.system("cp -rf {a} {b}".format(a=self.templates_dir, b=self.temp_templates_root))


    #     staged_uploads = [{
    #         "path": "/pack.yaml",
    #         "message": "Bootstrap a Bitovi StackStorm Exchange pack repository for pack ${PACK}.",
    #         "content": self.obj_to_yaml_content(pack_yaml_data)
    #     },{
    #         "path": "/.gitignore",
    #         "message": "Bootstrap process: add gitignore",
    #         "content": self.get_file_contents(self.temp_templates_dir + "/.gitignore")
    #     },{
    #         "path": "/rules/watch_pack_commit.yaml",
    #         "message": "Bootstrap process: add /rules/watch_pack_commit.yaml (speeds up pack development)",
    #         "content": self.obj_to_yaml_content(self.get_watch_pack_commit_rule(repo))
    #     },{
    #         "path": "/README.md",
    #         "message": "Bootstrap process: add readme",
    #         "content": self.get_readme(repo, user, description)
    #     }]

    #     # Remove the template files
    #     os.system("rm -rf {dir}".format(dir=self.temp_templates_root))

    #     return staged_uploads

    def get_file_contents(self, file):
        with open(file, 'r') as myfile:
            data=myfile.read()
        return data

    def obj_to_yaml_content(self, yaml_obj):
        tmp_yaml_file_dir = self.temp_templates_root + "/obj_to_yaml_content"
        tmp_yaml_file = tmp_yaml_file_dir + "/" + self.hash_obj(yaml_obj) + ".yaml"

        self._save_obj_to_yaml_file(tmp_yaml_file, yaml_obj)

        # get written file contents
        data = self.get_file_contents(tmp_yaml_file)

        # cleanup
        os.system("rm -rf {tmp_yaml_file_dir}".format(tmp_yaml_file_dir=tmp_yaml_file_dir))

        return data



    def get_readme(self, repo, org, description):
        return """
        # {repo} pack

        {description}

        ## Actions

        ### foo
        Sample action.  Returns `bar`

        ## Installation
        - Use `bitovi_packs.install` to install `{repo}` from [GitHub](https://github.com/{org}/{repo})        
        """.format(repo=repo, description=description, org=org)

    def get_watch_pack_commit_rule(self, repo):
        watch_pack_commit_path = self.temp_templates_dir + "/rules/watch_pack_commit.yaml"
        rule_watch_pack_commit = self._parse_yaml_file(watch_pack_commit_path)
        trigger_filepath = "/opt/stackstorm/bitovi-stackstorm-exchange/" + repo + "/.git/logs/refs/heads/dev"
        rule_watch_pack_commit["trigger"]["parameters"]["file_path"] = trigger_filepath
        return rule_watch_pack_commit

    def _parse_yaml_file(self, file_path):
        with open(file_path) as data_file:
            details = yaml.load(data_file)
        return details

    def _save_obj_to_yaml_file(self, file_path_root, file, yaml_obj):
        # ensure dirs exist
        self.makedirs(file_path_root)

        file_path = "{r}/{f}".format(r=file_path_root, f=file)

        if not os.path.isfile(file_path):
            os.system("touch {file}".format(file=file_path))

        if '__dict__' in yaml_obj:
            yaml_obj = yaml_obj.__dict__

        # write yaml to file
        with open(file_path, 'w+') as f:
            pyaml.dump(yaml_obj, f)

    def _save_file_contents(self, file_path_root, file, contents):
        # ensure dirs exist
        self.makedirs(file_path_root)

        file_path = "{r}/{f}".format(r=file_path_root, f=file)

        if not os.path.isfile(file_path):
            os.system("touch {file}".format(file=file_path))

        with open(file_path, 'w+') as f:
            f.write(contents)

    def hash_obj(self, obj):
        h = hashlib.new('ripemd160')
        h.update(json.dumps(obj))
        return h.hexdigest()

    def makedirs(self, dirs):
        if not os.path.isdir(dirs):
            os.makedirs(dirs)