import asyncio

from backend.llm.intent import extract_intent


async def main():

    questions = [
        "Find hospitals in Kokrajhar",
        "Which hospitals in Kokrajhar have an ICU?",
        "Show ICU bed charges at MRM",
        "How much does a CBC test cost?",
        "Which pharmacy has paracetamol in stock?"
    ]

    for question in questions:

        print("\nQUESTION:", question)

        try:
            intent = await extract_intent(question)

            print(
                intent.model_dump_json(indent=2)
            )

        except Exception as error:
            print(
                f"ERROR ({type(error).__name__}): {error}"
            )


if __name__ == "__main__":
    asyncio.run(main())