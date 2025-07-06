from llms.llm import LanguageModelName, build_language_model
import asyncio


async def main():
    grok_model = build_language_model(LanguageModelName.GROK_3_MINI)
    prompt = "What is the capital of France?"
    response = await grok_model.call(prompt, temperature=0.0, seed=42)
    print(f"Prompt: {prompt}")
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())


