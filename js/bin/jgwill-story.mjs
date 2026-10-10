#!/usr/bin/env node
// jgwill-story: a draft service over @miadi/ncp-story-studio.
//
// The studio is a library and ships no server. This file supplies one: it opens
// a JSON story store, seeds it with one bundled story when the store directory is
// empty, and serves the stories as JSON and each narrative's beat line as SVG.
// Read-only in this draft. See README.md, "Story studio bridge".

import { createServer } from 'node:http'
import { readdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { parseArgs } from 'node:util'
import { JsonStoryStore, assertProjectId } from '@miadi/ncp-story-studio/store/json'
import { FIXTURES, fixtureProject } from '@miadi/ncp-story-studio/fixtures'
import { layoutNarrative, layoutToSvg } from '@miadi/ncp-story-studio/graph'

const DEFAULT_SEED = 'echoes-of-the-past'
const USAGE = `Usage:
  jgwill-story serve [--port 3345] [--host 127.0.0.1] [--store ./story-data] [--seed ${DEFAULT_SEED}]
  jgwill-story fixtures

Endpoints (GET):
  /health
  /api/ncp/projects
  /api/ncp/projects/:id
  /api/ncp/projects/:id/line.svg[?narrative=0]
`

function sendJson(res, status, body) {
  if (res.headersSent) return res.end()
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(body, null, 2))
}

// True when the store directory does not exist yet or holds no entries at all.
// A directory with entries that `list()` skips is left alone, so nothing is overwritten.
async function isEmptyDirectory(root) {
  try {
    return (await readdir(root)).length === 0
  } catch (error) {
    if (error.code === 'ENOENT') return true
    throw error
  }
}

async function seedIfEmpty(store, fixtureId) {
  if (!(await isEmptyDirectory(store.location))) return null
  const project = await fixtureProject(fixtureId)
  // Fixtures are read-only in their own store. The seeded copy must be writable.
  await store.save({ ...project, read_only: false })
  return fixtureId
}

async function handle(store, req, res) {
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'GET only: this draft is read-only' })

  const { pathname, searchParams } = new URL(req.url, 'http://localhost')

  if (pathname === '/health') {
    const projects = await store.list()
    return sendJson(res, 200, { ok: true, projects: projects.length })
  }

  if (pathname === '/api/ncp/projects') {
    return sendJson(res, 200, { projects: await store.list() })
  }

  const match = pathname.match(/^\/api\/ncp\/projects\/([^/]+)(\/line\.svg)?$/)
  if (!match) return sendJson(res, 404, { error: 'not found' })

  let projectId
  try {
    projectId = decodeURIComponent(match[1])
    assertProjectId(projectId)
  } catch (error) {
    return sendJson(res, 400, { error: error.message })
  }

  const project = await store.get(projectId)
  if (!project) return sendJson(res, 404, { error: `no project ${projectId}` })
  if (!match[2]) return sendJson(res, 200, project)

  const index = Number(searchParams.get('narrative') ?? 0)
  const narrative = project.document.story.narratives[index]
  if (!narrative) return sendJson(res, 404, { error: `no narrative ${index}` })

  // Lay out before writing the status line, so a malformed story becomes a 500 and not a half-sent response.
  const svg = layoutToSvg(layoutNarrative(narrative))
  res.writeHead(200, { 'content-type': 'image/svg+xml; charset=utf-8' })
  res.end(svg)
}

async function serve(values) {
  const store = new JsonStoryStore({ root: resolve(values.store) })
  const seeded = await seedIfEmpty(store, values.seed)

  const port = Number(values.port)
  const server = createServer((req, res) => {
    handle(store, req, res).catch((error) => sendJson(res, 500, { error: error.message }))
  })

  server.once('error', (error) => {
    console.error(`jgwill-story could not listen on ${values.host}:${port}: ${error.message}`)
    process.exitCode = 1
  })

  let stopping = false
  const stop = () => {
    if (stopping) process.exit(130)
    stopping = true
    server.close(() => process.exit(0))
    server.closeAllConnections()
  }
  process.on('SIGINT', stop)
  process.on('SIGTERM', stop)

  server.listen(port, values.host, () => {
    console.log(`jgwill-story listening on http://${values.host}:${port}`)
    console.log(`store: ${store.location}${seeded ? ` (seeded with ${seeded})` : ''}`)
  })
}

function listFixtures() {
  for (const entry of FIXTURES) console.log(`${entry.id}\t${entry.family}\t${entry.title}`)
}

async function main(argv) {
  const { values, positionals } = parseArgs({
    args: argv,
    allowPositionals: true,
    options: {
      port: { type: 'string', default: '3345' },
      host: { type: 'string', default: '127.0.0.1' },
      store: { type: 'string', default: './story-data' },
      seed: { type: 'string', default: DEFAULT_SEED },
      help: { type: 'boolean', short: 'h', default: false },
    },
  })

  if (values.help) return console.log(USAGE)

  const command = positionals[0] ?? 'serve'
  if (command === 'serve') {
    const port = Number(values.port)
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      throw new Error(`--port must be a whole number from 1 to 65535, got "${values.port}"`)
    }
    return serve(values)
  }
  if (command === 'fixtures') return listFixtures()

  console.error(USAGE)
  process.exitCode = 2
}

main(process.argv.slice(2)).catch((error) => {
  console.error(`jgwill-story: ${error.message}`)
  process.exitCode = 1
})
