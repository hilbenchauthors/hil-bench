import argparse
import os

from ruamel.yaml import YAML

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "configs")
YAML_READER = YAML()
YAML_READER.preserve_quotes = True


def make_and_save_template(
    template_name: str, model_name: str, model_suffix: str, subdir: str = ""
) -> None:
    config_subdir = os.path.join(CONFIG_DIR, subdir) if subdir else CONFIG_DIR
    new_config_path = os.path.join(config_subdir, template_name + f"_{model_suffix}" + ".yaml")
    template_path = os.path.join(config_subdir, template_name + ".yaml")
    with open(template_path, "r") as f:
        config = YAML_READER.load(f)
    config["agent"]["model"]["name"] = model_name
    with open(new_config_path, "w") as f:
        YAML_READER.dump(config, f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--template_name", "-t", type=str, required=True)
    parser.add_argument("--model_name", "-m", type=str, required=True)
    parser.add_argument("--model_suffix", "-s", type=str, required=True)
    parser.add_argument("--subdir", "-d", type=str, default="", help="Subdirectory within configs/")
    args = parser.parse_args()
    make_and_save_template(args.template_name, args.model_name, args.model_suffix, args.subdir)
