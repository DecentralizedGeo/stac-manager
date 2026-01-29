
import yaml

yaml_content = """
field_mapping:
  assets.ANG.txt.alternate: "source"
  'assets."ANG.txt".alternate': "source_quoted"
"""

data = yaml.safe_load(yaml_content)
for k, v in data['field_mapping'].items():
    print(f"Key: {k}, Value: {v}")

from stac_manager.utils.field_ops import parse_field_path

print("\nParsing keys:")
for k in data['field_mapping']:
    print(f"'{k}' -> {parse_field_path(k)}")
