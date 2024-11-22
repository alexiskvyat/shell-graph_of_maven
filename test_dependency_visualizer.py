import unittest
from unittest.mock import patch, MagicMock
from graphviz import Digraph
import requests
from dependency_visualizer import fetch_pom, parse_dependencies, create_graph_hierarchy, build_dependency_graph


class TestDependencyVisualizer(unittest.TestCase):

    @patch('requests.get')
    def test_fetch_pom(self, mock_get):
        """Test fetching POM file."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<project><dependencies></dependencies></project>"
        mock_get.return_value = mock_response

        # Успешный запрос
        pom = fetch_pom("com.example", "my-lib", "1.0", "http://localhost:8000")
        self.assertEqual(pom, "<project><dependencies></dependencies></project>")

        # Ошибка сети
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        pom = fetch_pom("com.example", "my-lib", "1.0", "http://localhost:8000")
        self.assertIsNone(pom)

    def test_parse_dependencies(self):
        """Test parsing dependencies from POM content."""
        pom_content = """
        <project xmlns="http://maven.apache.org/POM/4.0.0">
            <dependencies>
                <dependency>
                    <groupId>org.example</groupId>
                    <artifactId>example-lib</artifactId>
                    <version>1.0.0</version>
                </dependency>
            </dependencies>
        </project>
        """
        dependencies = parse_dependencies(pom_content)
        self.assertEqual(dependencies, [("org.example", "example-lib", "1.0.0")])

    def test_create_graph_hierarchy(self):
        """Test graph hierarchy creation."""
        graph = Digraph(format='png')

        # Создаем иерархию для узла com.example:my-lib:1.0
        node = create_graph_hierarchy(graph, "com.example", "my-lib", "1.0", is_root=True)

        # Проверяем наличие узлов
        graph_body = '\n'.join(graph.body)
        self.assertIn('"com.example" [label="com.example" shape=folder]', graph_body)
        self.assertIn('"com.example.my-lib" [label="my-lib" shape=box]', graph_body)
        self.assertIn('"com.example.my-lib-v1.0" [label=1.0 shape=box]', graph_body)

    @patch('dependency_visualizer.fetch_pom')
    @patch('dependency_visualizer.parse_dependencies')
    def test_build_dependency_graph(self, mock_parse_dependencies, mock_fetch_pom):
        """Test recursive dependency graph building."""
        graph = Digraph(format='png')
        visited = set()

        # Заглушка для fetch_pom
        mock_fetch_pom.return_value = """
        <project xmlns="http://maven.apache.org/POM/4.0.0">
            <dependencies>
                <dependency>
                    <groupId>org.example</groupId>
                    <artifactId>example-lib</artifactId>
                    <version>1.0.0</version>
                </dependency>
            </dependencies>
        </project>
        """
        # Заглушка для parse_dependencies
        mock_parse_dependencies.return_value = [
            ("org.example", "example-lib", "1.0.0")
        ]

        # Построение графа
        build_dependency_graph(
            graph, "com.example", "my-lib", "1.0",
            "http://localhost:8000", 0, 2, visited, is_root=True
        )

        # Проверяем наличие ключевых узлов
        graph_body = '\n'.join(graph.body)
        self.assertIn('"com.example" [label="com.example" shape=folder]', graph_body)
        self.assertIn('"org.example.example-lib" [label="example-lib" shape=box]', graph_body)


if __name__ == "__main__":
    unittest.main()
