# InstanceTracker - Модуль для отслеживания жизненного цикла объектов

## Оглавление
1. [Назначение](#назначение)
2. [Установка](#установка)
3. [Быстрый старт](#быстрый-старт)
4. [Основные возможности](#основные-возможности)
5. [API Reference](#api-reference)
6. [Примеры использования](#примеры-использования)
7. [Лучшие практики](#лучшие-практики)

## Назначение

`InstanceTracker` - это мощный Python модуль, который предоставляет метакласс для автоматического отслеживания жизненного цикла объектов, управления памятью через weak references и обеспечения безопасной работы с ресурсами через контекстные менеджеры.

**Ключевые преимущества:**
- ✅ Автоматический подсчет созданных и удаленных экземпляров
- ✅ Отслеживание времени жизни объектов
- ✅ Безопасное управление памятью через weakref
- ✅ Контекстные менеджеры для ресурсов
- ✅ Глобальная статистика использования
- ✅ Обнаружение утечек памяти

## Установка

### Установка из GitHub

```bash
# Установка напрямую из репозитория
pip install git+https://github.com/shirinst/InstanceTracker.git
```
```
# Или для разработки
git clone https://github.com/shirinst/InstanceTracker.git
cd instance-tracker
pip install -e .
```

### Требования

- Python 3.7+
- Стандартная библиотека (weakref, datetime, contextlib)

## Быстрый старт

### Базовая настройка

```python
from instance_tracker import InstanceCounter

class DatabaseConnection(metaclass=InstanceCounter):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self._connect()
    
    def _connect(self):
        print(f"Подключаемся к {self.connection_string}")
    
    def execute(self, query):
        return f"Выполнено: {query}"

# Использование
with DatabaseConnection("postgresql://localhost/db") as db:
    result = db.execute("SELECT * FROM users")
    print(result)
```

## Основные возможности

### 1. Автоматическое отслеживание экземпляров

```python
class Service(metaclass=InstanceCounter):
    def __init__(self, name):
        self.name = name

# Создаем экземпляры
service1 = Service("Auth")
service2 = Service("Payment")

# Получаем статистику
stats = Service.get_stats()
print(f"Создано: {stats['total_created']}")
print(f"Активных: {stats['active_instances']}")
```

### 2. Безопасные контекстные менеджеры

```python
class FileProcessor(metaclass=InstanceCounter):
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'r')
    
    def process(self):
        return self.file.read()
    
    def close(self):
        if hasattr(self, 'file') and self.file:
            self.file.close()

# Автоматическое закрытие при выходе из контекста
with FileProcessor("data.txt") as processor:
    data = processor.process()
# Файл автоматически закрывается здесь
```

### 3. Глобальный мониторинг

```python
# Получаем статистику по всем классам
global_stats = InstanceCounter.get_global_stats()
print(f"Всего классов: {global_stats['total_classes']}")
print(f"Всего экземпляров: {global_stats['total_instances']}")

for class_stats in global_stats['classes']:
    print(f"{class_stats['class_name']}: {class_stats['active_instances']} активных")
```

## API Reference

### Метакласс InstanceCounter

#### Методы класса (добавляются в ваш класс)

- `get_active_instances()` - возвращает список активных экземпляров
- `get_stats()` - возвращает статистику по классу
- `close()` - явное закрытие экземпляра (добавляется в экземпляры)

#### Методы метакласса

- `InstanceCounter.get_all_classes()` - все зарегистрированные классы
- `InstanceCounter.get_global_stats()` - глобальная статистика
- `InstanceCounter.find_orphaned_instances()` - поиск "осиротевших" объектов

### Атрибуты экземпляра (автоматически добавляются)

- `_id` - уникальный идентификатор
- `created_at` - время создания (ISO формат)
- `deleted_at` - время удаления (ISO формат)
- `_is_active` - статус активности
- `get_metadata()` - метод для получения метаданных

## Примеры использования

### Пример 1: Управление подключениями к БД

```python
class DatabasePool(metaclass=InstanceCounter):
    _pool = []
    
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.active_connections = 0
    
    def get_connection(self):
        if self.active_connections >= self.max_connections:
            raise RuntimeError("Достигнут лимит подключений")
        
        self.active_connections += 1
        connection = f"Connection-{self.active_connections}"
        self._pool.append(connection)
        return connection
    
    def release_connection(self, connection):
        if connection in self._pool:
            self._pool.remove(connection)
            self.active_connections -= 1
    
    def close(self):
        # Освобождаем все подключения
        self._pool.clear()
        self.active_connections = 0
        super().close()

# Использование
with DatabasePool(5) as pool:
    conn1 = pool.get_connection()
    conn2 = pool.get_connection()
    print(f"Активных подключений: {pool.active_connections}")
    
print(f"После закрытия: {DatabasePool.get_stats()['active_instances']}")
```

### Пример 2: Кэширование с автоматическим удалением

```python
import weakref

class SmartCache(metaclass=InstanceCounter):
    def __init__(self, name):
        self.name = name
        self._cache = weakref.WeakValueDictionary()
        self.hits = 0
        self.misses = 0
    
    def get(self, key, creator=None):
        if key in self._cache:
            self.hits += 1
            return self._cache[key]
        
        self.misses += 1
        if creator:
            value = creator()
            self._cache[key] = value
            return value
        return None
    
    def get_stats(self):
        base_stats = super().get_metadata()
        base_stats.update({
            'cache_size': len(self._cache),
            'cache_hits': self.hits,
            'cache_misses': self.misses,
            'hit_ratio': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        })
        return base_stats

# Использование
cache = SmartCache("user_cache")

def create_user(user_id):
    return f"User-{user_id}"

user1 = cache.get(1, lambda: create_user(1))
user2 = cache.get(2, lambda: create_user(2))

print(cache.get_stats())
```

### Пример 3: Мониторинг микросервисов

```python
class Microservice(metaclass=InstanceCounter):
    def __init__(self, name, version="1.0"):
        self.name = name
        self.version = version
        self.requests_processed = 0
        self.start_time = datetime.now()
    
    def process_request(self, request):
        self.requests_processed += 1
        return f"Обработан запрос #{self.requests_processed}"
    
    def get_health(self):
        uptime = datetime.now() - self.start_time
        return {
            'name': self.name,
            'version': self.version,
            'uptime_seconds': uptime.total_seconds(),
            'requests_processed': self.requests_processed,
            'metadata': self.get_metadata()
        }

# Создаем сервисы
auth_service = Microservice("auth-service", "2.1.0")
payment_service = Microservice("payment-service", "1.5.0")
user_service = Microservice("user-service", "3.0.0")

# Мониторинг в реальном времени
def print_services_health():
    print("\n=== СТАТУС МИКРОСЕРВИСОВ ===")
    for cls in InstanceCounter.get_all_classes():
        if cls.__name__ == "Microservice":
            for instance in cls.get_active_instances():
                health = instance.get_health()
                print(f"{health['name']}: {health['requests_processed']} запросов")

# Использование
auth_service.process_request("login")
payment_service.process_request("payment")
print_services_health()
```

### Пример 4: Паттерн Наблюдатель с weakref

```python
class EventSystem(metaclass=InstanceCounter):
    def __init__(self):
        self._subscribers = weakref.WeakSet()
    
    def subscribe(self, subscriber):
        self._subscribers.add(subscriber)
        print(f"Добавлен подписчик. Всего: {len(self._subscribers)}")
    
    def unsubscribe(self, subscriber):
        self._subscribers.discard(subscriber)
    
    def notify(self, event):
        print(f"Отправка события: {event}")
        for subscriber in list(self._subscribers):  # Копируем для безопасности
            if hasattr(subscriber, 'on_event'):
                subscriber.on_event(event)

class Subscriber(metaclass=InstanceCounter):
    def __init__(self, name):
        self.name = name
    
    def on_event(self, event):
        print(f"{self.name} получил событие: {event}")

# Использование
event_system = EventSystem()
subscriber1 = Subscriber("Подписчик 1")
subscriber2 = Subscriber("Подписчик 2")

event_system.subscribe(subscriber1)
event_system.subscribe(subscriber2)

event_system.notify("Система запущена")

# Удаляем одного подписчика - weakref автоматически уберет его
del subscriber1
import gc
gc.collect()

event_system.notify("Обновление конфигурации")
```

### Пример 5: Профилирование использования памяти

```python
class MemoryProfiler:
    @staticmethod
    def analyze_memory_usage():
        stats = InstanceCounter.get_global_stats()
        
        print("\n=== АНАЛИЗ ИСПОЛЬЗОВАНИЯ ПАМЯТИ ===")
        print(f"Всего классов: {stats['total_classes']}")
        print(f"Всего экземпляров: {stats['total_instances']}")
        print(f"Активных экземпляров: {stats['active_instances']}")
        
        # Находим классы с наибольшим количеством экземпляров
        classes_by_instances = sorted(
            stats['classes'], 
            key=lambda x: x['active_instances'], 
            reverse=True
        )
        
        print("\nКлассы по количеству экземпляров:")
        for class_info in classes_by_instances[:5]:  # Топ-5
            print(f"  {class_info['class_name']}: {class_info['active_instances']} активных")

# Использование
MemoryProfiler.analyze_memory_usage()
```

## Лучшие практики

### 1. Всегда используйте контекстные менеджеры для ресурсов

```python
# ✅ ПРАВИЛЬНО
with DatabaseConnection("db_url") as db:
    db.execute(query)

# ❌ НЕПРАВИЛЬНО
db = DatabaseConnection("db_url")
try:
    db.execute(query)
finally:
    db.close()
```

### 2. Регулярно проверяйте статистику в продакшене

```python
def health_check():
    stats = InstanceCounter.get_global_stats()
    
    # Предупреждение при большом количестве активных экземпляров
    if stats['active_instances'] > 1000:
        logger.warning("Большое количество активных экземпляров")
    
    # Проверка на утечки памяти
    for class_stats in stats['classes']:
        if class_stats['active_instances'] > class_stats['total_deleted']:
            logger.warning(f"Возможная утечка в {class_stats['class_name']}")
```

### 3. Используйте weakref для кэшей и подписчиков

```python
class SafeCache:
    def __init__(self):
        self._cache = weakref.WeakValueDictionary()  # ✅ Автоматическая очистка
    
class EventManager:
    def __init__(self):
        self._listeners = weakref.WeakSet()  # ✅ Нет циклических ссылок
```

### 4. Наследуйте правильно

```python
class BaseService(metaclass=InstanceCounter):
    def __init__(self, name):
        self.name = name
        self.initialized_at = datetime.now()

class DerivedService(BaseService):
    def __init__(self, name, version):
        super().__init__(name)  # ✅ Важно вызывать super()
        self.version = version
```

## Заключение

`InstanceTracker` предоставляет мощный инструмент для управления жизненным циклом объектов в Python приложениях. Он особенно полезен для:

- **Микросервисных архитектур** - мониторинг экземпляров сервисов
- **Управления ресурсами** - автоматическое освобождение подключений
- **Отладки памяти** - обнаружение утечек памяти
- **Профилирования** - анализ использования объектов

Модуль готов к использованию в production-средах и может быть расширен для конкретных нужд вашего проекта.

---
*Для дополнительной информации и примеров посетите [GitHub репозиторий](https://github.com/shirinst/InstanceTracker)*
