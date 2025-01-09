class Route:
    def __init__(self, method, handler, path=None, aliases=[]):
        self.method = method
        self.handler = handler
        self.path = path
        self.aliases = aliases
    
    def __str__(self):
        return f"Route({self.method}, {self.path})"
    
    def has_alias(self, alias):
        return alias in self.aliases