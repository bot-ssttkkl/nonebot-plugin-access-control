from nonebot_plugin_access_control.models.rate_limit import RateLimitTokenOrm


class RateLimitToken:
    __slots__ = ('id', 'rule_id', 'user', 'acquire_time')

    def __init__(self, orm: RateLimitTokenOrm):
        self.id = orm.id
        self.rule_id = orm.rule_id
        self.user = orm.user
        self.acquire_time = orm.acquire_time
