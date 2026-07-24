import asyncio

from app.db.session import async_session_factory
from app.schemas import UserCreateData, UserRead
from app.services import UserService


async def main() -> None:
    password = "strong-password-123"

    async with async_session_factory() as session:
        service = UserService(session)

        data = UserCreateData(
            full_name="Тестовый Пользователь",
            password=password,
        )

        user = await service.create_user(data)

        assert user.password_hash != password

        correct_password = await service.verify_user_password(
            user=user,
            password=password,
        )
        wrong_password = await service.verify_user_password(
            user=user,
            password="wrong-password",
        )

        assert correct_password is True
        assert wrong_password is False

        public_user = UserRead.model_validate(user)
        public_data = public_user.model_dump()

        assert "password" not in public_data
        assert "password_hash" not in public_data

        print("Пользователь:", public_user)
        print("Хеш:", user.password_hash)
        print("Правильный пароль:", correct_password)
        print("Неправильный пароль:", wrong_password)
        print("Проверка успешно завершена")


if __name__ == "__main__":
    asyncio.run(main())
