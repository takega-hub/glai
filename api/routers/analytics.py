from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from api.auth.security import get_current_user, roles_required
from api.database.connection import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

class UserAnalytics(BaseModel):
    total_users: int
    active_users_7d: int
    active_users_30d: int
    new_users_7d: int
    new_users_30d: int
    retention_rate_7d: float
    retention_rate_30d: float

class RevenueAnalytics(BaseModel):
    total_revenue_7d: float
    total_revenue_30d: float
    total_revenue_lifetime: float
    average_revenue_per_user: float
    top_packages: List[Dict]
    revenue_by_day: List[Dict]

class CharacterAnalytics(BaseModel):
    character_id: int
    character_name: str
    total_interactions: int
    unique_users: int
    average_trust_score: float
    most_popular_content: List[Dict]
    engagement_rate: float

class ContentAnalytics(BaseModel):
    total_content: int
    content_by_type: Dict[str, int]
    unlocked_content: int
    content_engagement: Dict[str, float]
    top_content: List[Dict]

class TrustScoreAnalytics(BaseModel):
    average_trust_score: float
    trust_score_distribution: Dict[str, int]
    trust_score_progression: List[Dict]
    top_users_by_trust: List[Dict]

class SystemHealth(BaseModel):
    database_status: str
    api_response_time: float
    active_connections: int
    error_rate: float
    uptime_percentage: float

class CharacterPopularity(BaseModel):
    name: str
    user_count: int

@router.get("/users", response_model=UserAnalytics)
async def get_user_analytics(
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Get user analytics and metrics"""
    
    # Total users
    total_users = await db.fetchval("SELECT COUNT(*) FROM users WHERE role = 'app_user'")
    
    # Active users in last 7 and 30 days
    active_users_7d = await db.fetchval(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM messages 
        WHERE created_at >= NOW() - INTERVAL '7 days'
        """
    )
    
    active_users_30d = await db.fetchval(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM messages 
        WHERE created_at >= NOW() - INTERVAL '30 days'
        """
    )
    
    # New users in last 7 and 30 days
    new_users_7d = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days' AND role = 'app_user'"
    )
    
    new_users_30d = await db.fetchval(
        "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '30 days' AND role = 'app_user'"
    )
    
    # Retention rates (users active in both periods)
    retention_7d = await db.fetchval(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM messages 
        WHERE created_at >= NOW() - INTERVAL '14 days' 
        AND created_at < NOW() - INTERVAL '7 days'
        AND user_id IN (
            SELECT DISTINCT user_id FROM messages 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        )
        """
    )
    
    retention_30d = await db.fetchval(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM messages 
        WHERE created_at >= NOW() - INTERVAL '60 days' 
        AND created_at < NOW() - INTERVAL '30 days'
        AND user_id IN (
            SELECT DISTINCT user_id FROM messages 
            WHERE created_at >= NOW() - INTERVAL '30 days'
        )
        """
    )
    
    # Calculate retention rates
    active_users_14d = await db.fetchval(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM messages 
        WHERE created_at >= NOW() - INTERVAL '14 days'
        """
    )
    
    active_users_60d = await db.fetchval(
        """
        SELECT COUNT(DISTINCT user_id) 
        FROM messages 
        WHERE created_at >= NOW() - INTERVAL '60 days'
        """
    )
    
    retention_rate_7d = (retention_7d / max(active_users_14d, 1)) * 100
    retention_rate_30d = (retention_30d / max(active_users_60d, 1)) * 100
    
    return UserAnalytics(
        total_users=total_users,
        active_users_7d=active_users_7d,
        active_users_30d=active_users_30d,
        new_users_7d=new_users_7d,
        new_users_30d=new_users_30d,
        retention_rate_7d=retention_rate_7d,
        retention_rate_30d=retention_rate_30d
    )

@router.get("/revenue", response_model=RevenueAnalytics)
async def get_revenue_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Get revenue analytics"""
    
    # Total revenue in period
    total_revenue_period = await db.fetchval(
        """
        SELECT COALESCE(SUM(price_usd * t.token_amount / token_packages.token_amount), 0)
        FROM transactions t
        JOIN token_packages ON t.related_id = token_packages.id
        WHERE t.type = 'purchase' AND t.created_at >= NOW() - INTERVAL '%s days'
        """ % days
    )
    
    # Total revenue lifetime
    total_revenue_lifetime = await db.fetchval(
        """
        SELECT COALESCE(SUM(price_usd * t.token_amount / token_packages.token_amount), 0)
        FROM transactions t
        JOIN token_packages ON t.related_id = token_packages.id
        WHERE t.type = 'purchase'
        """
    )
    
    # Revenue by day
    revenue_by_day = await db.fetch(
        """
        SELECT 
            DATE(t.created_at) as date,
            COALESCE(SUM(price_usd * t.token_amount / token_packages.token_amount), 0) as revenue
        FROM transactions t
        JOIN token_packages ON t.related_id = token_packages.id
        WHERE t.type = 'purchase' AND t.created_at >= NOW() - INTERVAL '%s days'
        GROUP BY DATE(t.created_at)
        ORDER BY date DESC
        """ % days
    )
    
    # Top packages
    top_packages = await db.fetch(
        """
        SELECT 
            tp.name,
            COUNT(*) as purchase_count,
            SUM(tp.price_usd) as total_revenue
        FROM transactions t
        JOIN token_packages tp ON t.related_id = tp.id
        WHERE t.type = 'purchase' AND t.created_at >= NOW() - INTERVAL '%s days'
        GROUP BY tp.id, tp.name
        ORDER BY total_revenue DESC
        LIMIT 5
        """ % days
    )
    
    # Average revenue per user
    total_users = await db.fetchval("SELECT COUNT(*) FROM users WHERE role = 'app_user'")
    avg_revenue_per_user = total_revenue_lifetime / max(total_users, 1)
    
    return RevenueAnalytics(
        total_revenue_7d=total_revenue_period if days <= 7 else 0,
        total_revenue_30d=total_revenue_period if days <= 30 else 0,
        total_revenue_lifetime=total_revenue_lifetime,
        average_revenue_per_user=avg_revenue_per_user,
        top_packages=[dict(pkg) for pkg in top_packages],
        revenue_by_day=[dict(day) for day in revenue_by_day]
    )

@router.get("/characters", response_model=List[CharacterAnalytics])
async def get_character_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Get character analytics"""
    
    # Get character stats
    character_stats = await db.fetch(
        """
        SELECT 
            c.id as character_id,
            c.name as character_name,
            COUNT(DISTINCT m.user_id) as unique_users,
            COUNT(m.id) as total_interactions,
            AVG(ucs.trust_score) as average_trust_score
        FROM characters c
        LEFT JOIN messages m ON c.id = m.character_id 
            AND m.created_at >= NOW() - INTERVAL '%s days'
        LEFT JOIN user_character_state ucs ON c.id = ucs.character_id
        GROUP BY c.id, c.name
        ORDER BY total_interactions DESC
        """ % days
    )
    
    result = []
    for char_stat in character_stats:
        # Get most popular content for this character
        popular_content = await db.fetch(
            """
            SELECT 
                content.description,
                content.type,
                COUNT(*) as unlock_count
            FROM content
            JOIN transactions t ON content.id = t.related_content_id
            WHERE content.character_id = :character_id 
                AND t.type = 'content_unlock'
                AND t.created_at >= NOW() - INTERVAL '%s days'
            GROUP BY content.id, content.description, content.type
            ORDER BY unlock_count DESC
            LIMIT 3
            """ % days,
            {"character_id": char_stat["character_id"]}
        )
        
        # Calculate engagement rate (messages per user)
        engagement_rate = char_stat["total_interactions"] / max(char_stat["unique_users"], 1)
        
        result.append(CharacterAnalytics(
            character_id=char_stat["character_id"],
            character_name=char_stat["character_name"],
            total_interactions=char_stat["total_interactions"],
            unique_users=char_stat["unique_users"],
            average_trust_score=char_stat["average_trust_score"] or 0,
            most_popular_content=[dict(content) for content in popular_content],
            engagement_rate=engagement_rate
        ))
    
    return result

@router.get("/characters/popularity", response_model=List[CharacterPopularity])
async def get_character_popularity(
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Get character popularity based on user selections."""
    query = """
        SELECT c.name, COUNT(uc.user_id) as user_count
        FROM characters c
        JOIN user_character_state uc ON c.id = uc.character_id
        GROUP BY c.name
        ORDER BY user_count DESC;
    """
    popularity_data = await db.fetch(query)
    return [CharacterPopularity(**row) for row in popularity_data]

@router.get("/content", response_model=ContentAnalytics)
async def get_content_analytics(
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Get content analytics"""
    
    # Total content
    total_content = await db.fetchval("SELECT COUNT(*) FROM content")
    
    # Content by type
    content_by_type = await db.fetch(
        """
        SELECT type, COUNT(*) as count
        FROM content
        GROUP BY type
        """
    )
    
    # Unlocked content
    unlocked_content = await db.fetchval(
        "SELECT COUNT(*) FROM content WHERE is_locked = false"
    )
    
    # Content engagement (unlock rate)
    content_engagement = {}
    for content_type in ["photo", "video", "audio", "text"]:
        total = await db.fetchval(
            "SELECT COUNT(*) FROM content WHERE type = :type",
            {"type": content_type}
        )
        unlocked = await db.fetchval(
            """
            SELECT COUNT(*) FROM content 
            WHERE type = :type AND is_locked = false
            """,
            {"type": content_type}
        )
        engagement_rate = (unlocked / max(total, 1)) * 100
        content_engagement[content_type] = engagement_rate
    
    # Top content by unlocks
    top_content = await db.fetch(
        """
        SELECT 
            c.description,
            c.type,
            COUNT(t.id) as unlock_count
        FROM content c
        JOIN transactions t ON c.id = t.related_content_id
        WHERE t.type = 'content_unlock'
        GROUP BY c.id, c.description, c.type
        ORDER BY unlock_count DESC
        LIMIT 10
        """
    )
    
    return ContentAnalytics(
        total_content=total_content,
        content_by_type={item["type"]: item["count"] for item in content_by_type},
        unlocked_content=unlocked_content,
        content_engagement=content_engagement,
        top_content=[dict(content) for content in top_content]
    )

@router.get("/trust-scores", response_model=TrustScoreAnalytics)
async def get_trust_score_analytics(
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Get trust score analytics"""
    
    # Average trust score
    avg_trust_score = await db.fetchval(
        "SELECT AVG(trust_score) FROM user_character_state"
    )
    
    # Trust score distribution
    trust_distribution = await db.fetch(
        """
        SELECT 
            CASE 
                WHEN trust_score < 20 THEN '0-19'
                WHEN trust_score < 50 THEN '20-49'
                WHEN trust_score < 80 THEN '50-79'
                WHEN trust_score < 120 THEN '80-119'
                ELSE '120+'
            END as range,
            COUNT(*) as count
        FROM user_character_state
        GROUP BY range
        ORDER BY range
        """
    )
    
    # Trust score progression over time
    trust_progression = await db.fetch(
        """
        SELECT 
            DATE(created_at) as date,
            AVG(points) as avg_points_change
        FROM trust_score_history
        WHERE created_at >= NOW() - INTERVAL '30 days'
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
    )
    
    # Top users by trust score
    top_users = await db.fetch(
        """
        SELECT 
            u.username,
            ucs.character_id,
            c.name as character_name,
            ucs.trust_score
        FROM user_character_state ucs
        JOIN users u ON ucs.user_id = u.id
        JOIN characters c ON ucs.character_id = c.id
        ORDER BY ucs.trust_score DESC
        LIMIT 10
        """
    )
    
    return TrustScoreAnalytics(
        average_trust_score=avg_trust_score or 0,
        trust_score_distribution={item["range"]: item["count"] for item in trust_distribution},
        trust_score_progression=[dict(day) for day in trust_progression],
        top_users_by_trust=[dict(user) for user in top_users]
    )

@router.get("/system-health", response_model=SystemHealth)
async def get_system_health(
    current_user=Depends(roles_required(["super_admin"])),
    db=Depends(get_db)
):
    """Get system health metrics"""
    
    # Database status
    try:
        await db.fetchval("SELECT 1")
        database_status = "healthy"
    except Exception:
        database_status = "unhealthy"
    
    # API response time (simplified - would need proper monitoring)
    api_response_time = 0.1  # Placeholder
    
    # Active connections (simplified)
    active_connections = await db.fetchval(
        "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
    )
    
    # Error rate (simplified - would need proper error tracking)
    error_rate = 0.01  # Placeholder
    
    # Uptime percentage (simplified)
    uptime_percentage = 99.9  # Placeholder
    
    return SystemHealth(
        database_status=database_status,
        api_response_time=api_response_time,
        active_connections=active_connections,
        error_rate=error_rate,
        uptime_percentage=uptime_percentage
    )

@router.get("/custom-report")
async def get_custom_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    metrics: List[str] = Query(["users", "revenue", "engagement"]),
    group_by: str = Query("day"),  # day, week, month
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Generate custom analytics report"""
    
    report_data = {}
    
    if "users" in metrics:
        # User metrics for the period
        user_data = await db.fetch(
            """
            SELECT 
                DATE_TRUNC(:group_by, created_at) as period,
                COUNT(*) as new_users,
                COUNT(DISTINCT CASE WHEN last_active >= created_at THEN id END) as active_users
            FROM users
            WHERE created_at BETWEEN :start_date AND :end_date
            GROUP BY period
            ORDER BY period
            """,
            {"start_date": start_date, "end_date": end_date, "group_by": group_by}
        )
        report_data["users"] = [dict(item) for item in user_data]
    
    if "revenue" in metrics:
        # Revenue metrics for the period
        revenue_data = await db.fetch(
            """
            SELECT 
                DATE_TRUNC(:group_by, created_at) as period,
                SUM(amount_usd) as revenue,
                COUNT(DISTINCT user_id) as paying_users
            FROM transactions
            WHERE created_at BETWEEN :start_date AND :end_date
            AND type = 'purchase'
            GROUP BY period
            ORDER BY period
            """,
            {"start_date": start_date, "end_date": end_date, "group_by": group_by}
        )
        report_data["revenue"] = [dict(item) for item in revenue_data]
    
    if "engagement" in metrics:
        # Engagement metrics for the period
        engagement_data = await db.fetch_all(
            """
            SELECT 
                DATE_TRUNC(:group_by, created_at) as period,
                COUNT(*) as total_messages,
                COUNT(DISTINCT user_id) as active_users,
                AVG(trust_score_change) as avg_trust_change
            FROM messages
            WHERE created_at BETWEEN :start_date AND :end_date
            GROUP BY period
            ORDER BY period
            """,
            {"start_date": start_date, "end_date": end_date, "group_by": group_by}
        )
        report_data["engagement"] = [dict(item) for item in engagement_data]
    
    return {
        "report_period": {
            "start_date": start_date,
            "end_date": end_date,
            "group_by": group_by
        },
        "metrics": report_data,
        "generated_at": datetime.utcnow()
    }

@router.get("/export-report")
async def export_analytics_report(
    format: str = Query("json", pattern="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
    current_user=Depends(roles_required(["analyst", "super_admin"])),
    db=Depends(get_db)
):
    """Export analytics report in specified format"""
    
    # Get all analytics data
    user_analytics = await get_user_analytics(current_user, db)
    revenue_analytics = await get_revenue_analytics(days, current_user, db)
    character_analytics = await get_character_analytics(days, current_user, db)
    content_analytics = await get_content_analytics(current_user, db)
    trust_analytics = await get_trust_score_analytics(current_user, db)
    
    report_data = {
        "report_date": datetime.utcnow(),
        "period_days": days,
        "user_analytics": user_analytics.dict(),
        "revenue_analytics": revenue_analytics.dict(),
        "character_analytics": [char.dict() for char in character_analytics],
        "content_analytics": content_analytics.dict(),
        "trust_analytics": trust_analytics.dict()
    }
    
    if format == "json":
        return report_data
    elif format == "csv":
        # Convert to CSV format (simplified implementation)
        csv_data = "Metric,Value\n"
        csv_data += f"Total Users,{user_analytics.total_users}\n"
        csv_data += f"Active Users (7d),{user_analytics.active_users_7d}\n"
        csv_data += f"Active Users (30d),{user_analytics.active_users_30d}\n"
        csv_data += f"Total Revenue (30d),{revenue_analytics.total_revenue_30d}\n"
        csv_data += f"Average Trust Score,{trust_analytics.average_trust_score}\n"
        
        return {"csv_data": csv_data}
    
    return report_data