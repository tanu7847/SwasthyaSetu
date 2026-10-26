import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
function App() {
  const [email, setEmail] = useState('operator@example.test');
  const [password, setPassword] = useState('OperatorDemo123!');
  const [token, setToken] = useState('');
  const [message, setMessage] = useState('Sign in with a seeded demo account.');
  const [summary, setSummary] = useState(null);
  const [requests, setRequests] = useState([]);
  async function call(path, opts={}) {
    const res = await fetch(API + path, {...opts, headers: {'Content-Type':'application/json', ...(token ? {Authorization:`Bearer ${token}`} : {}), ...(opts.headers||{})}});
    const data = await res.json().catch(()=>({detail:'Unexpected response'}));
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  }
  async function login(e) {
    e.preventDefault();
    try {
      const data = await call('/auth/login', {method:'POST', body:JSON.stringify({email,password})});
      setToken(data.access_token); setMessage(`Signed in as ${data.role}.`);
      const [s, r] = await Promise.all([
        fetch(API+'/dashboard/summary',{headers:{Authorization:`Bearer ${data.access_token}`}}).then(x=>x.json()),
        fetch(API+'/emergency-requests',{headers:{Authorization:`Bearer ${data.access_token}`}}).then(x=>x.json())
      ]);
      setSummary(s); setRequests(Array.isArray(r)?r:[]);
    } catch(err) { setMessage(err.message); }
  }
  return <main>
    <header><div className="logo">✚ SwasthyaSetu</div><span>Staff coordination dashboard · Prototype</span></header>
    <section className="hero"><p className="eyebrow">BRIDGING CARE, EMPOWERING HEALTH</p><h1>Healthcare coordination</h1><p>Review system status and simulated emergency requests. No ambulance dispatch integration is configured.</p></section>
    <section className="panel">
      <h2>Staff sign in</h2><form onSubmit={login}>
        <label>Email<input value={email} onChange={e=>setEmail(e.target.value)} /></label>
        <label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} /></label>
        <button>Sign in</button>
      </form><p className="message">{message}</p>
    </section>
    <section className="cards">
      {Object.entries(summary || {API:'Sign in', MongoDB:'Required', Patients:'—', 'Simulated requests':'—'}).map(([k,v])=><div className="card" key={k}><span>{k.replaceAll('_',' ')}</span><strong>{v}</strong></div>)}
    </section>
    <section className="panel"><h2>Emergency requests</h2><p className="warning">SIMULATION ONLY — this dashboard does not contact emergency services.</p>
      {requests.length ? <div className="table-wrap"><table><thead><tr><th>Request ID</th><th>Status</th><th>Symptoms</th><th>Location</th><th>Created</th></tr></thead><tbody>{requests.map(r=><tr key={r.request_id}><td>{r.request_id}</td><td>{r.status}</td><td>{r.symptoms}</td><td>{r.location_text}</td><td>{r.created_at}</td></tr>)}</tbody></table></div>:<p>No requests loaded. Sign in with operator/admin to view demo records.</p>}
    </section>
    <footer>Development prototype · Use synthetic patient data only · AI drafts require clinician review.</footer>
  </main>;
}
createRoot(document.getElementById('root')).render(<App/>);
