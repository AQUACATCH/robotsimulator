async function call(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const err = new Error(data?.error ?? `${method} ${path} → ${res.status}`)
    err.status = res.status
    throw err
  }
  return data
}

function normalize(state) {
  const p = state.program ?? {}
  return {
    ...state,
    ast: p.ast ?? [],
    source: p.source ?? '',
    lineMap: p.line_map ?? {},
  }
}

export async function getState() {
  return normalize(await call('GET', '/api/state'))
}

export async function putProgram(ast) {
  return normalize(await call('PUT', '/api/program', ast))
}

export async function startRun(mode) {
  return normalize(await call('POST', '/api/run/start', { mode }))
}

export async function runStep() {
  return normalize(await call('POST', '/api/run/step'))
}

export async function stopRun() {
  return normalize(await call('POST', '/api/run/stop'))
}

export async function manual(action, value = 1) {
  return normalize(await call('POST', '/api/manual', { action, value }))
}

export async function resetWorld() {
  return normalize(await call('POST', '/api/reset'))
}

export async function getLog() {
  return call('GET', '/api/log')
}
