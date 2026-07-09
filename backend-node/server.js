const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient({});
const app = express();

// Anti-Hacking & Security Middlewares
app.use(helmet()); // Sets secure HTTP headers (XSS protection, no-sniff, etc)

// ─── Rate limiting ────────────────────────────────────────────────────────────
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  message: { success: false, error: 'Too many requests from this IP, please try again after 15 minutes', code: 'RATE_LIMIT_EXCEEDED' },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', apiLimiter);

// ─── CORS — Origens autorizadas (anti-leak) ───────────────────────────────────
const ALLOWED_ORIGINS = [
  'https://vagasync.com.br',
  'https://www.vagasync.com.br',
  'https://ceo.vagasync.com.br',
  'http://localhost:5173',
  'http://localhost:3000',
  'http://localhost:8080',
  'http://127.0.0.1:5173',
];

app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (mobile apps, Postman, curl) only in dev
    if (!origin) {
      if (process.env.NODE_ENV === 'production') {
        return callback(new Error('CORS: origem não permitida'), false);
      }
      return callback(null, true);
    }
    if (ALLOWED_ORIGINS.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error(`CORS: origem bloqueada — ${origin}`), false);
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Authorization', 'Content-Type', 'Accept'],
}));

app.use(express.json({ limit: '1mb' })); // Limita payload JSON a 1MB

// JWT verification utility matching the Python backend
const crypto = require('crypto');
const JWT_SECRET = "vagasync_super_secret_jwt_key_2026";

function base64UrlDecode(str) {
  let base64 = str.replace(/-/g, '+').replace(/_/g, '/');
  while (base64.length % 4) {
    base64 += '=';
  }
  return Buffer.from(base64, 'base64').toString('utf8');
}

function verifyJWT(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const [headerB64, payloadB64, sigB64] = parts;

    const signatureBase = `${headerB64}.${payloadB64}`;
    const hmac = crypto.createHmac('sha256', JWT_SECRET);
    hmac.update(signatureBase);
    const expectedSig = hmac.digest('base64url');

    if (sigB64 !== expectedSig) return null;

    const payload = JSON.parse(base64UrlDecode(payloadB64));

    if (payload.exp < Date.now() / 1000) return null;

    return payload;
  } catch (error) {
    return null;
  }
}

// Authentication middleware to prevent data leaks
const authMiddleware = (req, res, next) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ success: false, error: 'Unauthorized: Missing or malformed token' });
  }

  const token = authHeader.split(' ')[1];
  const payload = verifyJWT(token);

  if (!payload || payload.role !== 'admin') {
    return res.status(403).json({ success: false, error: 'Forbidden: Invalid token or insufficient permissions' });
  }

  req.user = payload;
  next();
};

// Toolkit Route 1: Get all jobs with match score filtering
app.get('/api/jobs', authMiddleware, async (req, res) => {
  try {
    const { minMatch } = req.query;
    
    let where = {};
    if (minMatch) {
      where.match_score = {
        gte: parseInt(minMatch)
      };
    }
    
    const jobs = await prisma.jobs.findMany({
      where,
      orderBy: { created_at: 'desc' }
    });
    
    res.json({ success: true, data: jobs });
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: 'Database error' });
  }
});

// Toolkit Route 2: Get financial transactions
app.get('/api/financial', authMiddleware, async (req, res) => {
  try {
    const transactions = await prisma.financial_transactions.findMany({
      orderBy: { created_at: 'desc' },
      take: 50
    });
    
    res.json({ success: true, data: transactions });
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: 'Database error' });
  }
});

// Toolkit Route 3: System Stats
app.get('/api/stats', authMiddleware, async (req, res) => {
  try {
    const totalJobs = await prisma.jobs.count();
    const activeTransactions = await prisma.financial_transactions.count({
      where: { status: 'paid' }
    });
    const recentLogs = await prisma.audit_logs.findMany({
      orderBy: { timestamp: 'desc' },
      take: 10
    });
    
    res.json({ 
      success: true, 
      data: {
        totalJobs,
        activeTransactions,
        recentLogs
      }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: 'Database error' });
  }
});

// Toolkit Route 4: Add new job programmatically
app.post('/api/jobs', authMiddleware, async (req, res) => {
  try {
    const { title, company, location, link, source, description } = req.body;
    
    const newJob = await prisma.jobs.create({
      data: {
        title,
        company,
        location,
        link,
        source: source || 'api',
        description,
        status: 'found',
        match_score: Math.floor(Math.random() * 30) + 70 // Mocking score for testing
      }
    });
    
    res.status(201).json({ success: true, data: newJob });
  } catch (error) {
    console.error(error);
    res.status(500).json({ success: false, error: 'Failed to create job' });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`🚀 VagaSync API Server with Prisma running on http://localhost:${PORT}`);
});
