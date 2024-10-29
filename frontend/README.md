This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Configuring a supervisord service

```txt
[program:fastapi]
command="source .venv/bin/activate && python main.py"
directory=/path/to/backend
autostart=true
autorestart=true
startsecs=0
stdout_logfile=/var/log/fastapi.out.log
stderr_logfile=/var/log/fastapi.err.log

[program:nextjs]
command="npm run build && npm run start"
directory=/path/to/frontend
autostart=true
autorestart=true
startsecs=10
stdout_logfile=/var/log/nextjs.out.log
stderr_logfile=/var/log/nextjs.err.log

[group:urlwiz]
programs=fastapi,nextjs
```
