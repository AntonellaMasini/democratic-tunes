GET_ROOM_TRACK_IN_ROOM = """
SELECT 1
FROM room_tracks
WHERE id = :room_track_id::uuid
  AND room_id = :room_id::uuid
  AND status = 'queued'::track_status;
"""

UPSERT_VOTE = """
INSERT INTO votes (id, room_track_id, user_id, value)
VALUES (
    :id::uuid, 
    :room_track_id::uuid, 
    :user_id::uuid, 
    :value::int)
ON CONFLICT (room_track_id, user_id)
DO UPDATE SET value = EXCLUDED.value
RETURNING id;
"""