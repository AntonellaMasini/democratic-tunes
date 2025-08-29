from datetime import datetime, timezone

def score_room_track(created_at, votes_sum: int, is_host_add: bool=False,
                     w_age=0.25, t_age=600, w_host=0.1, now=None) -> float:
    """
    votes_sum: net (+1/-1)
    w_age: weight for age bonus; reaches full after t_age seconds
    w_host: weight for host bonus ;) , perks of hosting!
    """
    now = now or datetime.now(timezone.utc)
    
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
        
    age = (now - created_at).total_seconds()

    age_bonus = w_age * min(age / t_age, 1.0)
    host_bonus = w_host if is_host_add else 0.0
    return votes_sum + age_bonus + host_bonus
