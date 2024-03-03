
# Add items from Async Generator into a list of queues to be consumed by multiple consumers
async def producer(ag, queues):
    async for item in ag:
        # print(f"producer got item {item}")
        for q in queues:
            await q.put(item)
    for q in queues:
        await q.put(None)  # Signal the consumers that the stream has ended

