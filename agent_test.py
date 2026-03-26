import asyncio
from agent import AutonomousResearchAgent

async def test():
    agent = AutonomousResearchAgent("Namita Thapar")
    report = await agent.run()
    print("\n--- FINAL REPORT ---\n")
    print(report)

if __name__ == "__main__":
    asyncio.run(test())
