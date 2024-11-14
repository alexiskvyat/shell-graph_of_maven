import argparse
import requests
import xml.etree.ElementTree as ET
from graphviz import Digraph
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description="Maven Dependency Visualizer")
    parser.add_argument('--graphviz_path', type=str, required=True, help="Path to output Graphviz file")
    parser.add_argument('--package_name', type=str, required=True, help="Name of the Maven package (format: groupId:artifactId:version)")
    parser.add_argument('--max_depth', type=int, required=True, help="Maximum depth of dependencies to explore")
    parser.add_argument('--repository_url', type=str, required=True, help="URL or local path to the Maven repository")
    return parser.parse_args()

from pathlib import Path

def fetch_pom(group_id, artifact_id, version, repository_url):
    """Fetches the POM file for the specified artifact."""
    # Remove 'file://' prefix for local paths
    if repository_url.startswith("file://"):
        repository_url = repository_url[7:]

    # Expand '~' to the user's home directory
    repository_url = str(Path(repository_url).expanduser())

    pom_path = f"{repository_url}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    print(f"Fetching POM from local path: {pom_path}")

    # Check if POM file exists locally
    if not os.path.exists(pom_path):
        print(f"Error: POM file not found at {pom_path}")
        return None

    with open(pom_path, 'r') as f:
        return f.read()

def parse_dependencies(pom_xml):
    """Extracts dependencies from a POM XML file."""
    dependencies = []
    root = ET.fromstring(pom_xml)
    for dependency in root.findall(".//dependency"):
        group_id = dependency.find("groupId").text
        artifact_id = dependency.find("artifactId").text
        version = dependency.find("version")
        dependencies.append((group_id, artifact_id, version.text if version is not None else None))
    return dependencies

def build_dependency_graph(graph, group_id, artifact_id, version, repository_url, depth, max_depth):
    """Recursively builds a dependency graph."""
    if depth > max_depth:
        return
    pom_xml = fetch_pom(group_id, artifact_id, version, repository_url)
    if pom_xml is None:
        return

    dependencies = parse_dependencies(pom_xml)
    for dep_group_id, dep_artifact_id, dep_version in dependencies:
        if dep_version is None:
            dep_version = "latest"  # placeholder if no version is specified

        node_label = f"{dep_group_id}:{dep_artifact_id}:{dep_version}"
        graph.node(node_label)
        graph.edge(f"{group_id}:{artifact_id}:{version}", node_label)

        build_dependency_graph(graph, dep_group_id, dep_artifact_id, dep_version, repository_url, depth + 1, max_depth)

def main():
    args = parse_arguments()
    group_id, artifact_id, version = args.package_name.split(":")

    # Create the dependency graph
    graph = Digraph(format='png')
    graph.node(f"{group_id}:{artifact_id}:{version}")

    # Build the graph
    build_dependency_graph(graph, group_id, artifact_id, version, args.repository_url, 1, args.max_depth)

    # Save the graph
    output_path = args.graphviz_path
    graph.render(output_path)
    print(f"Dependency graph saved to {output_path}.png")

if __name__ == "__main__":
    main()
