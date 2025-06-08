module.exports = {
  apps: [
    {
      name: 'fastapi-streaming',
      script: 'main.py',
      cwd: '/Users/al-husseinabdullah/aqlon',
      interpreter: 'python3',
      args: '--host 0.0.0.0 --port 8000',
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      env: {
        NODE_ENV: 'production',
        STREAMING_ENABLED: 'true',
        STREAMING_DELAY: '0.05',
        MAX_CONCURRENT_STREAMS: '100',
        LOG_LEVEL: 'info'
      },
      error_file: './logs/fastapi-error.log',
      out_file: './logs/fastapi-out.log',
      log_file: './logs/fastapi-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '500M'
    },
    {
      name: 'nestjs-backend',
      script: 'npm',
      args: 'run start:prod',
      cwd: './ai-chat-backend',
      instances: 2,
      exec_mode: 'cluster',
      watch: false,
      env: {
        NODE_ENV: 'production',
        PORT: '3001',
        FASTAPI_URL: 'http://localhost:8000',
        CORS_ORIGIN: 'http://localhost:3000,https://yourdomain.com',
        RATE_LIMIT_TTL: '60',
        RATE_LIMIT_LIMIT: '100'
      },
      error_file: './logs/nestjs-error.log',
      out_file: './logs/nestjs-out.log',
      log_file: './logs/nestjs-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '300M'
    },
    {
      name: 'nextjs-frontend',
      script: 'npm',
      args: 'run start',
      cwd: './your-nextjs-app',
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      env: {
        NODE_ENV: 'production',
        PORT: '3000',
        NEXT_PUBLIC_API_URL: 'http://localhost:3001'
      },
      error_file: './logs/nextjs-error.log',
      out_file: './logs/nextjs-out.log',
      log_file: './logs/nextjs-combined.log',
      time: true,
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '400M'
    }
  ],

  deploy: {
    production: {
      user: 'deploy',
      host: ['your-server.com'],
      ref: 'origin/main',
      repo: 'git@github.com:yourusername/ai-chat-app.git',
      path: '/var/www/ai-chat-app',
      'post-deploy': 'npm install && npm run build && pm2 reload ecosystem.config.js --env production',
      env: {
        NODE_ENV: 'production'
      }
    }
  }
};
