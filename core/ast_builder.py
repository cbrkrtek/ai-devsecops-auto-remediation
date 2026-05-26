import json
from dockerfile_parse import DockerfileParser

def build_dockerfile_ast(file_content: str) -> dict:
    parser = DockerfileParser()
    parser.content = file_content
    
    ast_nodes = []
    for index, item in enumerate(parser.structure):
        node = {
            "node_id": index,
            "instruction": item['instruction'].upper(),
            "value": item['value'].strip() if item['value'] else ""
        }
        ast_nodes.append(node)
        
    ast_tree = {
        "type": "Dockerfile_AST",
        "length": len(ast_nodes),
        "nodes": ast_nodes
    }
    return ast_tree