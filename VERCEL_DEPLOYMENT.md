# Vercel Deployment Guide

## Important Notes

⚠️ **SQLite Limitation on Vercel**: 
- Vercel's filesystem is **read-only** except for `/tmp`
- SQLite databases stored in `/tmp` will **NOT persist** between deployments
- Data will be lost when the serverless function restarts
- **Recommendation**: Use Vercel Postgres, PostgreSQL, or another cloud database for production

## Current Setup

The app is configured to use `/tmp/travel.db` on Vercel, which means:
- ✅ The app will run without errors
- ❌ Data will be reset on each cold start
- ❌ No persistent storage

## Environment Variables

Set these in your Vercel project settings:

1. **SECRET_KEY**: A secure random string for Flask sessions
   - Generate one: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Add in Vercel Dashboard → Settings → Environment Variables

2. **DB_PATH**: (Optional) Database path - defaults to `/tmp/travel.db` on Vercel

## Deployment Steps

1. Push your code to GitHub
2. Import the repository in Vercel
3. Set environment variables in Vercel dashboard
4. Deploy

## Recommended: Migrate to Vercel Postgres

For production, consider migrating to Vercel Postgres:

1. Add Vercel Postgres in your Vercel project
2. Update `app.py` to use PostgreSQL instead of SQLite
3. Update connection string to use environment variables from Vercel

## Troubleshooting

If you see "Internal Server Error":
1. Check Vercel function logs
2. Verify environment variables are set
3. Check that all dependencies are in `requirements.txt`
4. Ensure `api/index.py` is properly configured

