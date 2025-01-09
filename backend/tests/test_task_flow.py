import asyncio
import httpx
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8002/api/v1"

async def test_full_flow():
    """Test the complete flow of creating an agent, task, and executing it."""
    async with httpx.AsyncClient() as client:
        # 1. Create an agent
        agent_data = {
            "role": "test_assistant",
            "goal": "Execute test tasks successfully",
            "backstory": "I am a test agent",
            "allow_delegation": False,
            "verbose": True,
            "tools": [],
            "memory": {},
            "llm_config": {},
            "max_iterations": 5
        }
        
        response = await client.post(
            f"{BASE_URL}/agents/",
            json=agent_data
        )
        assert response.status_code == 201, f"Failed to create agent: {response.text}"
        agent = response.json()
        print(f"✅ Agent created: {agent['id']}")

        # 2. Create a task
        task_data = {
            "description": "Test task execution",
            "agent_role": "test_assistant",
            "expected_output": "Success message",
            "context": {"test": True},
            "async_execution": True
        }
        
        response = await client.post(
            f"{BASE_URL}/tasks/",
            json=task_data
        )
        assert response.status_code == 200, f"Failed to create task: {response.text}"
        task = response.json()
        print(f"✅ Task created")

        # 3. Execute the task
        response = await client.post(
            f"{BASE_URL}/tasks/{task['id']}/execute"
        )
        assert response.status_code == 200, f"Failed to execute task: {response.text}"
        execution = response.json()
        print(f"✅ Task execution started: {execution['task_id']}")

        # 4. Poll for task completion
        max_retries = 10
        retry_count = 0
        while retry_count < max_retries:
            response = await client.get(
                f"{BASE_URL}/tasks/{execution['task_id']}"
            )
            assert response.status_code == 200, f"Failed to get task status: {response.text}"
            task_status = response.json()
            
            if task_status['status'] in ['completed', 'error']:
                print(f"✅ Task finished with status: {task_status['status']}")
                print(f"Result: {json.dumps(task_status.get('result', {}), indent=2)}")
                break
                
            print(f"⏳ Task still running... (attempt {retry_count + 1}/{max_retries})")
            retry_count += 1
            await asyncio.sleep(2)

        # 5. Get agent analytics
        response = await client.get(
            f"{BASE_URL}/tasks/agent/{agent['id']}/analytics"
        )
        assert response.status_code == 200, f"Failed to get analytics: {response.text}"
        analytics = response.json()
        print(f"✅ Agent analytics retrieved")
        print(f"Analytics: {json.dumps(analytics, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_full_flow()) 