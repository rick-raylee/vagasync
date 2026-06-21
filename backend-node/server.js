const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient({});
const app = express();

// Anti-Hacking & Security Middlewares
app.use(helmet()); // Sets secure HTTP headers (XSS protection, no-sniff, etc)

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per `window` (here, per 15 minutes)
  message: { success: false, error: 'Too many requests from this IP, please try again after 15 minutes', code: 'RATE_LIMIT_EXCEEDED' },
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
});

app.use('/api/', apiLimiter); // Apply rate limiting to all /api/ routes

app.use(cors());
app.use(express.json());

// Toolkit Route 1: Get all jobs with match score filtering
app.get('/api/jobs', async (req, res) => {
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
app.get('/api/financial', async (req, res) => {
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
app.get('/api/stats', async (req, res) => {
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
app.post('/api/jobs', async (req, res) => {
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
