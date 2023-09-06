import structlog


class StructlogMixin:
    logger_name = None

    def __init__(self, *args, **kwargs):
        if not getattr(self, "log", None):
            name = (
                self.logger_name
                or f"{self.__class__.__module__}.{self.__class__.__name__}"
            )
            self.log = structlog.get_logger(name).new()
        super().__init__(*args, **kwargs)
