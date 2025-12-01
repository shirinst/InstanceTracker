from instance_tracker import InstanceCounter
from contextlib import contextmanager
import gc

# Создаем классы с нашим метаклассом
class DatabaseConnection(metaclass=InstanceCounter):
    def __init__(self, database_url):
        self.database_url = database_url
        self.connection = f"Connection to {database_url}"
    
    def execute(self, query):
        return f"Executed '{query}' on {self.database_url}"

class CacheManager(metaclass=InstanceCounter):
    def __init__(self, cache_size=100):
        self.cache_size = cache_size
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value):
        self.cache[key] = value

class UADIA(metaclass=InstanceCounter):
    def __init__(self, model_name="default"):
        self.model_name = model_name
        self.loaded_model = f"Model {model_name}"

# Демонстрация работы
def demo_weakref_advantages():
    print("=== ДЕМОНСТРАЦИЯ ПРЕИМУЩЕСТВ WEAKREF ===\n")
    
    # Создаем экземпляры с контекстными менеджерами
    print("1. Контекстные менеджеры:")
    with DatabaseConnection("postgresql://localhost/db1") as db1:
        print(f"   Создана: {db1.get_metadata()}")
        print(f"   Результат: {db1.execute('SELECT * FROM users')}")
    
    print(f"   После выхода из контекста - активные: {len(DatabaseConnection.get_active_instances())}")
    
    # Создаем экземпляры без контекстных менеджеров
    print("\n2. Создание экземпляров без контекстных менеджеров:")
    cache1 = CacheManager(50)
    cache2 = CacheManager(200)
    uadia1 = UADIA("model_v1")
    
    print(f"   Активные CacheManager: {len(CacheManager.get_active_instances())}")
    print(f"   Активные UADIA: {len(UADIA.get_active_instances())}")
    
    # Демонстрация автоматической очистки
    print("\n3. Автоматическая очистка weakref:")
    def create_temporary_objects():
        temp_db = DatabaseConnection("temp://memory")
        temp_cache = CacheManager(10)
        print(f"   Внутри функции: {len(DatabaseConnection.get_active_instances())} активных DB")
    
    create_temporary_objects()
    gc.collect()
    print(f"   После функции: {len(DatabaseConnection.get_active_instances())} активных DB")
    
    # Статистика
    print("\n4. Детальная статистика:")
    global_stats = InstanceCounter.get_global_stats()
    print(f"   Всего классов: {global_stats['total_classes']}")
    print(f"   Всего экземпляров в памяти: {global_stats['total_instances']}")
    print(f"   Активных экземпляров: {global_stats['active_instances']}")
    
    for class_stats in global_stats['classes']:
        print(f"   {class_stats['class_name']}: "
              f"создано={class_stats['total_created']}, "
              f"удалено={class_stats['total_deleted']}, "
              f"активных={class_stats['active_instances']}")
    
    # Явное управление памятью
    print("\n5. Явное управление памятью:")
    cache1.close()
    print(f"   После закрытия cache1: {len(CacheManager.get_active_instances())} активных")
    
    # Демонстрация WeakValueDictionary для кэширования
    print("\n6. WeakValueDictionary для кэширования:")
    
    class ResourceManager:
        def __init__(self):
            self._cache = weakref.WeakValueDictionary()
        
        def get_resource(self, key):
            if key not in self._cache:
                print(f"      Создаем ресурс для ключа '{key}'")
                resource = UADIA(f"resource_{key}")
                self._cache[key] = resource
            return self._cache[key]
    
    manager = ResourceManager()
    resource_a = manager.get_resource('A')
    resource_b = manager.get_resource('B')
    
    print(f"   В кэше: {len(manager._cache)} ресурсов")
    
    del resource_a
    gc.collect()
    
    print(f"   После удаления resource_a: {len(manager._cache)} ресурсов")
    
    # Очищаем оставшиеся объекты
    print("\n7. Финальная очистка:")
    for obj in [cache2, uadia1]:
        obj.close()
    
    final_stats = InstanceCounter.get_global_stats()
    print(f"   Финально - активных экземпляров: {final_stats['active_instances']}")

def demo_observer_pattern():
    print("\n=== PATTERN: OBSERVER С WEAKREF ===")
    
    class EventManager:
        def __init__(self):
            self._subscribers = weakref.WeakSet()
        
        def subscribe(self, subscriber):
            self._subscribers.add(subscriber)
            print(f"   Подписчик добавлен. Всего: {len(self._subscribers)}")
        
        def notify(self, event):
            print(f"   Отправка события: {event}")
            for subscriber in self._subscribers:
                subscriber.handle_event(event)
    
    class Subscriber:
        def __init__(self, name):
            self.name = name
        
        def handle_event(self, event):
            print(f"      {self.name} получил: {event}")
    
    event_manager = EventManager()
    sub1 = Subscriber("Subscriber-1")
    sub2 = Subscriber("Subscriber-2")
    
    event_manager.subscribe(sub1)
    event_manager.subscribe(sub2)
    
    event_manager.notify("Первое событие")
    
    print("   Удаляем Subscriber-1...")
    del sub1
    gc.collect()
    
    event_manager.notify("Второе событие")

if __name__ == "__main__":
    demo_weakref_advantages()
    demo_observer_pattern()
