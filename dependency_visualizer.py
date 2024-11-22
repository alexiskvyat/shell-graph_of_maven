import argparse
import requests
import xml.etree.ElementTree as ET
from graphviz import Digraph


def parse_arguments():
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Визуализатор зависимостей Maven")
    parser.add_argument('--graphviz_path', type=str, required=True, help="Путь для сохранения файла Graphviz (без расширения)")
    parser.add_argument('--package_name', type=str, required=True, help="Имя пакета Maven (формат: groupId:artifactId:version)")
    parser.add_argument('--max_depth', type=int, required=True, help="Максимальная глубина дерева зависимостей")
    parser.add_argument('--repository_url', type=str, required=True, help="Базовый URL Maven-репозитория")
    return parser.parse_args()


def fetch_pom(group_id, artifact_id, version, repository_url):
    """Загружает POM-файл для указанного пакета Maven."""
    url = f"{repository_url}/{group_id.replace('.', '/')}/{artifact_id}/{version}/{artifact_id}-{version}.pom"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Не удалось загрузить POM с {url}: {e}")
        return None


def parse_dependencies(pom_content):
    """Парсит содержимое POM-файла для извлечения зависимостей."""
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
        print(f"Ошибка при парсинге содержимого POM: {e}")
    return dependencies


def create_graph_hierarchy(graph, group_id, artifact_id, version, is_root=False):
    """
    Создает иерархические узлы для groupId, artifactId и version.
    Флаг `is_root` указывает, является ли это корневым узлом.
    """
    # Разбиваем groupId на части
    group_parts = group_id.split('.')
    previous_node = None

    # Если это корневой узел, обрабатываем его иначе
    if is_root:
        node_name = group_id
        graph.node(node_name, label=group_id, shape="folder")
        previous_node = node_name
    else:
        # Создаем узлы для каждой части groupId
        for i, part in enumerate(group_parts):
            node_name = ".".join(group_parts[:i + 1])
            graph.node(node_name, label=part, shape="folder")
            if previous_node:
                graph.edge(previous_node, node_name)
            previous_node = node_name

    # Добавляем узел для artifactId
    artifact_node = f"{group_id}.{artifact_id}"
    graph.node(artifact_node, label=artifact_id, shape="box")
    graph.edge(previous_node, artifact_node)

    # Добавляем узел для version
    version_node = f"{artifact_node}-v{version}"
    graph.node(version_node, label=version, shape="box")
    graph.edge(artifact_node, version_node)

    return version_node


def build_dependency_graph(graph, group_id, artifact_id, version, repository_url, depth, max_depth, visited, is_root=False):
    """
    Рекурсивно строит граф зависимостей и устанавливает связи.
    """
    if depth > max_depth or (group_id, artifact_id, version) in visited:
        return

    visited.add((group_id, artifact_id, version))

    # Создаем иерархию для текущего пакета
    current_node = create_graph_hierarchy(graph, group_id, artifact_id, version, is_root)

    # Загружаем POM-файл и парсим зависимости
    pom_content = fetch_pom(group_id, artifact_id, version, repository_url)
    if not pom_content:
        return

    dependencies = parse_dependencies(pom_content)
    for dep_group_id, dep_artifact_id, dep_version in dependencies:
        # Рекурсивно строим граф для зависимостей
        dependency_node = build_dependency_graph(
            graph, dep_group_id, dep_artifact_id, dep_version,
            repository_url, depth + 1, max_depth, visited
        )
        if dependency_node:
            # Связываем текущий пакет с его зависимостями
            graph.edge(current_node, dependency_node)


def main():
    """Основная функция для генерации графа зависимостей Maven."""
    args = parse_arguments()

    # Разбираем данные о пакете
    group_id, artifact_id, version = args.package_name.split(':')
    graph = Digraph(format='png')

    # Настраиваем внешний вид графа
    graph.attr(rankdir="TB", size="20,20", dpi="300")
    graph.attr('node', fontname="Arial", fontsize="12")

    visited = set()

    # Создаем корневой узел с флагом `is_root`
    build_dependency_graph(graph, group_id, artifact_id, version, args.repository_url, 0, args.max_depth, visited, is_root=True)

    output_path = args.graphviz_path
    dot_path = f"{output_path}.dot"

    # Сохраняем DOT-файл
    graph.save(dot_path)
    print(f"DOT-файл Graphviz сохранен по пути: {dot_path}")

    # Рендерим граф
    try:
        output_file = graph.render(output_path)
        print(f"Граф зависимостей сгенерирован и сохранен в {output_file}")
    except Exception as e:
        print(f"Ошибка при рендеринге графа: {e}")
        print(f"Проверьте DOT-файл по пути: {dot_path}")


if __name__ == "__main__":
    main()
