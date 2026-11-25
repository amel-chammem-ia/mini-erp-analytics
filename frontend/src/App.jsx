import { useEffect, useState } from 'react'

const LABELS = {
  ok: { text: 'Connectée', className: 'ok' },
  indisponible: { text: 'Indisponible', className: 'ko' },
}

function StatusCard({ title, value }) {
  const label = LABELS[value] ?? { text: 'Vérification…', className: 'wait' }
  return (
    <div className={`card ${label.className}`}>
      <span className="dot" />
      <div>
        <p className="card-title">{title}</p>
        <p className="card-value">{title === 'API' && value === 'ok' ? 'En ligne' : label.text}</p>
      </div>
    </div>
  )
}

export default function App() {
  const [health, setHealth] = useState({ api: null, database: null })
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setError(true))
  }, [])

  return (
    <main>
      <h1>Mini-ERP Analytics</h1>
      <p className="subtitle">Clients, produits, ventes, stock et tableaux de bord</p>
      {error ? (
        <p className="error">L'API ne répond pas. Vérifiez que « docker compose up » est lancé.</p>
      ) : (
        <div className="cards">
          <StatusCard title="API" value={health.api} />
          <StatusCard title="Base de données" value={health.database} />
        </div>
      )}
    </main>
  )
}
