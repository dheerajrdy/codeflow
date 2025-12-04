#!/usr/bin/env python3
"""
Basic test of the tool approval infrastructure.
This demonstrates that the approval components are working.
"""

from picoagents import (
    AgentContext,
    ApprovalMode,
    ToolApprovalRequest,
    ToolApprovalResponse,
    tool,
)
from picoagents.messages import ToolCallRequest


def test_tool_decorator():
    """Test that tool decorator works with approval mode."""

    @tool
    def simple_tool(x: int) -> int:
        """A simple tool without approval."""
        return x * 2

    @tool(approval_mode="always_require")
    def approval_tool(x: int) -> int:
        """A tool that requires approval."""
        return x * 3

    print("✓ Tool decorators created successfully")
    print(f"  - simple_tool.approval_mode: {simple_tool.approval_mode}")
    print(f"  - approval_tool.approval_mode: {approval_tool.approval_mode}")

    assert simple_tool.approval_mode == ApprovalMode.NEVER
    assert approval_tool.approval_mode == ApprovalMode.ALWAYS
    return simple_tool, approval_tool


def test_context_approval_flow():
    """Test the context approval management flow."""

    # Create a context
    context = AgentContext()
    print("\n✓ AgentContext created")

    # Create a tool call that would need approval
    tool_call = ToolCallRequest(
        call_id="call_123",
        tool_name="delete_file",
        parameters={"path": "/tmp/test.txt"}
    )
    print("✓ ToolCallRequest created")

    # Add approval request to context
    approval_req = context.add_approval_request(tool_call, "delete_file")
    print(f"✓ Approval request added to context")
    print(f"  - Request ID: {approval_req.request_id}")
    print(f"  - Tool: {approval_req.tool_name}")
    print(f"  - Waiting for approval: {context.waiting_for_approval}")

    assert context.waiting_for_approval == True
    assert len(context.pending_approval_requests) == 1

    # Simulate user approval
    print("\n→ Simulating user approval...")
    approval_resp = approval_req.create_response(approved=True)
    context.add_approval_response(approval_resp)
    print(f"✓ Approval response added")
    print(f"  - Approved: {approval_resp.approved}")
    print(f"  - Waiting for approval: {context.waiting_for_approval}")

    assert context.waiting_for_approval == False

    # Get approved tool calls
    approved_calls = context.get_approved_tool_calls()
    print(f"✓ Retrieved {len(approved_calls)} approved tool calls")

    assert len(approved_calls) == 1
    assert approved_calls[0] == tool_call

    return context


def test_rejection_flow():
    """Test handling of rejected approvals."""

    print("\n" + "="*50)
    print("Testing Rejection Flow")
    print("="*50)

    context = AgentContext()

    # Create tool call
    tool_call = ToolCallRequest(
        call_id="call_456",
        tool_name="dangerous_operation",
        parameters={"action": "delete_everything"}
    )

    # Add approval request
    approval_req = context.add_approval_request(tool_call, "dangerous_operation")
    print(f"✓ Approval request added for: {approval_req.tool_name}")

    # Reject it
    print("\n→ Simulating user rejection...")
    approval_resp = approval_req.create_response(approved=False)
    context.add_approval_response(approval_resp)
    print(f"✓ Rejection response added")

    # Check results
    approved = context.get_approved_tool_calls()
    rejected = context.get_rejected_tool_calls()

    print(f"  - Approved calls: {len(approved)}")
    print(f"  - Rejected calls: {len(rejected)}")

    assert len(approved) == 0
    assert len(rejected) == 1
    assert rejected[0][0] == "call_456"

    return context


def test_multiple_approvals():
    """Test handling multiple approval requests."""

    print("\n" + "="*50)
    print("Testing Multiple Approvals")
    print("="*50)

    context = AgentContext()

    # Create multiple tool calls
    calls = [
        ToolCallRequest(call_id="call_1", tool_name="tool_1", parameters={"x": 1}),
        ToolCallRequest(call_id="call_2", tool_name="tool_2", parameters={"x": 2}),
        ToolCallRequest(call_id="call_3", tool_name="tool_3", parameters={"x": 3}),
    ]

    # Add approval requests
    requests = []
    for call in calls:
        req = context.add_approval_request(call, call.tool_name)
        requests.append(req)

    print(f"✓ Added {len(requests)} approval requests")
    print(f"  - Pending approvals: {len(context.pending_approval_requests)}")
    assert context.waiting_for_approval == True
    assert len(context.pending_approval_requests) == 3

    # Approve first two, reject the third
    print("\n→ Processing approvals...")
    for i, req in enumerate(requests):
        approved = i < 2  # Approve first 2, reject third
        resp = req.create_response(approved=approved)
        context.add_approval_response(resp)
        print(f"  - {req.tool_name}: {'✓ Approved' if approved else '✗ Rejected'}")

    # Check results
    print("\n→ Retrieving results...")
    approved = context.get_approved_tool_calls()
    rejected = context.get_rejected_tool_calls()

    print(f"✓ Results:")
    print(f"  - Approved: {len(approved)} calls")
    print(f"  - Rejected: {len(rejected)} calls")

    assert len(approved) == 2
    assert len(rejected) == 1
    assert not context.waiting_for_approval

    return context


def main():
    """Run all tests."""

    print("="*60)
    print(" Testing PicoAgents Tool Approval Infrastructure")
    print("="*60)

    try:
        # Test 1: Tool decorators
        print("\n" + "="*50)
        print("Test 1: Tool Decorators with Approval Mode")
        print("="*50)
        simple_tool, approval_tool = test_tool_decorator()

        # Test 2: Basic approval flow
        print("\n" + "="*50)
        print("Test 2: Context Approval Flow")
        print("="*50)
        context = test_context_approval_flow()

        # Test 3: Rejection flow
        context = test_rejection_flow()

        # Test 4: Multiple approvals
        context = test_multiple_approvals()

        print("\n" + "="*60)
        print(" ✅ All Tests Passed!")
        print("="*60)
        print("\nThe tool approval infrastructure is working correctly.")
        print("The following components are functional:")
        print("  • Tool decorator with approval_mode parameter")
        print("  • AgentContext with approval state management")
        print("  • ToolApprovalRequest and ToolApprovalResponse")
        print("  • Approval/rejection flow handling")
        print("  • Multiple approval request management")

        print("\nNote: Full agent integration requires updating Agent.run()")
        print("      to accept context parameter and handle approval flow.")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())