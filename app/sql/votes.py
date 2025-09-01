GET_ROOM_TRACK_IN_ROOM = """
SELECT 1
FROM room_tracks
WHERE id = CAST(:room_track_id AS uuid)
  AND room_id = CAST(:room_id AS uuid)
  AND status = 'queued'::track_status;
"""

UPSERT_VOTE = """
INSERT INTO votes (id, room_track_id, user_id, value)
VALUES (
    CAST(:id AS uuid), 
    CAST(:room_track_id AS uuid), 
    CAST(:user_id AS uuid), 
    CAST(:value AS int))
ON CONFLICT (room_track_id, user_id)
DO UPDATE SET value = EXCLUDED.value
RETURNING id;
"""