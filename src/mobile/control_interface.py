"""
Mobile Control Interface
Provides goal setting, approval workflows, and mobile-optimized agent control.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

# Import agent components
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.specialist_agents import AgentTask
from qa.qa_engine import QAEngine
from qa.qa_event_bus import QAEventBus


class ApprovalStatus(Enum):
    """Approval status for mobile control workflows."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class GoalPriority(Enum):
    """Priority levels for goals."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MobileGoal:
    """Mobile goal with approval workflow."""

    goal_id: str
    title: str
    description: str
    priority: GoalPriority
    created_by: str
    created_at: datetime
    due_date: Optional[datetime] = None
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    agent_tasks: List[str] = None  # List of agent task IDs

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "approval_status": self.approval_status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "agent_tasks": self.agent_tasks or [],
        }


@dataclass
class MobileApproval:
    """Mobile approval request."""

    approval_id: str
    goal_id: str
    requested_by: str
    requested_at: datetime
    approvers: List[str]
    status: ApprovalStatus = ApprovalStatus.PENDING
    responses: Dict[str, str] = None  # approver -> response
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "approval_id": self.approval_id,
            "goal_id": self.goal_id,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at.isoformat(),
            "approvers": self.approvers,
            "status": self.status.value,
            "responses": self.responses or {},
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class MobileControlInterface:
    """Mobile control interface for goal setting and approvals."""

    def __init__(self, qa_engine: QAEngine, event_bus: QAEventBus):
        self.qa_engine = qa_engine
        self.event_bus = event_bus
        self.goals: Dict[str, MobileGoal] = {}
        self.approvals: Dict[str, MobileApproval] = {}
        self.notification_callbacks: List[Callable] = []

        # Subscribe to agent events
        self.event_bus.subscribe("qa_success", self._handle_agent_success)
        self.event_bus.subscribe("qa_failure", self._handle_agent_failure)

    def create_goal(
        self,
        title: str,
        description: str,
        priority: GoalPriority,
        created_by: str,
        due_date: Optional[datetime] = None,
        requires_approval: bool = True,
    ) -> MobileGoal:
        """Create a new mobile goal."""

        goal_id = f"goal_{int(time.time())}"
        goal = MobileGoal(
            goal_id=goal_id,
            title=title,
            description=description,
            priority=priority,
            created_by=created_by,
            created_at=datetime.now(),
            due_date=due_date,
            approval_status=(
                ApprovalStatus.PENDING if requires_approval else ApprovalStatus.APPROVED
            ),
        )

        self.goals[goal_id] = goal

        # Create approval request if needed
        if requires_approval:
            self._create_approval_request(goal)

        # Notify subscribers
        self._notify_goal_created(goal)

        return goal

    def approve_goal(self, goal_id: str, approver: str) -> bool:
        """Approve a goal."""

        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]
        goal.approval_status = ApprovalStatus.APPROVED
        goal.approved_by = approver
        goal.approved_at = datetime.now()

        # Update approval status
        for approval in self.approvals.values():
            if approval.goal_id == goal_id:
                approval.status = ApprovalStatus.APPROVED
                break

        # Notify subscribers
        self._notify_goal_approved(goal)

        return True

    def reject_goal(self, goal_id: str, approver: str, reason: str) -> bool:
        """Reject a goal."""

        if goal_id not in self.goals:
            return False

        goal = self.goals[goal_id]
        goal.approval_status = ApprovalStatus.REJECTED
        goal.rejection_reason = reason

        # Update approval status
        for approval in self.approvals.values():
            if approval.goal_id == goal_id:
                approval.status = ApprovalStatus.REJECTED
                break

        # Notify subscribers
        self._notify_goal_rejected(goal)

        return True

    def get_goals_for_user(self, user: str) -> List[MobileGoal]:
        """Get goals for a specific user."""

        user_goals = []
        for goal in self.goals.values():
            if goal.created_by == user or goal.approved_by == user:
                user_goals.append(goal)

        return sorted(user_goals, key=lambda g: g.created_at, reverse=True)

    def get_pending_approvals(self, approver: str) -> List[MobileApproval]:
        """Get pending approvals for an approver."""

        pending = []
        for approval in self.approvals.values():
            if approval.status == ApprovalStatus.PENDING and approver in approval.approvers:
                pending.append(approval)

        return sorted(pending, key=lambda a: a.requested_at, reverse=True)

    def get_goal_status(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a goal."""

        if goal_id not in self.goals:
            return None

        goal = self.goals[goal_id]
        status = {
            "goal": goal.to_dict(),
            "agent_tasks": [],
            "progress": 0.0,
            "last_activity": goal.created_at.isoformat(),
        }

        # Add agent task information if available
        if goal.agent_tasks:
            status["agent_tasks"] = goal.agent_tasks
            # Calculate progress based on completed tasks
            # This would integrate with actual agent task tracking

        return status

    def create_agent_task_for_goal(
        self, goal_id: str, agent_name: str, task_action: str, task_payload: Dict[str, Any]
    ) -> Optional[str]:
        """Create an agent task for a goal."""

        if goal_id not in self.goals:
            return None

        goal = self.goals[goal_id]
        if goal.approval_status != ApprovalStatus.APPROVED:
            return None

        # Create agent task
        task_id = f"task_{int(time.time())}"
        agent_task = AgentTask(action=task_action, payload=task_payload, correlation_id=task_id)

        # Store task reference in goal
        if goal.agent_tasks is None:
            goal.agent_tasks = []
        goal.agent_tasks.append(task_id)

        # Publish task to event bus
        self.event_bus.publish(
            "mobile_task_created",
            {
                "task_id": task_id,
                "goal_id": goal_id,
                "agent_name": agent_name,
                "task": (
                    agent_task.to_dict() if hasattr(agent_task, "to_dict") else asdict(agent_task)
                ),
            },
        )

        return task_id

    def subscribe_to_notifications(self, callback: Callable) -> None:
        """Subscribe to mobile control notifications."""
        self.notification_callbacks.append(callback)

    def _create_approval_request(self, goal: MobileGoal) -> None:
        """Create an approval request for a goal."""

        approval_id = f"approval_{int(time.time())}"
        approval = MobileApproval(
            approval_id=approval_id,
            goal_id=goal.goal_id,
            requested_by=goal.created_by,
            requested_at=datetime.now(),
            approvers=self._get_approvers_for_priority(goal.priority),
            expires_at=datetime.now() + timedelta(hours=24),  # 24 hour expiry
        )

        self.approvals[approval_id] = approval
        self._notify_approval_requested(approval)

    def _get_approvers_for_priority(self, priority: GoalPriority) -> List[str]:
        """Get approvers based on goal priority."""

        # This would integrate with user management system
        approvers = {
            GoalPriority.LOW: ["qa_agent"],
            GoalPriority.MEDIUM: ["qa_agent", "meta_agent"],
            GoalPriority.HIGH: ["qa_agent", "meta_agent", "architect_agent"],
            GoalPriority.CRITICAL: ["qa_agent", "meta_agent", "architect_agent", "admin"],
        }

        return approvers.get(priority, ["qa_agent"])

    def _handle_agent_success(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle agent success events."""
        self._notify_agent_event("success", data)

    def _handle_agent_failure(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle agent failure events."""
        self._notify_agent_event("failure", data)

    def _notify_goal_created(self, goal: MobileGoal) -> None:
        """Notify subscribers of goal creation."""
        for callback in self.notification_callbacks:
            try:
                callback("goal_created", goal.to_dict())
            except Exception:
                pass  # Don't let notification failures break the system

    def _notify_goal_approved(self, goal: MobileGoal) -> None:
        """Notify subscribers of goal approval."""
        for callback in self.notification_callbacks:
            try:
                callback("goal_approved", goal.to_dict())
            except Exception:
                pass

    def _notify_goal_rejected(self, goal: MobileGoal) -> None:
        """Notify subscribers of goal rejection."""
        for callback in self.notification_callbacks:
            try:
                callback("goal_rejected", goal.to_dict())
            except Exception:
                pass

    def _notify_approval_requested(self, approval: MobileApproval) -> None:
        """Notify subscribers of approval request."""
        for callback in self.notification_callbacks:
            try:
                callback("approval_requested", approval.to_dict())
            except Exception:
                pass

    def _notify_agent_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify subscribers of agent events."""
        for callback in self.notification_callbacks:
            try:
                callback(f"agent_{event_type}", data)
            except Exception:
                pass

    def export_goals(self, output_path: Path) -> None:
        """Export goals to JSON file."""
        data = {
            "goals": [goal.to_dict() for goal in self.goals.values()],
            "approvals": [approval.to_dict() for approval in self.approvals.values()],
            "exported_at": datetime.now().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)


# Export main classes
__all__ = [
    "MobileControlInterface",
    "MobileGoal",
    "MobileApproval",
    "ApprovalStatus",
    "GoalPriority",
]
