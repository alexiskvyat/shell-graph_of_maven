import argparse
import requests
import xml.etree.ElementTree as ET
from graphviz import Digraph

def parse_arguments():
    parser = argparse.ArgumentParser(description="Maven Dependency Visualizer")
    parser.add_argument('--graphviz_path', type=str, required=True, help="Path to save the Graphviz file (without extension)")
    parser.add_argument('--package_name', type=str, required=True, help="Maven package name (format: groupId:artifactId:version)")
    parser.add_argument('--max_depth', type=int, required=True, help="Maximum depth of dependency tree to explore")
    parser.add_argument('--repository_url', type=str, required=True, help="Base URL of the Maven repository")
    return parser.parse_args()


def sanitize_label(label):
    """Sanitizes labels for Graphviz compatibility."""
    label = label.replace(":", "_")   # Replace colon with underscore
    label = label.replace(".", "_")   # Replace dot with underscore
    label = label.replace("-", "_")   # Replace dash with underscore
    label = label.replace(",", "_")   # Replace comma with underscore
    label = label.replace("\"", "\\\"")  # Escape quotes
    label = label.replace("\\", "\\\\")  # Escape backslashes
    return label


def fetch_pom(group_id, artifact_id, version, repository_url):
    if version in {"LATEST", "RELEASE"}:
        print(f"Skipping dependency {group_id}:{artifact_id}:{version} - 'LATEST' and 'RELEASE' are not supported.")
        return None
    
    url = f"{repository_url}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    try:
        response = requests.get(url, timeout=10)  # Reduced timeout for speed
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch POM from {url}: {e}")
        return None


def parse_dependencies(pom_content):
    dependencies = []
    try:
        root = ET.fromstring(pom_content)
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
        for dependency in root.findall('.//m:dependency', ns):
            group_id = dependency.find('m:groupId', ns).text
            artifact_id = dependency.find('m:artifactId', ns).text
            version = dependency.find('m:version', ns)
            if version is not None:
                dependencies.append((group_id, artifact_id, version.text))
            else:
                print(f"Skipping dependency {group_id}:{artifact_id} - version is missing.")
    except ET.ParseError as e:
        print(f"Error parsing POM content: {e}")
    return dependencies


def build_dependency_graph(graph, group_id, artifact_id, version, repository_url, depth, max_depth, visited):
    if depth > max_depth or (group_id, artifact_id, version) in visited:
        return

    visited.add((group_id, artifact_id, version))

    # Create label for the package and sanitize it
    label = sanitize_label(f"{group_id}:{artifact_id}:{version}")
    
    # Add a subgraph to represent the "folder" or group (e.g., com.example)
    group_parts = group_id.split(".")
    subgraph_name = "_".join(group_parts)  # Create subgraph name like "com_example"
    
    with graph.subgraph(name=f"cluster_{subgraph_name}") as c:
        c.attr(style='filled', color='lightgray')  # Color the folder cluster
        c.node(f"{subgraph_name}")  # Add the "folder" as a node
        
        # Add the actual package node inside the folder cluster
        c.node(label)

    # Fetch the POM file
    pom_content = fetch_pom(group_id, artifact_id, version, repository_url)
    if not pom_content:
        return

    dependencies = parse_dependencies(pom_content)
    for dep_group_id, dep_artifact_id, dep_version in dependencies:
        dep_label = sanitize_label(f"{dep_group_id}:{dep_artifact_id}:{dep_version}")
        # Create edge between current package and its dependency
        graph.edge(label, dep_label)
        # Recursively build graph for dependencies
        build_dependency_graph(graph, dep_group_id, dep_artifact_id, dep_version, repository_url, depth + 1, max_depth, visited)


def main():
    args = parse_arguments()

    group_id, artifact_id, version = args.package_name.split(':')
    graph = Digraph(format='png')  # Generate PNG by default

    visited = set()
    build_dependency_graph(graph, group_id, artifact_id, version, args.repository_url, 0, args.max_depth, visited)

    output_path = args.graphviz_path
    dot_path = f"{output_path}.dot"

    # Save the .dot file for inspection
    graph.save(dot_path)
    print(f"Graphviz DOT file saved at: {dot_path}")

    # Generate PNG
    try:
        output_file = graph.render(output_path)
        print(f"Dependency graph generated and saved to {output_file}")
    except Exception as e:
        print(f"Error rendering graph: {e}")
        print(f"Check the DOT file at: {dot_path}")


if __name__ == "__main__":
    main()
