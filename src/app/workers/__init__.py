import asyncio


async def main() -> None:
    print("Email worker started")

    while True:
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())