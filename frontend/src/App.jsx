import { useState, useEffect, useRef, useCallback } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const j = (path, opts) => fetch(API + path, opts).then(r => r.json())

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: 'grid' },
  { id: 'assistant', label: 'Voice assistant', icon: 'mic' },
  { id: 'inventory', label: 'Inventory', icon: 'box' },
  { id: 'history', label: 'History', icon: 'clock' },
]

function Icon({ name, size = 19 }) {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    mic: <><rect x="9" y="2" width="6" height="13" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v4m-4 0h8" /></>,
    box: <><path d="m12 3 9 5-9 5-9-5 9-5Z" /><path d="m3 8 9 5 9-5m-18 0v9l9 5 9-5V8M12 13v9" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    arrow: <><path d="M7 17 17 7M7 7h10v10" /></>,
    alert: <><path d="m12 3 10 18H2L12 3Z" /><path d="M12 9v4m0 4h.01" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    spark: <><path d="m12 3 1.9 5.8L20 11l-6.1 2.2L12 19l-1.9-5.8L4 11l6.1-2.2L12 3Z" /><path d="m19 14 1.1 2.9L23 18l-2.9 1.1L19 22l-1.1-2.9L15 18l2.9-1.1L19 14Z" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 5 5" /></>,
    chevron: <path d="m9 18 6-6-6-6" />,
  }
  return <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date)
}

function actionLabel(action) {
  if (action === 'ADD_STOCK') return 'Stock added'
  if (action === 'SELL') return 'Sale'
  return action || 'Transaction'
}

function App() {
  const [tab, setTab] = useState('dashboard')
  const [products, setProducts] = useState([])
  const [txs, setTxs] = useState([])
  const [reply, setReply] = useState(null)
  const [text, setText] = useState('')
  const [rec, setRec] = useState(false)
  const [health, setHealth] = useState(null)
  const [inventoryQuery, setInventoryQuery] = useState('')
  const [stockFilter, setStockFilter] = useState('all')
  const mr = useRef(null)

  const refresh = useCallback(async () => {
    setProducts(await j('/api/products'))
    setTxs(await j('/api/transactions'))
  }, [])
  useEffect(() => {
    j('/api/health').then(setHealth).catch(() => setHealth({ ok: false }))
    refresh().catch(() => {})
  }, [refresh])

  const speak = async (t) => {
    try {
      const r = await fetch(API + '/api/voice/speak', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: t }) })
      if (!r.ok) throw new Error()
      new Audio(URL.createObjectURL(await r.blob())).play()
    } catch {
      if ('speechSynthesis' in window) speechSynthesis.speak(new SpeechSynthesisUtterance(t))
    }
  }
  const send = async (transcript) => {
    if (!transcript.trim()) return
    const res = await j('/api/voice/command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ transcript }) })
    setReply({ ...res, transcript })
    speak(res.spoken)
    refresh()
  }
  const confirm = async (token) => {
    const res = await j('/api/voice/confirm/' + token, { method: 'POST' })
    setReply({ ...res, transcript: 'confirmed' })
    speak(res.spoken)
    refresh()
  }
  const toggleMic = async () => {
    if (rec) {
      mr.current.stop()
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const chunks = []
      const m = new MediaRecorder(stream)
      mr.current = m
      m.ondataavailable = e => chunks.push(e.data)
      m.onstop = async () => {
        setRec(false)
        stream.getTracks().forEach(t => t.stop())
        const fd = new FormData()
        fd.append('file', new Blob(chunks, { type: 'audio/webm' }), 'rec.webm')
        try {
          const r = await fetch(API + '/api/voice/transcribe', { method: 'POST', body: fd })
          let body
          try {
            body = await r.json()
          } catch {
            setReply({ status: 'rejected', message: `Backend returned an invalid response (HTTP ${r.status}).` })
            return
          }
          if (!r.ok) {
            setReply({ status: 'rejected', message: typeof body.detail === 'string' ? body.detail : `Transcription failed (HTTP ${r.status}).` })
            return
          }
          if (typeof body.transcript !== 'string' || !body.transcript.trim()) {
            setReply({ status: 'rejected', message: 'Speech recognition returned an empty transcript. Please try again.' })
            return
          }
          setText(body.transcript)
          send(body.transcript)
        } catch (error) {
          setReply({ status: 'rejected', message: `Could not reach the backend for transcription: ${error.message}` })
        }
      }
      m.start()
      setRec(true)
    } catch {
      setReply({ status: 'rejected', message: 'Microphone blocked. Allow mic access, or type the command.' })
    }
  }
  const undo = async (id) => {
    const res = await j(`/api/transactions/${id}/undo`, { method: 'POST' })
    setReply(res)
    refresh()
  }

  const low = products.filter(p => p.low)
  const visibleProducts = products.filter(p => {
    const matchesQuery = `${p.name} ${p.aliases.join(' ')}`.toLowerCase().includes(inventoryQuery.trim().toLowerCase())
    return matchesQuery && (stockFilter === 'all' || p.low)
  })
  const pageTitle = navItems.find(item => item.id === tab)?.label || 'Dashboard'
  const connectionText = !health ? 'Checking connection' : health.ok ? 'Backend connected' : 'Backend offline'

  const nav = (
    <nav className="sidebar-nav" aria-label="Main navigation">
      {navItems.map(item => (
        <button key={item.id} className={`nav-link${tab === item.id ? ' active' : ''}`} onClick={() => setTab(item.id)} aria-current={tab === item.id ? 'page' : undefined}>
          <Icon name={item.icon} />
          <span>{item.label}</span>
          {item.id === 'inventory' && low.length > 0 && <span className="nav-count">{low.length}</span>}
        </button>
      ))}
    </nav>
  )

  const activityRows = (rows, compact = false) => rows.length ? rows.map(t => (
    <tr key={t.id}>
      <td><span className={`activity-type ${t.status === 'undone' ? 'muted' : t.action === 'SELL' ? 'sale' : 'added'}`}>{actionLabel(t.action)}</span></td>
      <td className="product-cell">{t.product}</td>
      <td className={`change-cell ${t.change < 0 ? 'negative' : 'positive'}`}>{t.change > 0 ? '+' : ''}{t.change}</td>
      {!compact && <td>{t.after}</td>}
      <td><span className={`status-pill ${t.status === 'undone' ? 'status-undone' : 'status-applied'}`}>{t.status === 'undone' ? 'Undone' : 'Applied'}</span></td>
      {!compact && <td className="date-cell">{formatDate(t.at)}</td>}
      <td>{t.undoable && <button className="text-button" onClick={() => undo(t.id)}>Undo</button>}</td>
    </tr>
  )) : <tr><td className="empty-cell" colSpan={compact ? 5 : 7}>No transactions yet. Your stock activity will appear here.</td></tr>

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={e => { e.preventDefault(); setTab('dashboard') }} aria-label="KiranaVoice dashboard">
          <span className="brand-mark"><Icon name="spark" size={21} /></span>
          <span className="brand-copy"><strong>KiranaVoice</strong><small>STORE WORKSPACE</small></span>
        </a>
        <div className="sidebar-label">WORKSPACE</div>
        {nav}
        <div className="sidebar-spacer" />
        <div className="sidebar-help">
          <span className={`connection-dot ${health?.ok ? 'online' : health ? 'offline' : ''}`} />
          <div><strong>{connectionText}</strong><span>{health?.ok && !health.gnani_configured ? 'Text mode enabled' : 'Inventory assistant'}</span></div>
        </div>
        <div className="sidebar-foot">Built for your everyday business</div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="mobile-brand"><span className="brand-mark"><Icon name="spark" size={19} /></span><strong>KiranaVoice</strong></div>
          <div className="breadcrumb"><span>Workspace</span><Icon name="chevron" size={15} /><strong>{pageTitle}</strong></div>
          <div className="topbar-status"><span className={`connection-dot ${health?.ok ? 'online' : health ? 'offline' : ''}`} /><span>{connectionText}</span></div>
        </header>

        <main className="page-content">
          {tab === 'dashboard' && <>
            <section className="page-heading dashboard-heading">
              <div><div className="eyebrow">YOUR STORE AT A GLANCE</div><h1>Good to see you.</h1><p>Here’s what’s happening with your inventory today.</p></div>
              <button className="primary-button heading-action" onClick={() => setTab('assistant')}><Icon name="mic" size={17} /> Talk to your store</button>
            </section>
            <section className="stats-grid" aria-label="Store overview">
              <article className="stat-card"><div className="stat-top"><span className="stat-icon green"><Icon name="box" /></span><span className="stat-caption">IN YOUR CATALOG</span></div><div className="stat-value">{products.length}</div><div className="stat-label">Products tracked</div></article>
              <article className="stat-card"><div className="stat-top"><span className="stat-icon amber"><Icon name="alert" /></span><span className="stat-caption">NEEDS ATTENTION</span></div><div className="stat-value">{low.length}</div><div className="stat-label">Low-stock items</div></article>
              <article className="stat-card"><div className="stat-top"><span className="stat-icon blue"><Icon name="clock" /></span><span className="stat-caption">LATEST ACTIVITY</span></div><div className="stat-value">{txs.length}</div><div className="stat-label">Recent transactions loaded</div></article>
            </section>

            <section className="dashboard-grid">
              <article className="panel assistant-panel">
                <div className="assistant-panel-head"><div className="assistant-mark"><Icon name="spark" size={21} /></div><div><div className="eyebrow">YOUR AI STORE ASSISTANT</div><h2>Run your shop by voice or text</h2></div></div>
                <p className="panel-description">Add stock, record a sale, or ask what’s running low—in the words you’d use every day.</p>
                <form className="command-form" onSubmit={e => { e.preventDefault(); send(text); setText('') }}>
                  <label className="sr-only" htmlFor="dashboard-command">Store command</label>
                  <input id="dashboard-command" value={text} onChange={e => setText(e.target.value)} placeholder="Try “chawal kitna hai?”" />
                  <button className="primary-button command-submit" type="submit"><span>Send command</span><Icon name="arrow" size={17} /></button>
                </form>
                <button className={`mic-control${rec ? ' recording' : ''}`} onClick={toggleMic} aria-label={rec ? 'Stop recording' : 'Start voice recording'}>
                  <Icon name="mic" size={18} />
                  <span>{rec ? 'Listening — tap to stop' : 'Tap to speak'}</span>
                  <span className="mic-indicator" />
                </button>
                {reply && <div className={`reply ${reply.status}`} role="status">
                  {reply.transcript && <div className="reply-transcript">“{reply.transcript}”</div>}
                  <div>{reply.message}</div>
                  {reply.status === 'needs_confirmation' && <button className="primary-button confirm-button" onClick={() => confirm(reply.token)}><Icon name="check" size={17} /> Yes, confirm</button>}
                </div>}
                <div className="assistant-footnote"><span className="connection-dot online" />{health?.ok && !health.gnani_configured ? 'Text commands ready · voice services need setup' : 'Connected to your live inventory'}</div>
              </article>

              <article className="panel low-stock-panel">
                <div className="section-heading"><div><div className="eyebrow">KEEP AN EYE ON</div><h2>Low stock</h2></div><span className={`section-count${low.length ? ' warning' : ''}`}>{low.length}</span></div>
                {low.length ? <div className="low-stock-list">{low.slice(0, 5).map(p => (
                  <div className="low-stock-item" key={p.id}><span className="stock-alert-icon"><Icon name="alert" size={16} /></span><div className="low-stock-info"><strong>{p.name}</strong><span>Below your stock threshold</span></div><div className="stock-quantity"><strong>{p.quantity}</strong><span>{p.unit} left</span></div></div>
                ))}</div> : <div className="empty-state"><span className="success-icon"><Icon name="check" /></span><strong>All stocked up</strong><span>No low-stock items right now.</span></div>}
                {low.length > 5 && <button className="section-link" onClick={() => { setTab('inventory'); setStockFilter('low') }}>View all {low.length} items <Icon name="arrow" size={15} /></button>}
              </article>
            </section>

            <section className="panel activity-panel">
              <div className="section-heading"><div><div className="eyebrow">WHAT’S BEEN HAPPENING</div><h2>Recent activity</h2></div><button className="section-link" onClick={() => setTab('history')}>View history <Icon name="arrow" size={15} /></button></div>
              <div className="table-scroll"><table className="activity-table"><thead><tr><th>ACTIVITY</th><th>PRODUCT</th><th>CHANGE</th><th>STATUS</th><th></th></tr></thead><tbody>{activityRows(txs.slice(0, 5), true)}</tbody></table></div>
            </section>
          </>}

          {tab === 'assistant' && <>
            <section className="page-heading"><div><div className="eyebrow">KIRANAVOICE ASSISTANT</div><h1>Your shop, in your words.</h1><p>Tell your assistant what you need—your inventory stays up to date.</p></div><span className={`mode-badge ${health?.ok ? 'connected' : ''}`}><span className={`connection-dot ${health?.ok ? 'online' : ''}`} />{health?.ok && !health.gnani_configured ? 'Text mode' : connectionText}</span></section>
            <section className="assistant-workspace">
              <div className="assistant-orbit"><div className="orbit-ring orbit-ring-one" /><div className="orbit-ring orbit-ring-two" /><button className={`large-mic${rec ? ' recording' : ''}`} onClick={toggleMic} aria-label={rec ? 'Stop recording' : 'Start voice recording'}><Icon name="mic" size={31} /></button></div>
              <div className="assistant-prompt"><h2>{rec ? 'I’m listening…' : 'How can I help your store?'}</h2><p>{rec ? 'Speak naturally, then tap the button to finish.' : 'Tap the microphone to speak, or type a command below.'}</p></div>
              <div className="voice-status"><span className={`connection-dot ${rec ? 'recording-dot' : health?.ok ? 'online' : ''}`} />{rec ? 'Recording in progress' : health?.ok && !health.gnani_configured ? 'Ready for text commands · connect Gnani for speech' : 'Ready when you are'}</div>
              <form className="assistant-input" onSubmit={e => { e.preventDefault(); send(text); setText('') }}>
                <label className="sr-only" htmlFor="assistant-command">Type a command for your store</label>
                <input id="assistant-command" value={text} onChange={e => setText(e.target.value)} placeholder="e.g. Maggi ke 10 packet add karo" />
                <button className="primary-button" type="submit">Send command <Icon name="arrow" size={17} /></button>
              </form>
              <div className="suggestion-row"><span>Try asking</span><button onClick={() => setText('low stock batao')}>What’s low on stock?</button><button onClick={() => setText('chawal kitna hai')}>How much rice is left?</button></div>
              {reply && <div className={`reply assistant-reply ${reply.status}`} role="status">
                {reply.transcript && <div className="reply-transcript">“{reply.transcript}”</div>}
                <div>{reply.message}</div>
                {reply.status === 'needs_confirmation' && <button className="primary-button confirm-button" onClick={() => confirm(reply.token)}><Icon name="check" size={17} /> Yes, confirm</button>}
              </div>}
            </section>
            <div className="voice-note"><Icon name="spark" size={18} /><span>Your commands update the same live inventory your team sees.</span></div>
          </>}

          {tab === 'inventory' && <>
            <section className="page-heading"><div><div className="eyebrow">YOUR PRODUCTS</div><h1>Inventory</h1><p>Keep track of what’s on your shelves.</p></div><div className="inventory-summary"><strong>{products.length}</strong><span>products</span><i /><strong>{low.length}</strong><span>low stock</span></div></section>
            <section className="panel inventory-panel">
              <div className="inventory-toolbar"><div><h2>All products</h2><p>{visibleProducts.length} of {products.length} products</p></div><div className="inventory-controls">
                <label className="search-field"><Icon name="search" size={17} /><span className="sr-only">Search products</span><input value={inventoryQuery} onChange={e => setInventoryQuery(e.target.value)} placeholder="Search products or aliases" /></label>
                <div className="filter-group" aria-label="Filter inventory">{[{ id: 'all', label: 'All stock' }, { id: 'low', label: 'Low stock' }].map(filter => <button key={filter.id} className={stockFilter === filter.id ? 'selected' : ''} onClick={() => setStockFilter(filter.id)} aria-pressed={stockFilter === filter.id}>{filter.label}</button>)}</div>
              </div></div>
              <div className="table-scroll"><table className="inventory-table"><thead><tr><th>PRODUCT</th><th>STOCK LEVEL</th><th>PRICE</th><th>ALSO KNOWN AS</th><th>STATUS</th></tr></thead><tbody>
                {visibleProducts.length ? visibleProducts.map(p => <tr key={p.id}>
                  <td><div className="product-name"><span className="product-avatar">{p.name.trim().charAt(0).toUpperCase()}</span><strong>{p.name}</strong></div></td>
                  <td><span className={`stock-value${p.low ? ' low' : ''}`}>{p.quantity} <span>{p.unit}</span></span></td>
                  <td className="price-cell">₹{p.price}</td>
                  <td><div className="alias-list">{p.aliases.length ? p.aliases.map(alias => <span className="alias-chip" key={alias}>{alias}</span>) : <span className="muted-copy">—</span>}</div></td>
                  <td><span className={`stock-status ${p.low ? 'needs-stock' : 'in-stock'}`}><span />{p.low ? 'Low stock' : 'In stock'}</span></td>
                </tr>) : <tr><td className="empty-cell" colSpan="5">No products match your search.</td></tr>}
              </tbody></table></div>
              <div className="inventory-footnote"><Icon name="alert" size={15} /><span>Stock alerts are based on each product’s configured threshold.</span></div>
            </section>
          </>}

          {tab === 'history' && <>
            <section className="page-heading"><div><div className="eyebrow">YOUR STORE’S ACTIVITY</div><h1>Transaction history</h1><p>A clear record of stock changes and sales.</p></div><span className="mode-badge"><Icon name="clock" size={16} /> Latest {txs.length} records</span></section>
            <section className="panel history-panel">
              <div className="history-summary"><div className="stat-icon blue"><Icon name="clock" /></div><div><strong>{txs.length}</strong><span>Transactions loaded</span></div><p>Showing the latest records available from your store.</p></div>
              <div className="table-scroll"><table className="history-table"><thead><tr><th>ACTIVITY</th><th>PRODUCT</th><th>CHANGE</th><th>STOCK AFTER</th><th>STATUS</th><th>DATE &amp; TIME</th><th></th></tr></thead><tbody>{activityRows(txs)}</tbody></table></div>
              <div className="inventory-footnote"><Icon name="check" size={15} /><span>Applied stock changes can be undone where available.</span></div>
            </section>
          </>}
        </main>
      </div>
      <div className="mobile-navigation">{nav}</div>
    </div>
  )
}

export default App
