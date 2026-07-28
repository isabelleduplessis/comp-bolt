"""Read and write .bolt.yml metadata files."""

import yaml


def load_yaml(path):
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data or {}


def save_yaml(path, data):
    with open(path, "w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
