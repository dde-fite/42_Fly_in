from uuid import UUID


def short_id(id: UUID) -> str:
    return str(id)[:5]
