"""
Mobile App Interface
Complete mobile functionality for goal setting, approvals, and agent control.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from qa.qa_engine import QAEngine, QARules

# Import mobile control interface
from .control_interface import (
    ApprovalStatus,
    GoalPriority,
    MobileApproval,
    MobileControlInterface,
    MobileGoal,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MobileAppState(Enum):
    """Mobile app state."""

    IDLE = "idle"
    LOADING = "loading"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class MobileNotification:
    """Mobile notification."""

    id: str
    title: str
    message: str
    type: str  # info, warning, error, success
    timestamp: datetime
    read: bool = False
    action_required: bool = False
    action_url: Optional[str] = None


@dataclass
class MobileDashboard:
    """Mobile dashboard data."""

    total_goals: int
    pending_approvals: int
    completed_tasks: int
    active_agents: int
    recent_activity: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]


class MobileApp:
    """Complete mobile app interface."""

    def __init__(self, control_interface: MobileControlInterface):
        self.control_interface = control_interface
        self.state = MobileAppState.IDLE
        self.notifications: List[MobileNotification] = []
        self.dashboard_data: Optional[MobileDashboard] = None
        self.user_preferences: Dict[str, Any] = {}

        # Subscribe to control interface events
        self.control_interface.subscribe_to_notifications(self._handle_control_event)

    async def initialize(self) -> None:
        """Initialize the mobile app."""

        logger.info("Initializing mobile app...")
        self.state = MobileAppState.LOADING

        try:
            # Load user preferences
            await self._load_user_preferences()

            # Initialize dashboard
            await self._initialize_dashboard()

            # Setup notifications
            await self._setup_notifications()

            self.state = MobileAppState.IDLE
            logger.info("Mobile app initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing mobile app: {e}")
            self.state = MobileAppState.ERROR

    async def _load_user_preferences(self) -> None:
        """Load user preferences."""

        preferences_file = Path("config/mobile_preferences.json")
        if preferences_file.exists():
            with open(preferences_file, "r") as handle:
                self.user_preferences = json.load(handle)
        else:
            # Default preferences
            self.user_preferences = {
                "notifications_enabled": True,
                "auto_approve_low_priority": False,
                "theme": "light",
                "language": "en",
                "refresh_interval": 30,
            }

    async def _initialize_dashboard(self) -> None:
        """Initialize dashboard data."""

        # Get goals for current user
        user_goals = self.control_interface.get_goals_for_user("mobile_user")

        # Get pending approvals
        pending_approvals = self.control_interface.get_pending_approvals("mobile_user")

        # Create dashboard
        self.dashboard_data = MobileDashboard(
            total_goals=len(user_goals),
            pending_approvals=len(pending_approvals),
            completed_tasks=len(
                [g for g in user_goals if g.approval_status == ApprovalStatus.APPROVED]
            ),
            active_agents=7,  # All 7 agents are active
            recent_activity=await self._get_recent_activity(),
            performance_metrics=await self._get_performance_metrics(),
        )

    async def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent activity data."""

        # This would integrate with actual agent activity tracking
        return [
            {
                "type": "goal_created",
                "title": "New goal created",
                "timestamp": datetime.now().isoformat(),
                "agent": "mobile_user",
            },
            {
                "type": "agent_task",
                "title": "Frontend agent completed task",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "agent": "frontend_agent",
            },
            {
                "type": "approval",
                "title": "Goal approved",
                "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
                "agent": "qa_agent",
            },
        ]

    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""

        # This would integrate with actual performance tracking
        return {
            "response_time_avg": 1.2,
            "success_rate": 0.95,
            "active_goals": 5,
            "completed_this_week": 12,
        }

    async def _setup_notifications(self) -> None:
        """Setup notification system."""

        # Add some default notifications
        self.notifications.append(
            MobileNotification(
                id="welcome",
                title="Welcome to CodexHUB Mobile",
                message="Your mobile control interface is ready!",
                type="info",
                timestamp=datetime.now(),
            )
        )

    async def create_goal(
        self,
        title: str,
        description: str,
        priority: GoalPriority,
        due_date: Optional[datetime] = None,
    ) -> MobileGoal:
        """Create a new goal via mobile interface."""

        try:
            goal = self.control_interface.create_goal(
                title=title,
                description=description,
                priority=priority,
                created_by="mobile_user",
                due_date=due_date,
                requires_approval=True,
            )

            # Add notification
            self._add_notification(
                title="Goal Created",
                message=f"Goal '{title}' has been created and is pending approval.",
                type="success",
            )

            # Update dashboard
            await self._refresh_dashboard()

            return goal

        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            self._add_notification(
                title="Error", message=f"Failed to create goal: {e}", type="error"
            )
            raise

    async def approve_goal(self, goal_id: str) -> bool:
        """Approve a goal via mobile interface."""

        try:
            success = self.control_interface.approve_goal(goal_id, "mobile_user")

            if success:
                self._add_notification(
                    title="Goal Approved",
                    message=f"Goal {goal_id} has been approved.",
                    type="success",
                )
                await self._refresh_dashboard()
            else:
                self._add_notification(
                    title="Approval Failed",
                    message=f"Failed to approve goal {goal_id}.",
                    type="error",
                )

            return success

        except Exception as e:
            logger.error(f"Error approving goal: {e}")
            self._add_notification(
                title="Error", message=f"Failed to approve goal: {e}", type="error"
            )
            return False

    async def reject_goal(self, goal_id: str, reason: str) -> bool:
        """Reject a goal via mobile interface."""

        try:
            success = self.control_interface.reject_goal(goal_id, "mobile_user", reason)

            if success:
                self._add_notification(
                    title="Goal Rejected",
                    message=f"Goal {goal_id} has been rejected: {reason}",
                    type="warning",
                )
                await self._refresh_dashboard()
            else:
                self._add_notification(
                    title="Rejection Failed",
                    message=f"Failed to reject goal {goal_id}.",
                    type="error",
                )

            return success

        except Exception as e:
            logger.error(f"Error rejecting goal: {e}")
            self._add_notification(
                title="Error", message=f"Failed to reject goal: {e}", type="error"
            )
            return False

    async def get_dashboard(self) -> MobileDashboard:
        """Get current dashboard data."""

        if self.dashboard_data is None:
            await self._initialize_dashboard()

        return self.dashboard_data

    async def get_goals(self, status_filter: Optional[str] = None) -> List[MobileGoal]:
        """Get goals with optional status filter."""

        goals = self.control_interface.get_goals_for_user("mobile_user")

        if status_filter:
            if status_filter == "pending":
                goals = [g for g in goals if g.approval_status == ApprovalStatus.PENDING]
            elif status_filter == "approved":
                goals = [g for g in goals if g.approval_status == ApprovalStatus.APPROVED]
            elif status_filter == "rejected":
                goals = [g for g in goals if g.approval_status == ApprovalStatus.REJECTED]

        return goals

    async def get_approvals(self) -> List[MobileApproval]:
        """Get pending approvals."""

        return self.control_interface.get_pending_approvals("mobile_user")

    async def get_goal_status(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed goal status."""

        return self.control_interface.get_goal_status(goal_id)

    async def create_agent_task(
        self, goal_id: str, agent_name: str, task_action: str, task_payload: Dict[str, Any]
    ) -> Optional[str]:
        """Create an agent task for a goal."""

        try:
            task_id = self.control_interface.create_agent_task_for_goal(
                goal_id=goal_id,
                agent_name=agent_name,
                task_action=task_action,
                task_payload=task_payload,
            )

            if task_id:
                self._add_notification(
                    title="Task Created",
                    message=f"Agent task created for {agent_name}",
                    type="info",
                )

            return task_id

        except Exception as e:
            logger.error(f"Error creating agent task: {e}")
            self._add_notification(
                title="Error", message=f"Failed to create agent task: {e}", type="error"
            )
            return None

    def get_notifications(self, unread_only: bool = False) -> List[MobileNotification]:
        """Get notifications."""

        notifications = self.notifications

        if unread_only:
            notifications = [n for n in notifications if not n.read]

        return sorted(notifications, key=lambda n: n.timestamp, reverse=True)

    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""

        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                return True

        return False

    def _add_notification(
        self,
        title: str,
        message: str,
        type: str,
        action_required: bool = False,
        action_url: Optional[str] = None,
    ) -> None:
        """Add a new notification."""

        notification = MobileNotification(
            id=f"notification_{int(time.time())}",
            title=title,
            message=message,
            type=type,
            timestamp=datetime.now(),
            action_required=action_required,
            action_url=action_url,
        )

        self.notifications.append(notification)
        logger.info(f"Added notification: {title}")

    async def _refresh_dashboard(self) -> None:
        """Refresh dashboard data."""

        await self._initialize_dashboard()

    def _handle_control_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle events from control interface."""

        if event_type == "goal_created":
            self._add_notification(
                title="New Goal",
                message=f"Goal '{data.get('title', 'Unknown')}' created",
                type="info",
            )

        elif event_type == "goal_approved":
            self._add_notification(
                title="Goal Approved",
                message=f"Goal '{data.get('title', 'Unknown')}' approved",
                type="success",
            )

        elif event_type == "goal_rejected":
            self._add_notification(
                title="Goal Rejected",
                message=f"Goal '{data.get('title', 'Unknown')}' rejected",
                type="warning",
            )

        elif event_type == "agent_success":
            self._add_notification(
                title="Agent Success",
                message=f"Agent {data.get('agent', 'Unknown')} completed task successfully",
                type="success",
            )

        elif event_type == "agent_failure":
            self._add_notification(
                title="Agent Failure",
                message=f"Agent {data.get('agent', 'Unknown')} failed task",
                type="error",
                action_required=True,
            )

    async def export_data(self, output_path: Path) -> None:
        """Export mobile app data."""

        data = {
            "dashboard": asdict(self.dashboard_data) if self.dashboard_data else None,
            "notifications": [asdict(n) for n in self.notifications],
            "user_preferences": self.user_preferences,
            "exported_at": datetime.now().isoformat(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported mobile app data to {output_path}")


# Global mobile app instance
_global_mobile_app: Optional[MobileApp] = None


def get_mobile_app() -> MobileApp:
    """Get the global mobile app instance."""
    global _global_mobile_app
    if _global_mobile_app is None:
        # Create control interface
        from qa.qa_event_bus import QAEventBus

        event_bus = QAEventBus()
        rules = QARules(version="1.0", agents={}, macros={})
        qa_engine = QAEngine(rules)
        control_interface = MobileControlInterface(qa_engine, event_bus)

        _global_mobile_app = MobileApp(control_interface)
    return _global_mobile_app


async def start_mobile_app() -> None:
    """Start the mobile app."""

    mobile_app = get_mobile_app()
    await mobile_app.initialize()


async def create_goal(title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
    """Create a new goal using the mobile app."""
    
    mobile_app = get_mobile_app()
    goal = await mobile_app.create_goal(
        title=title,
        description=description,
        priority=priority
    )
    
    return {
        "id": goal.id,
        "title": goal.title,
        "description": goal.description,
        "priority": goal.priority.value,
        "status": goal.status.value,
        "created_at": goal.created_at.isoformat()
    }


async def get_goals(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all goals using the mobile app."""
    
    mobile_app = get_mobile_app()
    goals = await mobile_app.get_goals(status_filter)
    
    return [
        {
            "id": goal.id,
            "title": goal.title,
            "description": goal.description,
            "priority": goal.priority.value,
            "status": goal.status.value,
            "created_at": goal.created_at.isoformat()
        }
        for goal in goals
    ]


# Export main classes and functions
__all__ = [
    "MobileApp",
    "MobileNotification",
    "MobileDashboard",
    "MobileAppState",
    "get_mobile_app",
    "start_mobile_app",
    "create_goal",
    "get_goals",
]
