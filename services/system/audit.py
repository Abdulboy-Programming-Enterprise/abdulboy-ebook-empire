"""
Audit Service
=============
Service for logging and retrieving audit trails of admin actions.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from app.models.audit import AuditLog
from app.core.logger import logger


class AuditService:
    """Service for audit logging."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_action(
        self,
        admin_id: Optional[str],
        admin_email: Optional[str],
        action_type: str,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an admin action to audit trail."""
        audit_log = AuditLog(
            admin_id=admin_id,
            admin_email=admin_email,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )
        
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        
        logger.info(f"Audit log created: {action_type} by {admin_email}")
        
        return audit_log
    
    async def get_audit_logs(
        self,
        admin_id: Optional[str] = None,
        action_type: Optional[str] = None,
        target_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50
    ) -> tuple[List[AuditLog], int]:
        """Get audit logs with filters."""
        query = select(AuditLog)
        
        if admin_id:
            query = query.where(AuditLog.admin_id == admin_id)
        
        if action_type:
            query = query.where(AuditLog.action_type == action_type)
        
        if target_type:
            query = query.where(AuditLog.target_type == target_type)
        
        if start_date:
            query = query.where(AuditLog.created_at >= start_date)
        
        if end_date:
            query = query.where(AuditLog.created_at <= end_date)
        
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        
        query = query.order_by(AuditLog.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return logs, total or 0
    
    async def get_user_audit_logs(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 50
    ) -> tuple[List[AuditLog], int]:
        """Get audit logs for actions affecting a specific user."""
        return await self.get_audit_logs(
            target_type="user",
            target_id=user_id,
            page=page,
            limit=limit
        )
    
    async def get_admin_action_logs(
        self,
        admin_id: str,
        page: int = 1,
        limit: int = 50
    ) -> tuple[List[AuditLog], int]:
        """Get audit logs for actions performed by a specific admin."""
        return await self.get_audit_logs(
            admin_id=admin_id,
            page=page,
            limit=limit
        )
