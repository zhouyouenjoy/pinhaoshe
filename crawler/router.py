"""
数据库路由，确保爬虫相关模型使用独立的数据库
"""


class CrawlerRouter:
    """
    数据库路由，将爬虫相关的模型路由到独立的数据库
    """
    route_app_labels = {'crawler'}
    
    # 需要在crawler数据库中排除的应用
    excluded_apps = {'auth', 'contenttypes', 'sessions', 'admin'}

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
        db_list = ('default', 'crawler')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        确保crawler应用的模型只在crawler数据库中创建，
        其他应用（如auth、contenttypes）的模型只在默认数据库中创建
        """
        if app_label == 'crawler':
            # crawler应用的模型只能在crawler数据库中创建
            return db == 'crawler'
        elif db == 'crawler' and app_label in self.excluded_apps:
            # crawler数据库中不能创建排除的应用的模型
            return False
        elif db == 'crawler':
            # crawler数据库中只能创建crawler应用的模型
            return app_label == 'crawler'
        # 默认数据库可以创建除crawler应用外的所有模型
        return app_label != 'crawler'