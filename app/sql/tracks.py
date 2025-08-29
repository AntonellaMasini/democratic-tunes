GET_ACTIVE_ROOM_BY_CODE = """
SELECT id
FROM rooms
WHERE code = :code 
AND is_active IS TRUE;
"""

TRACK_EXISTS = """
SELECT 1
FROM tracks
WHERE id = :track_id;
"""

SEARCH_TRACKS = """
SELECT 
    id, 
    title, 
    artist, 
    duration_ms
FROM tracks
WHERE title ILIKE :q OR artist ILIKE :q
ORDER BY title
LIMIT 20;
"""

INSERT_ROOM_TRACK_IF_NOT_EXISTS = """
WITH ins AS (
  INSERT INTO room_tracks (id, room_id, track_id, added_by_user_id, status)
  SELECT :id::uuid, :room_id::uuid, :track_id::text, :user_id::uuid, 'queued'::track_status
  WHERE NOT EXISTS (
    SELECT 1
    FROM room_tracks
    WHERE room_id = :room_id::uuid
      AND track_id = :track_id::text
      AND status = 'queued'::track_status
  )
  RETURNING id
)
SELECT id FROM ins;
"""

COMPUTE_QUEUE = """
WITH votes_sum AS (
  SELECT 
    room_track_id, 
    COALESCE(SUM(value), 0) AS votes_sum
  FROM votes
  GROUP BY room_track_id
)
SELECT
  rt.id AS room_track_id,
  t.id  AS track_id,
  t.title AS title,
  t.artist AS artist,
  t.duration_ms AS duration_ms,
  COALESCE(vs.votes_sum, 0) AS votes,
  rt.created_at AS created_at,
  rt.status AS status,
  rt.added_by_user_id AS added_by_user_id,
  r.host_user_id  AS host_user_id
FROM room_tracks rt
JOIN tracks t ON t.id = rt.track_id
JOIN rooms  r ON r.id = rt.room_id 
LEFT JOIN votes_sum vs 
ON vs.room_track_id = rt.id
WHERE rt.room_id = :room_id::uuid
  AND rt.status = 'queued'::track_status;
"""
