# Shared Selection

These answers are set once and shared by both roles (Business and Technical).
Fill in each `[Answer]:` tag, save the file, then reply in chat with: **ready**

---

### S1: Which language should I use for questions and final documents?

Control files (state, audit) stay in English either way.

a) English
b) Spanish / Español
c) Other (write it after [Answer]:)

[Answer]:b

---

### S2: Which best describes this project?

a) **Brand-new project** — we are building something from scratch. There is no
   existing code, and no existing system we must integrate with or preserve.

b) **New feature on an existing product** — there is already a system in
   production (or built), and we are adding a capability to it. Existing code,
   schemas, APIs, or users must continue to work.

c) **Migration / modernisation of an existing system** — there is a system
   in place and we are rebuilding, replatforming, or replacing part of it.
   Some existing contracts or data will carry over.

x) Other — describe after [Answer]:
   (example: "mostly brand-new but we must connect to one existing service
   for authentication")

[Answer]:C

---

### S3: How can I learn about your existing system? (answer only if S2 = b or c)

a) The existing code is in this workspace or in a repository I can read.
   Tell me the path and I'll explore it as needed.

b) No code access, but I have documents (architecture notes, ADRs, wiki pages,
   screenshots). I'll share paths or links when the interview asks.

c) Neither. I'll describe the existing system in my own words when asked.

x) Other

[Answer]: El repositorio GitHub del sistema existente ya está clonado localmente.

Ruta del proyecto:
D:\usuarios\OATI\migracion-recibos-ws

Ruta del código fuente:
D:\usuarios\OATI\migracion-recibos-ws\codigo-fuente

Repositorio:
https://github.com/braianestiven/recibos.git

La carpeta principal del código es codigo-fuente/weboffice.

---

### S4: Who is filling in the interviews? (mode)

a) **Business only** — I'll produce the Vision Document (the "what and why").
b) **Technical only** — I'll produce the Technical Environment Document (tools and constraints).
c) **Both, sequential** — one person does Business first, then Technical.
d) **Both, parallel** — a PM and a tech lead work at the same time in separate sessions.
   Each writes only its own state file; the open-questions step runs once both finish.

**Recommendation:** c if you are covering both roles yourself; d if two different
people own the vision and the technical constraints.

[Answer]:d

---

### S5: How deep should the interview go? (depth)

a) **Quick pass** (~10 min per role) — only the core questions.
b) **Full interview** (~25 min per role) — every question.

**Recommendation:** b for a migration, because current-state and
"what must not change" questions matter more there.

[Answer]: b

---

### S6: How should I present the questions? (interaction)

a) **Batch** — I write 5–7 questions into a markdown file, you fill in the
   `[Answer]:` tags and reply `ready`. Fewer round-trips; edit at your own pace.
b) **Conversational** — I ask in chat, one question (or 2–3) at a time,
   and you answer inline. No file editing.

[Answer]: b, but you need to write into a md all the questions and answers for context

---

When you're done, reply with a single word: **ready**
