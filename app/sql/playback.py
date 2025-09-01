GET_ACTIVE_ROOM_WITH_HOST = """
SELECT id, host_user_id
FROM rooms
WHERE code = :code AND is_active IS TRUE;
"""

GET_CURRENT_PLAYING = """
SELECT id
FROM room_tracks
WHERE room_id = CAST(:room_id AS uuid)
  AND status = 'playing'::track_status
ORDER BY created_at DESC
LIMIT 1;
"""

MARK_PLAYED = """
UPDATE room_tracks
SET status = 'played'::track_status
WHERE id = CAST(:room_track_id AS uuid);
"""

SET_PLAYING = """
UPDATE room_tracks
SET status = 'playing'::track_status
WHERE id = CAST(:room_track_id AS uuid);
"""

GET_NOW_PLAYING_DETAILS = """
WITH votes_sum AS (
  SELECT room_track_id, 
  COALESCE(SUM(value), 0) AS votes
  FROM votes
  GROUP BY room_track_id
)
SELECT
  rt.id AS room_track_id,
  t.id AS track_id,
  t.title AS title,
  t.artist AS artist,
  t.duration_ms AS duration_ms,
  COALESCE(vs.votes, 0) AS votes,
  rt.created_at AS created_at,
  rt.status AS status,
  rt.added_by_user_id AS added_by_user_id,
  r.host_user_id AS host_user_id
FROM room_tracks rt
JOIN tracks t 
    ON t.id = rt.track_id
JOIN rooms  r 
    ON r.id = rt.room_id
LEFT JOIN votes_sum vs 
     ON vs.room_track_id = rt.id
WHERE rt.room_id = CAST(:room_id AS uuid)
  AND rt.status = 'playing'::track_status
ORDER BY rt.created_at DESC
LIMIT 1;
"""