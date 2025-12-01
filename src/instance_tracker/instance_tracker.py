import weakref
from datetime import datetime
import gc
'''
✅ Автоматический подсчет созданных и удаленных экземпляров
✅ Отслеживание времени жизни объектов
✅ Безопасное управление памятью через weakref
✅ Контекстные менеджеры для ресурсов
✅ Глобальная статистика использования
✅ Обнаружение утечек памяти
'''
class InstanceCounter(type):
    _classes_registry = weakref.WeakValueDictionary()
    _global_instances = weakref.WeakSet()
    
    def __new__(meta, name, bases, namespace):
        cls = super().__new__(meta, name, bases, namespace)
        
        cls._instances = weakref.WeakSet()
        cls._created_count = 0
        cls._deleted_count = 0
        
        meta._classes_registry[name] = cls
        
        original_init = namespace.get('__init__', None)
        
        def __init__(self, *args, **kwargs):
            self._id = id(self)
            self.created_at = datetime.now().isoformat()
            self.deleted_at = None
            self._is_active = True
            
            # Вызываем оригинальный __init__ если он существует
            if original_init:
                original_init(self, *args, **kwargs)
            # Иначе вызываем __init__ родительского класса
            elif bases:
                super(cls, self).__init__(*args, **kwargs)
            
            type(self)._created_count += 1
            type(self)._instances.add(self)
            meta._global_instances.add(self)
            
            print(f"Создан экземпляр {type(self).__name__}#{self._id}")
        
        def __enter__(self):
            if not self._is_active:
                raise RuntimeError(f"Объект {type(self).__name__}#{self._id} уже закрыт")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()
            return False
        
        def close(self):
            if self._is_active:
                self._is_active = False
                self.deleted_at = datetime.now().isoformat()
                type(self)._deleted_count += 1
                print(f"Закрыт экземпляр {type(self).__name__}#{self._id}")
        
        def get_metadata(self):
            return {
                'id': self._id,
                'class': type(self).__name__,
                'created_at': self.created_at,
                'deleted_at': self.deleted_at,
                'is_active': self._is_active
            }
        
        def process(self):
            if not self._is_active:
                raise RuntimeError(f"Объект {type(self).__name__}#{self._id} закрыт")
            return f"Обработка от {type(self).__name__}#{self._id}"
        
        def __del__(self):
            if getattr(self, '_is_active', True):
                self.close()
        
        cls.__init__ = __init__
        cls.__enter__ = __enter__
        cls.__exit__ = __exit__
        cls.close = close
        cls.get_metadata = get_metadata
        cls.process = process
        cls.__del__ = __del__
        
        @classmethod
        def get_active_instances(cls):
            return [inst for inst in cls._instances if getattr(inst, '_is_active', False)]
        
        @classmethod
        def get_stats(cls):
            active_count = len(cls.get_active_instances())
            return {
                'class_name': cls.__name__,
                'total_created': cls._created_count,
                'total_deleted': cls._deleted_count,
                'active_instances': active_count,
                'pending_deletion': len(cls._instances) - active_count
            }
        
        cls.get_active_instances = get_active_instances
        cls.get_stats = get_stats
        
        return cls
    
    @classmethod
    def get_all_classes(meta):
        return list(meta._classes_registry.values())
    
    @classmethod
    def get_global_stats(meta):
        total_instances = len(meta._global_instances)
        active_instances = 0
        classes_stats = []
        
        for cls in meta.get_all_classes():
            cls_active = len(cls.get_active_instances())
            active_instances += cls_active
            classes_stats.append(cls.get_stats())
        
        return {
            'total_classes': len(meta._classes_registry),
            'total_instances': total_instances,
            'active_instances': active_instances,
            'classes': classes_stats
        }
