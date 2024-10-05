def _gen():
    entity_id = 0
    while True:
        entity_id += 1
        yield entity_id


id_generator = _gen()


def get_id() -> int:
    return next(id_generator)
