import ky from "ky";

const api = ky.create({
  prefixUrl: import.meta.env.VITE_API_BASE,
  credentials: "include", // keep the uid cookie
  headers: { "content-type": "application/json" },
  hooks: {
    beforeRequest: [
    r => {
        const uid = localStorage.getItem("uid");
        if (uid) r.headers.set("X-User-ID", uid);
    }
    ]
}
});

export const health = () => api.get("health").json();

export const guest = (display_name: string) =>
  api.post("auth/guest", { json: { display_name } }).json();

export const createRoom = (name: string, userId: string) =>
  api.post("rooms", {
    json: { name },
    headers: { "X-User-ID": userId },
  }).json<any>();

export const getQueue = (code: string) =>
  api.get(`tracks/rooms/${code}/queue`).json<any>();

export const searchTracks = (q: string) =>
  api.get("tracks/search", { searchParams: { q } }).json<any>();

export const addTrack = (code: string, track_id: string) =>
  api.post(`tracks/rooms/${code}/tracks`, { json: { track_id } }).json<any>();

export const vote = (code: string, room_track_id: string, value: 1 | -1) =>
  api.post(`votes/rooms/${code}/votes`, { json: { room_track_id, value } }).json<any>();

export const advance = (code: string) =>
  api.post(`playback/rooms/${code}/advance`).json<{ now_playing: any | null, queue: any[] }>();