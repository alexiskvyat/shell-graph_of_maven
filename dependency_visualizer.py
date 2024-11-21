import argparse
import requests
import xml.etree.ElementTree as ET
from graphviz import Digraph


def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(description="Maven Dependency Visualizer")
    parser.add_argument('--graphviz_path', type=str, required=True, help="Path to save the Graphviz file (without extension)")
    parser.add_argument('--package_name', type=str, required=True, help="Maven package name (format: groupId:artifactId:version)")
    parser.add_argument('--max_depth', type=int, required=True, help="Maximum depth of dependency tree to explore")
    parser.add_argument('--repository_url', type=str, required=True, help="Base URL of the Maven repository")
    return parser.parse_args()


def fetch_pom(group_id, artifact_id, version, repository_url):
    """Fetches the POM file for the given Maven package."""
    url = f"{repository_url}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch POM from {url}: {e}")
        return None


def parse_dependencies(pom_content):
    """Parses the POM content to extract dependencies."""
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
    except ET.ParseError as e:
        print(f"Error parsing POM content: {e}")
    return dependencies


def create_graph_hierarchy(graph, group_id, artifact_id, version):
    """
    Creates hierarchical nodes for groupId, artifactId, and version.
    """
    # Split groupId into folders
    group_parts = group_id.split('.')
    previous_node = None

    # Create nodes for each folder in groupId
    for i, part in enumerate(group_parts):
        node_name = ".".join(group_parts[:i + 1])
        graph.node(node_name, label=part, shape="folder")
        if previous_node:
            graph.edge(previous_node, node_name)
        previous_node = node_name

    # Add artifactId node
    artifact_node = f"{group_id}.{artifact_id}"
    graph.node(artifact_node, label=artifact_id, shape="box")
    graph.edge(previous_node, artifact_node)

    # Add version node explicitly, without treating it as a port
    version_node = f"{artifact_node}-v{version}"
    graph.node(version_node, label=version, shape="box")
    graph.edge(artifact_node, version_node)

    return version_node


def build_dependency_graph(graph, group_id, artifact_id, version, repository_url, depth, max_depth, visited):
    """
    Recursively builds the dependency graph and establishes connections.
    """
    if depth > max_depth or (group_id, artifact_id, version) in visited:
        return

    visited.add((group_id, artifact_id, version))

    # Create the graph hierarchy for the current package
    current_node = create_graph_hierarchy(graph, group_id, artifact_id, version)

    # Fetch the POM and parse dependencies
    pom_content = fetch_pom(group_id, artifact_id, version, repository_url)
    if not pom_content:
        return

    dependencies = parse_dependencies(pom_content)
    for dep_group_id, dep_artifact_id, dep_version in dependencies:
        # Recursively build the graph for dependencies
        dependency_node = build_dependency_graph(
            graph, dep_group_id, dep_artifact_id, dep_version,
            repository_url, depth + 1, max_depth, visited
        )
        if dependency_node:
            # Link the current package to its dependencies
            graph.edge(current_node, dependency_node)


def main():
    """Main function to generate the Maven dependency graph."""
    args = parse_arguments()

    # Parse package details
    group_id, artifact_id, version = args.package_name.split(':')
    graph = Digraph(format='png')

    # Configure graph appearance
    graph.attr(rankdir="TB", size="20,20", dpi="300")
    graph.attr('node', fontname="Arial", fontsize="12")

    visited = set()
    build_dependency_graph(graph, group_id, artifact_id, version, args.repository_url, 0, args.max_depth, visited)

    output_path = args.graphviz_path
    dot_path = f"{output_path}.dot"

    # Save DOT file
    graph.save(dot_path)
    print(f"Graphviz DOT file saved at: {dot_path}")

    # Render the graph
    try:
        output_file = graph.render(output_path)
        print(f"Dependency graph generated and saved to {output_file}")
    except Exception as e:
        print(f"Error rendering graph: {e}")
        print(f"Check the DOT file at: {dot_path}")


if __name__ == "__main__":
    main()
