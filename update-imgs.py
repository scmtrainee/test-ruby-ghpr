#!/usr/local/bin/python3
# from optparse import OptionParser
import argparse
from pathlib import Path
import subprocess
import yaml, json
import re

def get_latest_tag(sn, tsuffix):
    repo_root = 'tcoreintegrity'
    query = f"'[?ends_with(@, `{tsuffix}`) == `true`]|[0]'"
    cmd = [
        'az', 'acr', 'repository', 'show-tags', '--name', 'integrity',
        '--repository', f"{repo_root}/{sn}",
        '--orderby', 'time_desc', '--query', query
    ]
    response_data = subprocess.check_output(' '.join(cmd), shell=True)
    return json.loads(response_data or 'null')

def get_img_tags(syml,sfx):
    img_tags = {}
    with open(syml) as f:
        sdata = yaml.load(f, Loader=yaml.FullLoader)
        for svcs in sdata.values():
            for sname in svcs:
                l_tag = get_latest_tag(sname, sfx)
                img_tags[sname] = l_tag
                if args.verbose:
                    res = "Updating ... {:<40}{:<30}".format(sname, str(l_tag))
                    print(res)
    return img_tags
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="get latest image tags for services to be deployed")
    parser.add_argument("-e", "--environment",
                            dest="env",
                            help="specify the environment to update images")
    parser.add_argument('-v', '--verbose', dest="verbose", default=False, action="store_true")

    args = parser.parse_args()
    
    if args.env:
        services_file = Path(f"{args.env}-services-to-deploy.yaml")
        images_file = f"{args.env}-images.yaml"
        env_tagmap = { 
                        'dev': '-develop',
                        'qa': '-rc',
                        'qa2': '-rc',
                        'train': '-release',
                        'prod': '-release',
                        'uat': '-release'
                        }
        if services_file.exists():
            img_values = get_img_tags(services_file, env_tagmap[args.env])
            with open(images_file, 'r') as file :
                filedata = file.read()
            for f_key, f_value in img_values.items():
                search_string = f_key + '.*'
                if f_value: 
                    replace_string = f"{f_key}:{f_value}"
                else:
                    continue
                filedata = re.sub( search_string, replace_string, filedata)
            with open(images_file, 'w') as file:
                file.write(filedata)
                print("\nupdated - ", images_file)
        else:
            print(f"*** {services_file} missing *** \n")
            parser.print_help()
    else:
        parser.print_help()