class UndoStack:
    def __init__(self):
        self.stack = []

    def push(self, callable_fn, *args, **kwargs):
        self.stack.append((callable_fn, args, kwargs))

    def undo(self):
        if not self.stack:
            return None
        fn, args, kwargs = self.stack.pop()
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return e
