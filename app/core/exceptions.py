from uuid import UUID


class UserNotFoundError(Exception):
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id

        super().__init__(f"User with id {user_id} was not found")
