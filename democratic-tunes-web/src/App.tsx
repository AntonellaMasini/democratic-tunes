import React, { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  health,
  guest,
  createRoom,
  getQueue,
  searchTracks,
  addTrack,
  vote,
  advance,
  getNowPlaying,
} from "./api";

// Very loose types to avoid TS friction while you iterate
type QueueItem = {
  room_track_id: string;
  track_id: string;
  title: string;
  artist: string;
  duration_ms: number;
  votes: number;
  created_at: string;
  status: "queued" | "playing" | string;
  added_by_user_id: string;
  host_user_id: string;
};

type SearchResult = {
  id: string;
  title: string;
  artist: string;
  duration_ms?: number;
};

function msToMin(ms?: number) {
  if (!ms && ms !== 0) return "";
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function App() {
  // auth / identity
  const [displayName, setDisplayName] = useState<string>("");
  const [userId, setUserId] = useState<string | null>(localStorage.getItem("uid"));

  // // nav state
  // type View = "auth" | "choose" | "created" | "join" | "room";
  // const [view, setView] = useState<View>(userId ? "choose" : "auth");
  type View = "auth" | "choose" | "created" | "join" | "room";

  const [view, setView] = useState<View>(() => {
    const uid = localStorage.getItem("uid");
    const rc = localStorage.getItem("room_code");
    if (uid && rc) return "room";
    if (uid) return "choose";
    return "auth";
  });


  // room state
  const [roomName, setRoomName] = useState("");
  const [roomCodeState, _setRoomCodeState] = useState<string>(
    () => localStorage.getItem("room_code") || ""
  );

  const [joinCode, setJoinCode] = useState("");
  
  const setRoomCode = (code: string) => {
    _setRoomCodeState(code);
    if (code) localStorage.setItem("room_code", code);
    else localStorage.removeItem("room_code");
  };
  
  const roomCode = roomCodeState;
  const [createdRoomCode, setCreatedRoomCode] = useState<string | null>(null);

  function leaveRoom() {
    // invalidate in-flight polls so their results are ignored
    pollSeq.current++;

    // clear persisted and in-memory room info
    setRoomCode("");            // also clears localStorage via your setter
    setCreatedRoomCode(null);

    // clear UI state
    setQueue([]);
    setNowPlaying(null);
    setResults([]);
    setQ("");
    setQueueError(null);
    setErr(null);

    // back to chooser
    setView("choose");
  }

  // queue state
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [queueError, setQueueError] = useState<string | null>(null);

  // search state
  const [q, setQ] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [nowPlaying, setNowPlaying] = useState<any | null>(null);
  const pollSeq = useRef(0);

  const nowPlayingRef = useRef<any | null>(null);
  useEffect(() => { nowPlayingRef.current = nowPlaying; }, [nowPlaying]);

  const queueRef = useRef<QueueItem[]>([]);
  useEffect(() => { queueRef.current = queue; }, [queue]);

  const imgWrap: React.CSSProperties = { marginTop: 12, borderRadius: 12, overflow: "hidden" };
  const fullWidthImg: React.CSSProperties = { width: "100%", height: 200, objectFit: "cover", display: "block" };
  
  function sameNowPlaying(a: any | null, b: any | null) {
    if (!a && !b) return true;
    if (!a || !b) return false;
    return a.room_track_id === b.room_track_id && a.votes === b.votes;
  }

  function sameQueue(a: QueueItem[], b: QueueItem[]) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
      if (
        a[i].room_track_id !== b[i].room_track_id ||
        a[i].votes !== b[i].votes ||
        a[i].status !== b[i].status
      ) return false;
    }
    return true;
  }


  // Health-check once so the first interaction feels snappy
  useEffect(() => {
    health().catch(() => {});
  }, []);

  // Poll queue when in room
  useEffect(() => {
    let t: number | undefined;
  
  async function poll() {
    if (!roomCode) return;
    try {
      const seq = ++pollSeq.current;
      const [npResp, q] = await Promise.all([
        getNowPlaying(roomCode),
        getQueue(roomCode),
      ]);
      if (pollSeq.current !== seq) return; // ignore stale responses
  
      // Prefer explicit now_playing from API
      let candidate = npResp?.now_playing ?? null;
  
      // If API says null, try to infer from queue
      if (!candidate) {
        const fromQueue = q.find((x: any) => x.status === "playing");
        if (fromQueue) candidate = fromQueue;
      }
  
      // Last resort: keep previous to avoid flashing empty
      if (!candidate) candidate = nowPlayingRef.current;

      if (!sameNowPlaying(nowPlayingRef.current, candidate)) {
        setNowPlaying(candidate ?? null);
      }
      if (!sameQueue(queueRef.current, q)) {
        setQueue(q);
      }
  
      setNowPlaying(candidate ?? null);
      setQueue(q);
      setQueueError(null);
    } catch (e: any) {
      setQueueError(e?.message || "Failed to load queue/now playing");
    } finally {
    }
  }
  
    if (view === "room" && roomCode) {
      poll();
      t = window.setInterval(poll, 4000);
    }
    return () => { if (t) clearInterval(t); };
  }, [view, roomCode]);
  
  const queueOnly = useMemo(
    () => queue.filter((x) => x.status !== "playing"),
    [queue]
  );
  
  // --- actions ---
  async function onCreateGuest(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    const name = displayName.trim();
    if (!name) {
      setErr("Please enter a display name");
      return;
    }
    try {
      const resp = await guest(name); // expects { user_id, display_name }
      // keep localStorage for header fallback (X-User-ID)
      // @ts-ignore
      const id = resp.user_id as string;
      localStorage.setItem("uid", id);
      setUserId(id);
      setView("choose");
    } catch (e: any) {
      setErr(e?.message || "Failed to create guest");
    }
  }

  async function onCreateRoom(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    if (!userId) {
      setErr("Guest not set. Please go back and set a guest name.");
      return;
    }
    const name = roomName.trim() || "My Room";
    try {
      const data = await createRoom(name, userId);
      // Expect shape like { code: "ABCD1234", id: "...", host_user_id: "..." }
      const code = (data.code as string) || "";
      setCreatedRoomCode(code);
      setRoomCode(code);
      setView("created");
    } catch (e: any) {
      setErr(e?.message || "Failed to create room");
    }
  }

  async function onJoinRoom(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    const code = joinCode.trim().toUpperCase();
    if (!code) {
      setErr("Enter a room code");
      return;
    }
    try {
      // validate against API first
      await getQueue(code);
      setRoomCode(code);    // persists to localStorage
      setView("room");
    } catch {
      setErr("Invalid room code");
    }
  }

  async function onSearch(e: FormEvent) {
    e.preventDefault();
    setSearching(true);
    setErr(null);
    try {
      const data = await searchTracks(q);
      setResults(data);
    } catch (e: any) {
      setErr(e?.message || "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function onAddTrack(track_id: string) {
    if (!roomCode) return;
    try {
      await addTrack(roomCode, track_id);
      // refresh queue shortly after add
      const data = await getQueue(roomCode);
      setQueue(data);
    } catch (e: any) {
      setErr(e?.message || "Failed to add track");
    }
  }

  async function onVote(id: string, value: 1 | -1) {
    if (!roomCode) return;
    try {
      await vote(roomCode, id, value);
      const data = await getQueue(roomCode);
      setQueue(data);
    } catch (e: any) {
      setErr(e?.message || "Vote failed");
    }
  }


  async function onAdvance() {
    if (!roomCode) return;
    try {
      const { now_playing, queue } = await advance(roomCode);
      setNowPlaying(now_playing ?? null);
      setQueue(queue);
      setErr(null);
    } catch (e: any) {
      // ky throws HTTPError with a .response
      if (e?.response?.status === 403) {
        setErr(
          "Easy, DJ! Only the host can skip songs. It’s a democracy… unless the host says nope! Dance it out instead! 😉🕺"
        );
      } else {
        setErr(e?.message || "Advance failed");
      }
    }
  }
  

  // --- views ---
  if (view === "auth") {
    return (
      <div style={shell}>
        <Card>
          <h1>democratic-tunes</h1>
          <p>Pick a display name to get started!</p>
          <form onSubmit={onCreateGuest} style={{ display: "grid", gap: 12 }}>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Your name"
              maxLength={64}
            />
            <button type="submit">Continue</button>
          </form>
          {err && <ErrorNote>{err}</ErrorNote>}
        </Card>
      </div>
    );
  }

  if (view === "choose") {
    return (
      <div style={shell}>
        <Card>
          <h2>Welcome{displayName ? `, ${displayName}` : ""}!</h2>
          <div style={{ display: "grid", gap: 16 }}>
            <form onSubmit={onCreateRoom} style={{ display: "grid", gap: 8 }}>
              <label>Room name</label>
              <input
                value={roomName}
                onChange={(e) => setRoomName(e.target.value)}
                placeholder="My party"
              />
              <button type="submit">Create Room</button>
            </form>
            <div style={{ opacity: 0.6, textAlign: "center" }}>— or —</div>
            <form onSubmit={onJoinRoom} style={{ display: "grid", gap: 8 }}>
              <label>Join with code</label>
              <input
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value)}
                placeholder="8TVDCKVX"
              />
              <button type="submit">Join Room</button>
            </form>
          </div>
          {err && <ErrorNote>{err}</ErrorNote>}
        </Card>
      </div>
    );
  }

  if (view === "created" && createdRoomCode) {
    return (
      <div style={shell}>
        <Card>
          <h2>Room created 🎉</h2>
          <p>Share this code with friends:</p>
          <code style={codeBox}>{createdRoomCode}</code>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => navigator.clipboard.writeText(createdRoomCode)}>
              Copy
            </button>
            <button onClick={() => setView("room")}>Enter room</button>
          </div>
        </Card>
      </div>
    );
  }

  // room view
  return (
    <div style={shellWide}>
    <header style={header}>
      <div>
        <b>Room:</b> <code>{roomCode}</code>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={onAdvance} title="End current track & advance">
          ⏭ Advance
        </button>
        <button onClick={leaveRoom} title="Return to room chooser">
          Leave room
        </button>
      </div>
    </header>

    <div style={bannerWrap}>
      <img
        src={`${import.meta.env.BASE_URL}illustration1.png`}
        alt="Party vibes"
        style={bannerImg}
        loading="lazy"
      />
    </div>

      <main style={grid}>
        <section style={panelCol}>
          <h3>Now Playing</h3>
          {nowPlaying ? (
            <div style={npCard}>
              <div style={{ fontWeight: 600 }}>{nowPlaying.title}</div>
              <div style={{ opacity: 0.75 }}>
                {nowPlaying.artist} · {msToMin(nowPlaying.duration_ms)}
              </div>
              <div>Votes: {nowPlaying.votes}</div>
            </div>
          ) : (
            <div style={{ opacity: 0.7 }}>Nothing playing yet</div>
          )}

          <h3 style={{ marginTop: 8 }}>Queue</h3>

          {/* Only this part scrolls */}
          <div style={scrollArea}>
            {queueOnly.length === 0 && <div style={{ opacity: 0.7 }}>No tracks yet</div>}
            {queueOnly.map((t) => (
              <div key={t.room_track_id} style={row}>
                <div style={{ minWidth: 44, textAlign: "right" }}>{t.votes}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{t.title}</div>
                  <div style={{ opacity: 0.75 }}>
                    {t.artist} · {msToMin(t.duration_ms)}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button onClick={() => onVote(t.room_track_id, 1)}>👍</button>
                  <button onClick={() => onVote(t.room_track_id, -1)}>👎</button>
                </div>
              </div>
            ))}
          </div>
          {queueError && <ErrorNote>{queueError}</ErrorNote>}
        </section>


        <section style={panelCol}>
          <h3>Add Tracks</h3>
          {/* Form stays fixed height at top */}
          <form onSubmit={onSearch} style={{ display: "flex", gap: 8 }}>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder=" search songs…"
            />
            <button type="submit" disabled={searching}>
              {searching ? "Searching…" : "Search"}
            </button>
          </form>

          {/* Only results scroll; search bar doesnt move */}
          <div style={scrollArea}>
            {results.map((r) => (
              <div key={r.id} style={row}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{r.title}</div>
                  <div style={{ opacity: 0.75 }}>
                    {r.artist} {r.duration_ms ? `· ${msToMin(r.duration_ms)}` : ""}
                  </div>
                </div>
                <button onClick={() => onAddTrack(r.id)}>Add</button>
              </div>
            ))}
          </div>

          {err && <ErrorNote>{err}</ErrorNote>}
        </section>

      </main>
    </div>
  );
}



// --- lil’ styles (kept inline for simplicity) ---
const shell: React.CSSProperties = {
  minHeight: "100vh",
  width: "100vw",
  display: "grid",
  placeItems: "center",
  padding: 24,
  background: "#0b0c10",
  color: "#e8e8ea",
  fontFamily:
    "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
};

// full-viewport, centered column layout
const shellWide: React.CSSProperties = {
  minHeight: "100vh",
  width: "100vw",
  display: "flex",
  flexDirection: "vertical" as any, // or "column" if your TS config complains
  alignItems: "center",
  padding: 24,
  background: "#0b0c10",
  color: "#e8e8ea",
  fontFamily:
    "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
};

const Card: React.FC<React.PropsWithChildren> = ({ children }) => (
  <div style={{ padding: 24, borderRadius: 16, background: "#111217", width: 420, maxWidth: "100%", display: "grid", gap: 12, boxShadow: "0 6px 24px rgba(0,0,0,.25)" }}>
    {children}
  </div>
);

const header: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  gap: 12,
  padding: 16,
  borderRadius: 16,
  background: "#111217",
  width: "min(1200px, 100%)",
  margin: "24px auto 12px",
};

// main content area: always centered, fixed max width, fills the rest of screen
const grid: React.CSSProperties = {
  width: "min(1200px, 100%)",
  margin: "0 auto 24px",
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: 16,
  flex: "1 1 auto",  // fill remaining vertical space
  minHeight: 0,      // allow children to compute 100% height correctly
};


// panel that is a fixed-height column; only inner list scrolls
const panelCol: React.CSSProperties = {
  padding: 16,
  borderRadius: 16,
  background: "#111217",
  display: "flex",
  flexDirection: "column",
  gap: 12,
  height: "100%",  // fill the grid row
  minHeight: 0,    // important so inner scroll areas can size
};

// reusable scroll area
const scrollArea: React.CSSProperties = {
  flex: 1,
  minHeight: 0,
  overflowY: "auto",
  display: "grid",
  gap: 8,
  paddingRight: 4,  // little room for scrollbar
};

const row: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 12,
  padding: "8px 10px",
  borderRadius: 12,
  background: "#181a22",
};

const npCard: React.CSSProperties = {
  ...row,
  background: "#18202a",
};

const codeBox: React.CSSProperties = {
  display: "inline-block",
  padding: "8px 12px",
  background: "#181a22",
  borderRadius: 8,
  fontSize: 18,
  letterSpacing: 1.5,
};

const ErrorNote: React.FC<React.PropsWithChildren> = ({ children }) => (
  <div style={{ marginTop: 10, color: "#ffb3b3" }}>{children}</div>
);

const bannerWrap: React.CSSProperties = {
  width: "min(1200px, 100%)",
  margin: "0 auto 12px",
  borderRadius: 16,
  overflow: "hidden",
  boxShadow: "0 6px 24px rgba(0,0,0,.25)"
};

const bannerImg: React.CSSProperties = {
  width: "100%",
  height: 220,      // tweak height as you like
  display: "block",
  objectFit: "cover"
};
