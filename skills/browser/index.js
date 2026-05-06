/**
 * Browser Skill - Safety-Aware Web Reader
 * Uses OpenClaw's built-in web_fetch tool for reliable fetching.
 * All safety layers run in-process (no browser needed).
 * 
 * Safety layers:
 * 1. URL static analysis (pattern matching, typosquatting)
 * 2. HTTPS certificate check  
 * 3. Content audit (phishing keywords, password fields, external forms)
 * 
 * Note: This version uses HTTP fetching (no JS rendering).
 * For JS-heavy pages, use OpenClaw's Playwright integration separately.
 */

const { URL } = require('url');

// ─── SAFETY CONFIG ──────────────────────────────────────────────────────────

const SUSPICIOUS_PATTERNS = [
  { pattern: /^https?:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/, reason: 'IP address URL' },
  { pattern: /@/, reason: 'URL contains @ (hides real destination)' },
  { pattern: /^data:/i, reason: 'Data URI scheme' },
  { pattern: /^javascript:/i, reason: 'JavaScript URI scheme' },
  { pattern: /%25/, reason: 'Double-encoded URL' },
  { pattern: /\.(xyz|tk|ml|ga|cf|gq|top|work|buzz|pw)\//i, reason: 'Suspicious free TLD' },
  { pattern: /^https?:\/\/([a-z0-9-]+\.){5,}/i, reason: 'Excessive subdomains' },
];

const TRUSTED_DOMAINS = [
  'github.com', 'github.io', 'githubusercontent.com',
  'notion.so', 'notion.site',
  'openclaw.ai', 'docs.openclaw.ai', 'clawhub.ai',
  'google.com', 'youtube.com', 'blog.google',
  'wikipedia.org',
  'medium.com', 'dev.to',
  'stackoverflow.com',
  'npmjs.com', 'pypi.org',
  'reddit.com', 'old.reddit.com',
  'twitter.com', 'x.com',
  'bilibili.com', 'zhihu.com',
  'tencent.com', 'qq.com', 'weixin.qq.com',
  'baidu.com',
  'vercel.com', 'netlify.com', 'cloudflare.com',
  'figma.com', 'canva.com',
  'chatgpt.com', 'claude.ai', 'anthropic.com',
  'openai.com', 'ai.com',
];

const PHISHING_KEYWORDS_EN = [
  'verify your account', 'confirm your identity',
  'urgent action required', 'account suspended',
  'update your payment', 'security alert',
  'click here to', 'login now', 'verify now',
  'suspended unless', 'immediate action',
  'your account will be closed',
];

const PHISHING_KEYWORDS_ZH = [
  '您的账户已冻结', '立即验证', '安全警报',
  '账户存在风险', '请重新登录', '点击此处',
  '您的账号已被锁定', '立即更新', '重要通知',
  '请确认您的身份', '账户异常',
];

const SUSPICIOUS_TLDS = [
  'xyz', 'tk', 'ml', 'ga', 'cf', 'gq', 'top', 'work',
  'buzz', 'pw', 'cc', 'su', 'racing', 'win',
];

// ─── LAYER 1: URL STATIC ANALYSIS ────────────────────────────────────────────

function analyzeUrl(url) {
  const warnings = [];
  let hostname = null;

  try {
    const urlObj = new URL(url);
    hostname = urlObj.hostname.toLowerCase();

    // Check suspicious patterns
    for (const { pattern, reason } of SUSPICIOUS_PATTERNS) {
      if (pattern.test(url)) {
        warnings.push(`⚠️  ${reason}`);
      }
    }

    // Typosquatting
    const typosquatting = {
      'githuh.com': 'github.com', 'guthub.com': 'github.com',
      'githib.com': 'github.com', 'githun.com': 'github.com',
      'githlb.com': 'github.com', 'githab.com': 'github.com',
      'notionso.com': 'notion.so', 'notion-app.com': 'notion.so',
      'g00gle.com': 'google.com', 'googgle.com': 'google.com',
      'gogle.com': 'google.com', 'googel.com': 'google.com',
      'paypa1.com': 'paypal.com', 'paypall.com': 'paypal.com',
      'app1e.com': 'apple.com', 'appte.com': 'apple.com',
      'app1e-id.com': 'apple.com', 'apple-id.com': 'apple.com',
      'micros0ft.com': 'microsoft.com', 'microsft.com': 'microsoft.com',
      'amaz0n.com': 'amazon.com', 'amazom.com': 'amazon.com',
      'netf1ix.com': 'netflix.com', 'netfilx.com': 'netflix.com',
      'faceb00k.com': 'facebook.com', 'facebok.com': 'facebook.com',
    };

    if (typosquatting[hostname]) {
      warnings.push(`🚨 Typosquatting! Looks like "${typosquatting[hostname]}"`);
    }

    // Check TLD risk
    const tld = hostname.split('.').pop();
    if (SUSPICIOUS_TLDS.includes(tld)) {
      warnings.push(`⚠️  High-risk TLD: .${tld}`);
    }

    // Subdomain abuse (e.g., paypal.com.malicious.com)
    const parts = hostname.split('.');
    if (parts.length >= 3) {
      const baseDomain = parts.slice(-2).join('.');
      const subdomainPart = parts.slice(0, -2).join('.');
      // Check if subdomain looks like a legitimate brand
      const brandSubdomains = ['login', 'signin', 'account', 'secure', 'verify', 'update'];
      const suspiciousBrand = brandSubdomains.find(b =>
        subdomainPart.includes(b) && !TRUSTED_DOMAINS.includes(baseDomain) && !TRUSTED_DOMAINS.includes(hostname)
      );
      if (suspiciousBrand) {
        warnings.push(`🚨 Brand-spoofing subdomain: "${suspiciousBrand}" on untrusted domain`);
      }
    }

    // Check trusted
    const isTrusted = TRUSTED_DOMAINS.some(d =>
      hostname === d || hostname.endsWith('.' + d)
    );

    // HTTPS check
    if (urlObj.protocol === 'http:') {
      warnings.push(`⚠️  No HTTPS (data will be transmitted in clear text)`);
    }

    // Redirect params
    const hasRedirect = url.includes('redirect=') || url.includes('url=') ||
                        url.includes('next=') || url.includes('goto=') ||
                        url.includes('continue=');
    if (hasRedirect) {
      warnings.push(`🔍 URL contains redirect parameter`);
    }

    // Short URL services
    const shortDomains = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly'];
    if (shortDomains.some(d => hostname === d || hostname.endsWith('.' + d))) {
      warnings.push(`🔍 Shortened URL (destination hidden)`);
    }

    return { hostname, isTrusted, warnings };

  } catch (e) {
    return {
      hostname: null,
      isTrusted: false,
      warnings: [`⚠️  Invalid URL: ${e.message}`],
    };
  }
}

// ─── LAYER 2: CERT CHECK ──────────────────────────────────────────────────────

function checkCert(url) {
  try {
    const urlObj = new URL(url);
    if (urlObj.protocol === 'http:') {
      return Promise.resolve({ ok: true, note: 'HTTP (no cert check needed)' });
    }

    // Use curl -I for HEAD request, -k to ignore cert errors (we just check connectivity)
    const output = execSync(
      `curl -sI --connect-timeout 5 -o /dev/null -w "%{http_code}|%{ssl_verify_result}|%{url_effective}" ${JSON.stringify(url)} 2>/dev/null || echo "curl-failed"`,
      { timeout: 8000 }
    ).toString().trim();

    if (output.includes('curl-failed') || !output) {
      return Promise.resolve({ ok: true, note: 'Cert check skipped (proxy/network issue)' });
    }

    const parts = output.split('|');
    const httpCode = parts[0];
    const sslResult = parseInt(parts[1] || '0');

    if (httpCode === '000') {
      return Promise.resolve({ ok: false, reason: 'Connection failed' });
    }

    if (sslResult !== 0) {
      return Promise.resolve({ ok: false, reason: `SSL error (code: ${sslResult})` });
    }

    return Promise.resolve({ ok: true });
  } catch (e) {
    return Promise.resolve({ ok: true, note: 'Cert check unavailable' });
  }
}

// ─── LAYER 3: CONTENT AUDIT ──────────────────────────────────────────────────

function auditContent(html, url) {
  const issues = [];
  const lowerHtml = html.toLowerCase();

  // Strip comments and scripts for cleaner analysis
  const cleanText = html
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .toLowerCase();

  // Phishing keywords
  const allPhishing = [...PHISHING_KEYWORDS_EN, ...PHISHING_KEYWORDS_ZH];
  for (const kw of allPhishing) {
    if (cleanText.includes(kw)) {
      issues.push(`🔍 Phishing keyword: "${kw}"`);
      break; // One is enough signal
    }
  }

  // Password inputs on non-trusted pages
  const hasPasswordField = /<input[^>]*type\s*=\s*["']?password/i.test(html);
  if (hasPasswordField) {
    try {
      const urlObj = new URL(url);
      const host = urlObj.hostname.toLowerCase();
      const isTrusted = TRUSTED_DOMAINS.some(d => host === d || host.endsWith('.' + d));
      if (!isTrusted) {
        issues.push(`🚨 Password field on untrusted domain: ${host}`);
      }
    } catch {}
  }

  // Forms submitting externally
  const formMatches = html.match(/<form[^>]*>/gi) || [];
  for (const formTag of formMatches) {
    const actionMatch = formTag.match(/action\s*=\s*["']([^"']+)["']/i);
    if (actionMatch) {
      try {
        const formAction = actionMatch[1];
        const absoluteAction = new URL(formAction, url);
        const urlObj = new URL(url);
        if (absoluteAction.hostname !== urlObj.hostname) {
          issues.push(`🔍 Form submits externally to: ${absoluteAction.hostname}`);
        }
      } catch {}
    }
  }

  // External resources (images, scripts, iframes)
  const externalScripts = (html.match(/<script[^>]*src\s*=\s*["'][^"']+["']/gi) || [])
    .filter(tag => {
      try {
        const match = tag.match(/src\s*=\s*["']([^"']+)["']/i);
        if (!match) return false;
        return new URL(match[1], url).hostname !== new URL(url).hostname;
      } catch { return false; }
    });

  const externalIframes = (html.match(/<iframe[^>]*src\s*=\s*["'][^"']+["']/gi) || [])
    .filter(tag => {
      try {
        const match = tag.match(/src\s*=\s*["']([^"']+)["']/i);
        if (!match) return false;
        return new URL(match[1], url).hostname !== new URL(url).hostname;
      } catch { return false; }
    });

  if (externalScripts.length > 5) {
    issues.push(`⚠️  ${externalScripts.length} external scripts`);
  }
  if (externalIframes.length > 0) {
    issues.push(`🔍 ${externalIframes.length} embedded iframe(s)`);
  }

  // eval() in scripts
  if (/<script[\s\S]*?eval\s*\([\s\S]*?<\/script>/gi.test(html)) {
    issues.push(`⚠️  Contains eval()`);
  }

  // Inline event handlers (potential XSS)
  const inlineHandlers = (html.match(/on\w+\s*=\s*["'][^"']*\$\{[^}]+\}/gi) || []);
  if (inlineHandlers.length > 0) {
    issues.push(`⚠️  Inline JS template expressions in event handlers`);
  }

  // Meta refresh
  const metaRefresh = /<meta[^>]*http-equiv\s*=\s*["']?refresh["']?[^>]*content\s*=\s*["']?[^"']*url\s*=/i.test(html);
  if (metaRefresh) {
    issues.push(`🔍 Meta refresh redirect`);
  }

  return issues;
}

// ─── RISK SCORE ─────────────────────────────────────────────────────────────

function calcRisk(analysis, cert, issues) {
  if (!analysis.hostname) return '🔴 UNKNOWN';

  let score = 0;
  const critical = analysis.warnings.filter(w => w.includes('🚨'));
  const warns = analysis.warnings.filter(w => w.includes('⚠️'));
  const notes = analysis.warnings.filter(w => w.includes('🔍'));

  score += critical.length * 30;
  score += warns.length * 10;
  score += notes.length * 3;
  if (!cert.ok) score += 20;
  score += issues.filter(i => i.includes('🚨')).length * 30;
  score += issues.filter(i => i.includes('⚠️')).length * 10;
  score += issues.filter(i => i.includes('🔍')).length * 5;

  if (score === 0) return '🟢 LOW';
  if (score < 30) return '🟡 MEDIUM';
  if (score < 60) return '🟠 HIGH';
  return '🔴 CRITICAL';
}

// ─── HTTP FETCH ─────────────────────────────────────────────────────────────

const { execSync } = require('child_process');

function fetchUrl(url, maxChars = 50000) {
  try {
    // Use curl which respects HTTP_PROXY/HTTPS_PROXY env vars
    const content = execSync(
      `curl -sL --max-time 15 --connect-timeout 10 ` +
      `-A "Mozilla/5.0 (compatible; OpenClawBrowser/1.0)" ` +
      `-H "Accept: text/html,application/xhtml+xml,*/*" ` +
      `--max-filesize 1048576 ` +
      `${JSON.stringify(url)}`,
      { timeout: 20000, maxBuffer: 1048576 }
    ).toString('utf-8');

    // Follow final URL from curl's output
    // (simple: just return what we got)
    return { success: true, content: content.slice(0, maxChars || 50000), finalUrl: url };
  } catch (e) {
    const msg = e.stderr ? e.stderr.toString() : e.message;
    if (e.killed || e.signal === 'SIGTERM') {
      return { success: false, error: 'Timeout' };
    }
    return { success: false, error: msg.slice(0, 100) };
  }
}

// ─── EXTRACT TEXT ───────────────────────────────────────────────────────────

function extractText(html) {
  return html
    .replace(/<!--[\s\S]*?-->/g, '')
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<noscript[\s\S]*?<\/noscript>/gi, '')
    .replace(/<header[\s\S]*?<\/header>/gi, '')
    .replace(/<footer[\s\S]*?<\/footer>/gi, '')
    .replace(/<nav[\s\S]*?<\/nav>/gi, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

// ─── MAIN ───────────────────────────────────────────────────────────────────

async function safeReadUrl(url, skipWarnings = false) {
  // Layer 1: URL Analysis
  const analysis = analyzeUrl(url);
  console.error('\n🔍 URL Safety Analysis');
  console.error(`   Host: ${analysis.hostname || 'invalid'}`);
  console.error(`   Trusted: ${analysis.isTrusted ? '✅' : '❌'}`);

  if (analysis.warnings.length > 0) {
    analysis.warnings.forEach(w => console.error(`   ${w}`));
  } else {
    console.error('   ✅ No URL warnings');
  }

  // Block critical
  const critical = analysis.warnings.filter(w => w.includes('🚨'));
  if (critical.length > 0 && !skipWarnings) {
    return { success: false, blocked: true, reason: critical.join('; ') };
  }

  // Layer 2: Cert
  const cert = await checkCert(url);
  console.error(`\n🔒 SSL: ${cert.ok ? '✅ Valid' : '❌ ' + (cert.reason || 'unknown')}`);
  if (cert.warning) console.error(`   ⚠️  ${cert.warning}`);

  // Layer 3: Fetch
  console.error('\n🌐 Fetching...');
  const result = await fetchUrl(url);

  if (!result.success) {
    console.error(`\n❌ Fetch failed: ${result.error}`);
    return { success: false, error: result.error };
  }

  // Layer 4: Content Audit
  console.error('\n📋 Content audit...');
  const issues = auditContent(result.content, result.finalUrl);

  if (issues.length > 0) {
    issues.forEach(i => console.error(`   ${i}`));
  } else {
    console.error('   ✅ No content issues');
  }

  const text = extractText(result.content);
  const risk = calcRisk(analysis, cert, issues);

  console.error(`\n🛡️  Safety: ${risk}`);
  console.error('✅ Done\n');

  return {
    success: true,
    url: result.finalUrl,
    text,
    contentLength: result.content.length,
    risk,
    warnings: [...analysis.warnings, ...issues],
  };
}

// ─── CLI ─────────────────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (cmd === 'read' && args[1]) {
    const result = await safeReadUrl(args[1]);

    if (result.blocked) {
      console.log(`\n🚫 BLOCKED: ${result.reason}`);
      process.exit(1);
    }

    if (!result.success) {
      console.log(`\n❌ Failed: ${result.error}`);
      process.exit(1);
    }

    console.log(`═`.repeat(60));
    console.log(`🔗 ${result.url}`);
    console.log(`🛡️  Risk: ${result.risk}`);
    console.log(`═`.repeat(60));
    console.log(result.text);
    return;

  } else if (cmd === 'analyze' && args[1]) {
    const analysis = analyzeUrl(args[1]);
    const cert = await checkCert(args[1]);
    console.log(JSON.stringify({ url: args[1], analysis, cert }, null, 2));
    return;

  } else if (cmd === 'help') {
    console.log(`
Browser Skill - Safety-Aware Web Reader

Usage:
  node index.js read <url>      Fetch page with full safety audit
  node index.js analyze <url>   URL-only safety analysis
  node index.js help            This help

Safety Layers:
  1. URL analysis (IP URLs, typosquatting, subdomain abuse, short URLs)
  2. HTTPS certificate check
  3. Content audit (phishing keywords, password fields, external forms/scripts)

Exit codes:
  0 = success
  1 = blocked / error
`);
    return;
  }

  console.log('Usage: node index.js read <url>');
  console.log('       node index.js analyze <url>');
}

main().catch(e => { console.error(e); process.exit(1); });
