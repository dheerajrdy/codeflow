"""
Software Engineering Agent Example

This example demonstrates a software engineering agent that can:
1. Plan and execute coding tasks using memory-based task tracking
2. Remember patterns and decisions across runs
3. Use file operations, code execution, and search
4. Track progress and learn from experience

The agent follows this workflow:
- Check memory for relevant patterns
- Create a markdown-based plan in memory
- Execute steps using coding tools
- Log key decisions to memory
- Complete with summary
"""

import asyncio
import os
from pathlib import Path

from picoagents import Agent
from picoagents.llm import AzureOpenAIChatCompletionClient
from picoagents.tools import (
    MemoryTool,
    TaskStatusTool,
    ThinkTool,
    create_coding_tools,
)
from picoagents.types import AgentResponse


system_instructions  ="""
You are an expert software engineering agent. Follow this systematic workflow:

## PHASE 1: MEMORY CHECK (ALWAYS DO THIS FIRST)
1. Use memory tool with command='view', path='/memories' to see directory structure
2. Check for relevant patterns in /memories/patterns/
3. Check previous decisions in /memories/decisions/
4. Review any working notes from past sessions

## PHASE 2: PLANNING (MEMORY-BASED)
1. Use 'think' tool to analyze the task requirements
2. Use memory tool with command='create' to create /memories/current_task.md with:
   ```markdown
   # Task: [Task Name]

   ## Plan
   - [ ] Step 1: Description
   - [ ] Step 2: Description
   - [ ] Step 3: Description

   ## Notes
   - Key decisions
   - Important considerations
   ```
3. Break complex tasks into smaller, testable steps
4. Use markdown checkboxes for task tracking

## PHASE 3: EXECUTION
1. Use memory tool with command='view', path='/memories/current_task.md' to see your plan
2. For each unchecked task:
   a. Use coding tools as needed:
      - read_file: Read existing code
      - write_file: Create/modify files (use str_replace for edits)
      - list_directory: Explore project structure
      - bash_execute: Run commands, tests
      - python_repl: Test Python code snippets
   b. Test your changes if applicable
   c. Use memory tool with command='str_replace' to update the checkbox:
      - old_str: "- [ ] Step N"
      - new_str: "- [x] Step N"
   d. Log key decisions using memory tool with command='append':
      - path: '/memories/decisions/YYYY-MM-DD.md'
      - append_text: "- [timestamp] Decision: description"

## PHASE 4: LEARNING & DOCUMENTATION
1. Use memory tool with command='search' to check if similar patterns already exist
2. If you discover a useful pattern or solution:
   - Use memory tool with command='create' or 'append' to store it in /memories/patterns/
   - Document: what the problem was, your solution, why it works
3. Update /memories/current_task.md with completion status

## PHASE 5: TASK COMPLETION (CRITICAL - ALWAYS DO THIS)
Before finishing, ALWAYS call task_status tool to formally evaluate completion:

If ALL requirements are satisfied:
  task_status(
    status="complete",
    rationale="Detailed explanation of how each requirement was met with evidence",
    requirements_met=["List each requirement satisfied"]
  )

If unable to complete (blocked, need input, hit limits):
  task_status(
    status="incomplete",
    rationale="Explain the blocker, what was tried, why stopping now",
    requirements_pending=["List what remains"]
  )

Example complete rationale:
"✓ Requirement 1 (4 functions): Created add, subtract, multiply, divide in calculator.py
 ✓ Requirement 2 (error handling): divide() raises ValueError for zero divisor
 ✓ Requirement 3 (tests): Created test_calculator.py with 12 tests, all passed
 ✓ Requirement 4 (documentation): Added comprehensive docstrings to all functions
All requirements verified and complete."

NEVER finish without calling task_status. This documents WHY you're stopping.

## MEMORY ORGANIZATION
- /memories/patterns/: Reusable solutions, code patterns, common bugs
- /memories/decisions/: Why we chose specific approaches (dated logs)
- /memories/current_task.md: Active task tracking (markdown with checkboxes)
- /memories/project_context.md: High-level project understanding

## BEST PRACTICES
- ALWAYS check memory before starting a task
- ALWAYS test code changes when possible
- ALWAYS log important decisions
- ALWAYS call task_status before finishing
- Use 'think' tool for complex reasoning
- Keep memory organized and searchable
- Write clear, concise documentation
- Use markdown checkboxes (- [ ] and - [x]) for task tracking

## ERROR HANDLING
- If a command fails, analyze the error and try alternative approaches
- Log failures and solutions to help future tasks
- Don't give up after first failure - iterate
- If blocked after retries, call task_status with incomplete and explain

Remember: Your memory persists across sessions. Build up knowledge!
"""

 # Get API credentials
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

if not api_key or not endpoint:
    print("Error: Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")  

# Set up workspace directories
workspace = Path("./scratch/agent_workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Set up memory directory
memory_path = Path("./scratch/agent_memory")
memory_path.mkdir(parents=True, exist_ok=True)

def get_agent() -> Agent :
    """Create the software engineering agent.""" 
   

    # Initialize model client
    client = AzureOpenAIChatCompletionClient(
        model="gpt-4.1-mini",
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-10-21",
    )

    


    # Initialize tools
    memory_tool = MemoryTool(base_path=memory_path)

    # Create agent with comprehensive instructions
    agent = Agent(
        name="software_engineer",
        description="Expert software engineering agent that plans, codes, and learns from experience",
        model_client=client,
        instructions=system_instructions,
        tools=[
            memory_tool,
            ThinkTool(),
            TaskStatusTool(),
            *create_coding_tools(workspace=workspace, bash_timeout=60),
        ],
        max_iterations=50,  # Allow longer execution for complex tasks
    )
    return agent

agent = get_agent()   

async def main():
    """Run software engineering agent on sample tasks."""

    print("=" * 70)
    print("SOFTWARE ENGINEERING AGENT - Example Run")
    print("=" * 70)
    print()

    # Task 1: Create a simple Python module
    print("\n" + "=" * 70)
    print("TASK 1: Create a Calculator Module")
    print("=" * 70)

    task1 = """
Create a Python module called 'calculator.py' with the following functions:
1. add(a, b) - returns sum
2. subtract(a, b) - returns difference
3. multiply(a, b) - returns product
4. divide(a, b) - returns quotient (handle division by zero)

Also create a test file 'test_calculator.py' with basic tests for each function.
Run the tests to ensure everything works.
"""

    print("\nTask:", task1.strip())
    print("\nAgent working...\n")
 
    async for event in agent.run_stream(task1):
        print(event)

    print("\n" + "-" * 70)
    print("TASK 1 COMPLETE") 
    
    # Task 2: Enhance the module (tests agent's memory)
    print("\n" + "=" * 70)
    print("TASK 2: Add Power Function and Update Tests")
    print("=" * 70)

    task2 = """
Add a 'power(base, exponent)' function to the calculator module.
Update the test file to include tests for the power function.
Run all tests to ensure everything still works.

Note: Check if there are any patterns or decisions from the previous task that might help.
"""

    print("\nTask:", task2.strip())
    print("\nAgent working...\n")
 
    context = None
    async for event in agent.run_stream(task2):
        print(event)
        if isinstance(event, AgentResponse):
            context = event.context

    print("\n" + "-" * 70)
    print("TASK 2 COMPLETE")
    

    # Task 3: Code review and documentation
    print("\n" + "=" * 70)
    print("TASK 3: Add Docstrings and README")
    print("=" * 70)

    task3 = """
Review the calculator module and:
1. Add comprehensive docstrings to all functions
2. Create a README.md file explaining how to use the module
3. Include examples in the README

Check your memory for any documentation patterns or conventions.
"""

    print("\nTask:", task3.strip())
    print("\nAgent working...\n")

    async for event in agent.run_stream(task3, context=context):
        print(event)
        if isinstance(event, AgentResponse):
            context = event.context
     

    print("\n" + "-" * 70)
    print("TASK 3 COMPLETE") 
    print("-" * 70)

    # Summary
    print("\n" + "=" * 70)
    print("ALL TASKS COMPLETE")
    print("=" * 70)
    print(f"\nWorkspace: {workspace.absolute()}")
    print(f"Agent Memory: {memory_path.absolute()}")
    print("\nGenerated files:")
    for file in workspace.rglob("*"):
        if file.is_file():
            print(f"  - {file.relative_to(workspace)}")

    print("\nMemory files:")
    for file in memory_path.rglob("*"):
        if file.is_file():
            print(f"  - {file.relative_to(memory_path)}")

    print("\nThe agent has built up memory that will persist for future runs!")
    print("Try running the script again with a different task to see memory in action.")


if __name__ == "__main__":
    asyncio.run(main())
