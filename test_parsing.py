
from stac_manager.utils.field_ops import parse_field_path

def test_parsing():
    cases = [
        ('assets."ANG.txt".alternate', ['assets', 'ANG.txt', 'alternate']),
        ('assets.\'MTL.json\'.href', ['assets', 'MTL.json', 'href']),
        ('simple.path', ['simple', 'path']),
        ('properties.dgeo:cids', ['properties', 'dgeo:cids'])
    ]
    
    for input_path, expected in cases:
        result = parse_field_path(input_path)
        print(f"Input: {input_path}")
        print(f"Result: {result}")
        if result != expected:
            print(f"FAILURE: Expected {expected}, got {result}")
        else:
            print("SUCCESS")
        print("-" * 20)

if __name__ == "__main__":
    test_parsing()
