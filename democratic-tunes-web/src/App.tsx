// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
// import './App.css'

// function App() {
//   const [count, setCount] = useState(0)

//   return (
//     <>
//       <div>
//         <a href="https://vite.dev" target="_blank">
//           <img src={viteLogo} className="logo" alt="Vite logo" />
//         </a>
//         <a href="https://react.dev" target="_blank">
//           <img src={reactLogo} className="logo react" alt="React logo" />
//         </a>
//       </div>
//       <h1>Vite + React</h1>
//       <div className="card">
//         <button onClick={() => setCount((count) => count + 1)}>
//           count is {count}
//         </button>
//         <p>
//           Edit <code>src/App.tsx</code> and save to test HMR
//         </p>
//       </div>
//       <p className="read-the-docs">
//         Click on the Vite and React logos to learn more
//       </p>
//     </>
//   )
// }

// export default App

import { useEffect, useRef, useState } from "react";
import * as api from "./api";

type QueueItem = {
  room_track_id: string;
  track_id: string;
  title: string;
  artist: string;
  duration_ms: number;
  votes: number;
  score: number;
  status: "queued" | "playing" | "played" | "removed";
  created_at: string;
};

export default function App() {
  const [code, setCode] = useState<string>("");
  const [displayName, setDisplayName] = useState("guest");
  const [uid, setUid] = useState<string>(""); // optional: store from cookie if you expose it
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [nowPlaying, setNowPlaying] = useState<QueueItem | null>(null);
  const [progressMs, setProgressMs] = useState(0);

  // 1) create guest on load (sets HttpOnly cookie)
  useEffect(() => {
    (async () => {
      try { await api.guest(displayName); } catch { /* ignore */ }
    })();
  }, []);

  // 2) poll the queued list every 2s
  useEffect(() => {
    if (!code) return;
    const tick = async () => {
      const items = await api.getQueue(code);
      setQueue(items);
      // naive: pick first queued if nothing playing
      if (!nowPlaying && items.length > 0) {
        // do nothing; wait for manual "Play" or rely on advance()
      }
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => clearInterval(id);
  }, [code, nowPlaying]);

  // 3) progress bar + auto-advance
  useEffect(() => {
    if (!nowPlaying) return;
    setProgressMs(0);
    const step = 500;
    const id = setInterval(async () => {
      setProgressMs((p) => {
        const next = p + step;
        if (nowPlaying && next >= nowPlaying.duration_ms) {
          clearInterval(id);
          // call backend to advance
          api.advance(code).then(({ now_playing, queue }) => {
            setNowPlaying(now_playing);
            setQueue(queue);
            setProgressMs(0);
          });
        }
        return next;
      });
    }, step);
    return () => clearInterval(id);
  }, [nowPlaying, code]);

  const handlePlayTop = async () => {
    const { now_playing, queue } = await api.advance(code);
    setNowPlaying(now_playing);
    setQueue(queue);
    setProgressMs(0);
  };

  return (
    <div style={{ maxWidth: 800, margin: "2rem auto", padding: 16 }}>
      <h1>Democratic Tunes</h1>

      <section style={{ display: "flex", gap: 8 }}>
        <input
          placeholder="Room code (e.g. 8TVDCKVX)"
          value={code}
          onChange={(e) => setCode(e.target.value.trim().toUpperCase())}
        />
        <button onClick={handlePlayTop} disabled={!code}>Play / Advance</button>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Now Playing</h2>
        {nowPlaying ? (
          <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 8 }}>
            <div><strong>{nowPlaying.title}</strong> — {nowPlaying.artist}</div>
            <div>votes: {nowPlaying.votes} • score: {nowPlaying.score.toFixed(2)}</div>
            <progress
              max={nowPlaying.duration_ms}
              value={progressMs}
              style={{ width: "100%", height: 12, marginTop: 8 }}
            />
          </div>
        ) : (
          <div>Nothing playing.</div>
        )}
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Queue</h2>
        {queue.length === 0 && <div>Queue empty.</div>}
        {queue.map((q) => (
          <div key={q.room_track_id}
               style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
                        padding: 12, borderBottom: "1px solid #eee" }}>
            <div>
              <div><strong>{q.title}</strong> — {q.artist}</div>
              <small>votes: {q.votes} • score: {q.score.toFixed(2)}</small>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => api.vote(code, q.room_track_id, 1).then(() => api.getQueue(code).then(setQueue))}>👍</button>
              <button onClick={() => api.vote(code, q.room_track_id, -1).then(() => api.getQueue(code).then(setQueue))}>👎</button>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}