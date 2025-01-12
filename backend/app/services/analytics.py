"""Analytics service for task metrics and insights."""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.core.errors import AnalyticsError

class AnalyticsService:
    """Service for analyzing task metrics and performance."""

    @staticmethod
    async def get_task_metrics_summary(
        db: AsyncSession,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive task metrics summary."""
        try:
            query = select(Task)
            filters = []
            
            if agent_id:
                filters.append(Task.agent_id == agent_id)
            if start_date:
                filters.append(Task.created_at >= start_date)
            if end_date:
                filters.append(Task.created_at <= end_date)
                
            if filters:
                query = query.filter(and_(*filters))
                
            result = await db.execute(query)
            tasks = result.scalars().all()

            # Basic metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "completed"])
            failed_tasks = len([t for t in tasks if t.status == "failed"])
            cancelled_tasks = len([t for t in tasks if t.status == "cancelled"])
            
            # Performance metrics
            execution_times = [t.execution_time for t in tasks if t.execution_time is not None]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Resource usage
            total_tokens = sum(t.metrics.get("tokens_used", 0) for t in tasks if t.metrics)
            total_memory = sum(t.metrics.get("memory_usage", 0) for t in tasks if t.metrics)
            total_cost = sum(t.metrics.get("cost", 0.0) for t in tasks if t.metrics)
            
            # Error analysis
            error_types = {}
            for task in tasks:
                if task.error:
                    error_type = task.error.get("type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Tool usage analysis
            tool_usage = {}
            for task in tasks:
                if task.metrics and "tool_usage" in task.metrics:
                    for tool, count in task.metrics["tool_usage"].items():
                        tool_usage[tool] = tool_usage.get(tool, 0) + count
            
            # Priority-based analysis
            priority_metrics = {}
            for task in tasks:
                if task.priority not in priority_metrics:
                    priority_metrics[task.priority] = {
                        "total": 0,
                        "completed": 0,
                        "failed": 0,
                        "avg_execution_time": 0,
                        "success_rate": 0
                    }
                
                metrics = priority_metrics[task.priority]
                metrics["total"] += 1
                if task.status == "completed":
                    metrics["completed"] += 1
                elif task.status == "failed":
                    metrics["failed"] += 1
                if task.execution_time:
                    current_avg = metrics["avg_execution_time"]
                    metrics["avg_execution_time"] = (
                        (current_avg * (metrics["total"] - 1) + task.execution_time)
                        / metrics["total"]
                    )
                metrics["success_rate"] = metrics["completed"] / metrics["total"]

            return {
                "summary": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "cancelled_tasks": cancelled_tasks,
                    "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
                    "average_execution_time": avg_execution_time
                },
                "resource_usage": {
                    "total_tokens": total_tokens,
                    "total_memory_mb": total_memory,
                    "total_cost_usd": total_cost,
                    "average_tokens_per_task": total_tokens / total_tasks if total_tasks > 0 else 0
                },
                "error_analysis": {
                    "error_types": error_types,
                    "error_rate": failed_tasks / total_tasks if total_tasks > 0 else 0
                },
                "tool_usage": tool_usage,
                "priority_metrics": priority_metrics
            }
            
        except Exception as e:
            raise AnalyticsError(f"Failed to get task metrics summary: {str(e)}")

    @staticmethod
    async def get_task_trends(
        db: AsyncSession,
        agent_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get task execution trends over time."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = select(Task).filter(Task.created_at >= start_date)
            if agent_id:
                query = query.filter(Task.agent_id == agent_id)
            
            result = await db.execute(query)
            tasks = result.scalars().all()
            
            # Group tasks by day
            daily_metrics = {}
            for task in tasks:
                day = task.created_at.date()
                if day not in daily_metrics:
                    daily_metrics[day] = {
                        "total": 0,
                        "completed": 0,
                        "failed": 0,
                        "avg_execution_time": 0,
                        "total_tokens": 0
                    }
                
                metrics = daily_metrics[day]
                metrics["total"] += 1
                if task.status == "completed":
                    metrics["completed"] += 1
                elif task.status == "failed":
                    metrics["failed"] += 1
                if task.execution_time:
                    current_avg = metrics["avg_execution_time"]
                    metrics["avg_execution_time"] = (
                        (current_avg * (metrics["total"] - 1) + task.execution_time)
                        / metrics["total"]
                    )
                if task.metrics:
                    metrics["total_tokens"] += task.metrics.get("tokens_used", 0)
            
            return {
                "daily_metrics": {
                    str(day): metrics for day, metrics in daily_metrics.items()
                },
                "trend_analysis": {
                    "completion_rate_trend": [
                        metrics["completed"] / metrics["total"]
                        for metrics in daily_metrics.values()
                    ],
                    "execution_time_trend": [
                        metrics["avg_execution_time"]
                        for metrics in daily_metrics.values()
                    ],
                    "token_usage_trend": [
                        metrics["total_tokens"]
                        for metrics in daily_metrics.values()
                    ]
                }
            }
            
        except Exception as e:
            raise AnalyticsError(f"Failed to get task trends: {str(e)}")

    @staticmethod
    async def get_agent_performance(
        db: AsyncSession,
        agent_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get detailed agent performance metrics."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = select(Task).filter(
                and_(
                    Task.agent_id == agent_id,
                    Task.created_at >= start_date
                )
            )
            
            result = await db.execute(query)
            tasks = result.scalars().all()
            
            # Task completion metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "completed"])
            failed_tasks = len([t for t in tasks if t.status == "failed"])
            
            # Performance metrics
            execution_times = [t.execution_time for t in tasks if t.execution_time is not None]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Resource efficiency
            total_tokens = sum(t.metrics.get("tokens_used", 0) for t in tasks if t.metrics)
            total_memory = sum(t.metrics.get("memory_usage", 0) for t in tasks if t.metrics)
            
            # Tool proficiency
            tool_success_rates = {}
            for task in tasks:
                if task.metrics and "tool_usage" in task.metrics:
                    for tool, count in task.metrics["tool_usage"].items():
                        if tool not in tool_success_rates:
                            tool_success_rates[tool] = {"used": 0, "successful": 0}
                        tool_success_rates[tool]["used"] += count
                        if task.status == "completed":
                            tool_success_rates[tool]["successful"] += count
            
            return {
                "task_metrics": {
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks,
                    "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0
                },
                "performance_metrics": {
                    "average_execution_time": avg_execution_time,
                    "tokens_per_task": total_tokens / total_tasks if total_tasks > 0 else 0,
                    "memory_per_task": total_memory / total_tasks if total_tasks > 0 else 0
                },
                "tool_proficiency": {
                    tool: {
                        "usage_count": stats["used"],
                        "success_rate": stats["successful"] / stats["used"]
                        if stats["used"] > 0 else 0
                    }
                    for tool, stats in tool_success_rates.items()
                }
            }
            
        except Exception as e:
            raise AnalyticsError(f"Failed to get agent performance metrics: {str(e)}")

    @staticmethod
    async def get_error_insights(
        db: AsyncSession,
        days: int = 30,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get insights into task errors and failures."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            query = select(Task).filter(
                and_(
                    Task.status == "failed",
                    Task.created_at >= start_date
                )
            )
            
            result = await db.execute(query)
            failed_tasks = result.scalars().all()
            
            # Error categorization
            error_types = {}
            error_contexts = {}
            for task in failed_tasks:
                if task.error:
                    error_type = task.error.get("type", "unknown")
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                    
                    # Analyze error context
                    context = task.error.get("context", {})
                    for key, value in context.items():
                        if key not in error_contexts:
                            error_contexts[key] = {}
                        str_value = str(value)
                        error_contexts[key][str_value] = error_contexts[key].get(str_value, 0) + 1
            
            # Sort error types by frequency
            sorted_error_types = sorted(
                error_types.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return {
                "error_summary": {
                    "total_failures": len(failed_tasks),
                    "unique_error_types": len(error_types),
                    "most_common_errors": sorted_error_types
                },
                "error_contexts": error_contexts,
                "temporal_analysis": {
                    "daily_error_counts": {},  # TODO: Implement daily error tracking
                    "error_patterns": {}  # TODO: Implement pattern recognition
                },
                "impact_analysis": {
                    "average_retry_count": sum(t.retry_count for t in failed_tasks) / len(failed_tasks)
                    if failed_tasks else 0,
                    "resource_waste": sum(
                        t.metrics.get("tokens_used", 0) for t in failed_tasks if t.metrics
                    )
                }
            }
            
        except Exception as e:
            raise AnalyticsError(f"Failed to get error insights: {str(e)}")

analytics_service = AnalyticsService() 