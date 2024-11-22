
# Dependency Visualizer

## **Описание проекта**
**Dependency Visualizer** — это инструмент командной строки для анализа и визуализации зависимостей Maven-пакетов. Программа строит граф зависимостей, включая транзитивные, и отображает результат с использованием Graphviz.

---

## **Функциональность**
1. **Анализ зависимостей:**
   - Извлечение прямых и транзитивных зависимостей заданного Maven-пакета.

2. **Создание графа:**
   - Построение графа зависимостей, где узлы представляют пакеты, а ребра — связи между ними.

3. **Визуализация графа:**
   - Отображение графа на экране.
   - Сохранение визуализации в формате PNG.

4. **Тестирование:**
   - Покрытие всех ключевых функций тестами с использованием `unittest`.

---

## **Параметры командной строки**
Инструмент поддерживает следующие аргументы:
- `--graphviz_path` (обязательный): путь к Graphviz для генерации графов.
- `--package_name` (обязательный): имя Maven-пакета для анализа (в формате `groupId:artifactId:version`).
- `--max_depth` (необязательный): максимальная глубина анализа зависимостей (по умолчанию — полная).
- `--repository_url` (обязательный): URL Maven-репозитория.

---

## **Установка**
Перед использованием убедитесь, что у вас установлены:
- Python 3.x
- Graphviz
- Maven

Для установки зависимостей Python выполните:
```bash
pip install -r requirements.txt
```

---

## **Пример использования**
### Запуск программы
```bash
python dependency_visualizer.py \
    --graphviz_path "/usr/bin/graphviz" \
    --package_name "org.example:my-package:1.0.0" \
    --max_depth 3 \
    --repository_url "https://repo.maven.apache.org/maven2/"
```

После выполнения:
- Визуализация графа будет показана на экране.
- PNG-файл графа будет сохранён в текущей рабочей директории.

---

## **Тесты**
Тесты разработаны с использованием `unittest`. Они покрывают все основные функции программы, включая:
1. `analyze_dependencies()`:
   - Проверяет корректность извлечения зависимостей Maven.
2. `build_graph()`:
   - Проверяет структуру графа зависимостей.
3. `visualize_graph()`:
   - Убеждается, что графический файл успешно создаётся.

### Запуск тестов
```bash
python -m unittest discover tests
```

---

## **Пример структуры графа**
Граф представляет собой:
- Узлы: Maven-пакеты (`groupId:artifactId`).
- Ребра: связи между пакетами.

Пример визуализации:
![Пример графа](https://example.com/sample-graph.png)

---

## **Ограничения**
1. Программа работает только с Maven-репозиториями.
2. Использование сторонних библиотек для анализа зависимостей не допускается.
3. Для корректной работы необходимо указать путь к установленному Graphviz.

---

## **Контакты**
Если у вас возникли вопросы или предложения, свяжитесь с автором через раздел **Issues** на GitHub.