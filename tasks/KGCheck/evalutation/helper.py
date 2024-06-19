import json
import sys

file_path = ''

def extract_element_by_index(index):
    with open(file_path, 'r') as file:
        data = json.load(file)
    element = data[index]
    instruction = element.get('instruction')
    return instruction


if __name__ == "__main__":
    index = int(sys.argv[1])
    print(extract_element_by_index(index))
