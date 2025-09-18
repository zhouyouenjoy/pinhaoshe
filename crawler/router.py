"""
数据库路由，确保爬虫相关模型使用独立的数据库
"""


class CrawlerRouter:
    """
    数据库路由，将爬虫相关的模型路由到独立的数据库
    """
    route_app_labels = {'crawler'}

    def db_for_read(self, model, **hints):
        """
        尝试读取crawler应用的模型时，使用crawler数据库
        """
        if model._meta.app_label in self.route_app_labels:
            return 'crawler'
        return None

    def db_for_write(self, model, **hints):
        """
        尝试写入crawler应用的模型时，使用crawler数据库
        """
        if model._meta.app_label in self.route_app_labels:
            return 'crawler'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        如果涉及的两个对象都在crawler应用中，则允许关联
        """
        db_set = {'crawler'}
        if obj1._meta.app_label in self.route_app_labels and obj2._meta.app_label in self.route_app_labels:
            return True
        elif obj1._meta.app_label not in self.route_app_labels and obj2._meta.app_label not in self.route_app_labels:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        确保crawler应用的模型只在crawler数据库中创建
        """
        if app_label in self.route_app_labels:
            return db == 'crawler'
        elif db == 'crawler':
            return False
        return None