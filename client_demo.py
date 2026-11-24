import asyncio
from mcp.client import Client
from server import mcp


async def main():
    print("=== Connecting to JobApplicationTracker MCP Server ===\n")
    async with Client(mcp) as client:
        # 1. List available MCP Tools
        tools = await client.list_tools()
        print("Available MCP Tools:")
        for t in tools.tools:
            print(f"  - {t.name}: {t.description}")

        # 2. Read MCP Resource
        print("\n=== Reading Resource: jobs://summary ===")
        summary = await client.read_resource("jobs://summary")
        print(next(iter(summary.contents)).text)

        # 3. Call Tool: get_pending_followups
        print("\n=== Calling Tool: get_pending_followups(days_threshold=7) ===")
        followups = await client.call_tool("get_pending_followups", {"days_threshold": 7})
        print(next(iter(followups.content)).text)

        # 4. Call Tool: add_application
        print("\n=== Calling Tool: add_application ===")
        added = await client.call_tool(
            "add_application",
            {
                "company": "OpenAI",
                "role": "Research Engineer Intern",
                "status": "Applied",
                "notes": "Submitted portfolio via GitHub",
            },
        )
        print(next(iter(added.content)).text)

        # 5. Call Tool: log_followup
        print("\n=== Calling Tool: log_followup ===")
        updated = await client.call_tool(
            "log_followup",
            {
                "company": "Mistral",
                "new_status": "Interviewing",
                "note_update": "Sent follow-up email; scheduled first interview",
            },
        )
        print(next(iter(updated.content)).text)

        # 6. Verify updated pipeline summary
        print("\n=== Updated Resource: jobs://summary ===")
        summary_after = await client.read_resource("jobs://summary")
        print(next(iter(summary_after.contents)).text)


if __name__ == "__main__":
    asyncio.run(main())
