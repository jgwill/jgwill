# JGWILL

## TODO...

>🌱 I’m currently learning this whole agentic paradigm....

Soon, 🧠 Mia might have something to tell you....

## Story studio bridge (draft)

**Goal:** bring the story logic of [`storytelling`](https://www.npmjs.com/package/storytelling)
(the JavaScript version, from `jgwill/storytelling`) into [`@miadi/ncp-story-studio`](https://www.npmjs.com/package/@miadi/ncp-story-studio),
so a story storytelling produces can be read, laid out as a line of beats, and served by the studio.
The bridge maps storytelling's beats and NCP state onto NCP storypoints, storybeats and perspectives,
so the output validates with the studio's `validateNcpDocument`.

The draft is not the bridge yet. `jgwill-story` is a read-only service over the studio. It seeds an
empty store with one bundled story and serves it.

Without installing anything, run the published command with `npx`:

```bash
npx -p jgwill jgwill-story fixtures                    # list the bundled stories
npx -p jgwill jgwill-story serve --seed echoes-of-the-past --port 3345
curl http://127.0.0.1:3345/health
curl http://127.0.0.1:3345/api/ncp/projects/echoes-of-the-past
curl http://127.0.0.1:3345/api/ncp/projects/echoes-of-the-past/line.svg
```

From a checkout of this package, `node bin/jgwill-story.mjs` takes the same arguments.

Options for `serve`: `--port` (default `3345`, 1 to 65535), `--store` (default `./story-data`), `--host`
(default `127.0.0.1`), `--seed` (default `echoes-of-the-past`). The seed runs only when the store
directory is missing or empty.

