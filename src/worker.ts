interface AgentRhythm {
  agentId: string;
  activityPatterns: number[];
  optimalHours: number[];
  burnoutRisk: number;
  circadianPeak: number;
  lastUpdated: string;
}

interface OptimizationRequest {
  agentId: string;
  schedule: number[];
  workload: number;
}

class RhythmStore {
  private rhythms: Map<string, AgentRhythm> = new Map();

  constructor() {
    this.initializeSampleData();
  }

  private initializeSampleData(): void {
    const sampleRhythms: AgentRhythm[] = [
      {
        agentId: "agent-001",
        activityPatterns: [0.8, 0.9, 0.7, 0.6, 0.8, 0.9, 0.5],
        optimalHours: [9, 10, 11, 14, 15, 16],
        burnoutRisk: 0.3,
        circadianPeak: 14,
        lastUpdated: new Date().toISOString()
      },
      {
        agentId: "agent-002",
        activityPatterns: [0.6, 0.7, 0.9, 0.8, 0.7, 0.6, 0.5],
        optimalHours: [13, 14, 15, 16, 17, 18],
        burnoutRisk: 0.6,
        circadianPeak: 16,
        lastUpdated: new Date().toISOString()
      }
    ];

    sampleRhythms.forEach(rhythm => this.rhythms.set(rhythm.agentId, rhythm));
  }

  getRhythm(agentId: string): AgentRhythm | undefined {
    return this.rhythms.get(agentId);
  }

  getAllPatterns(): AgentRhythm[] {
    return Array.from(this.rhythms.values());
  }

  optimizeSchedule(request: OptimizationRequest): AgentRhythm {
    const existing = this.rhythms.get(request.agentId);
    const workloadFactor = Math.min(request.workload / 10, 1);
    
    const optimizedRhythm: AgentRhythm = {
      agentId: request.agentId,
      activityPatterns: this.calculateOptimalPatterns(request.schedule),
      optimalHours: this.findOptimalHours(request.schedule),
      burnoutRisk: this.calculateBurnoutRisk(request.workload, existing?.burnoutRisk || 0.5),
      circadianPeak: this.detectCircadianPeak(request.schedule),
      lastUpdated: new Date().toISOString()
    };

    this.rhythms.set(request.agentId, optimizedRhythm);
    return optimizedRhythm;
  }

  private calculateOptimalPatterns(schedule: number[]): number[] {
    const patterns: number[] = [];
    for (let i = 0; i < 7; i++) {
      patterns.push(Math.min(0.3 + (schedule[i % schedule.length] || 0) * 0.7, 0.95));
    }
    return patterns;
  }

  private findOptimalHours(schedule: number[]): number[] {
    const optimal: number[] = [];
    schedule.forEach((value, hour) => {
      if (value > 0.7 && hour >= 9 && hour <= 20) {
        optimal.push(hour);
      }
    });
    return optimal.length > 0 ? optimal : [10, 11, 14, 15];
  }

  private calculateBurnoutRisk(workload: number, previousRisk: number): number {
    const newRisk = workload > 8 ? 0.8 : workload > 6 ? 0.6 : 0.3;
    return (previousRisk * 0.3 + newRisk * 0.7);
  }

  private detectCircadianPeak(schedule: number[]): number {
    let peakHour = 14;
    let maxValue = 0;
    
    schedule.forEach((value, hour) => {
      if (value > maxValue && hour >= 9 && hour <= 20) {
        maxValue = value;
        peakHour = hour;
      }
    });
    
    return peakHour;
  }
}

const rhythmStore = new RhythmStore();

function generateHTML(title: string, content: string): string {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Rhythm - ${title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {
            --dark: #0a0a0f;
            --accent: #d946ef;
            --light: #f8fafc;
            --gray: #64748b;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--dark);
            color: var(--light);
            line-height: 1.6;
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 2rem 0;
            border-bottom: 2px solid var(--accent);
            margin-bottom: 2rem;
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, var(--accent), #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: var(--gray);
            font-size: 1.1rem;
        }
        
        .content {
            background: rgba(15, 15, 25, 0.8);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .endpoint {
            background: rgba(217, 70, 239, 0.1);
            border-left: 4px solid var(--accent);
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
        }
        
        .endpoint h3 {
            color: var(--accent);
            margin-bottom: 0.5rem;
        }
        
        .endpoint code {
            background: rgba(0, 0, 0, 0.3);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-family: monospace;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        
        .feature-card {
            background: rgba(30, 30, 40, 0.8);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            border-color: var(--accent);
        }
        
        .feature-card h4 {
            color: var(--accent);
            margin-bottom: 0.5rem;
        }
        
        footer {
            text-align: center;
            padding: 2rem 0;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            margin-top: 2rem;
            color: var(--gray);
        }
        
        .fleet-footer {
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        pre {
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .health-status {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Agent Rhythm</h1>
            <p class="subtitle">Detect and optimize agent work patterns and cycles</p>
        </header>
        
        <div class="content">
            ${content}
        </div>
        
        <footer>
            <div class="fleet-footer">
                Agent Rhythm System • Part of the Global Agent Fleet Network
            </div>
        </footer>
    </div>
</body>
</html>`;
}

function generateDashboard(): string {
  const patterns = rhythmStore.getAllPatterns();
  
  let patternsHTML = "";
  patterns.forEach(pattern => {
    patternsHTML += `
    <div class="endpoint">
        <h3>${pattern.agentId}</h3>
        <p>Burnout Risk: <strong>${(pattern.burnoutRisk * 100).toFixed(1)}%</strong></p>
        <p>Circadian Peak: <strong>${pattern.circadianPeak}:00</strong></p>
        <p>Optimal Hours: ${pattern.optimalHours.join(", ")}</p>
    </div>`;
  });

  return generateHTML("Dashboard", `
    <h2>Agent Rhythm Dashboard</h2>
    <p>Monitor and optimize agent work patterns across the fleet.</p>
    
    <div class="features">
        <div class="feature-card">
            <h4>Activity Pattern Detection</h4>
            <p>Analyze work patterns to identify peak performance periods.</p>
        </div>
        <div class="feature-card">
            <h4>Optimal Scheduling</h4>
            <p>Automatically schedule tasks during optimal performance windows.</p>
        </div>
        <div class="feature-card">
            <h4>Burnout Prediction</h4>
            <p>Predict and prevent agent burnout using workload analysis.</p>
        </div>
        <div class="feature-card">
            <h4>Circadian Agent Cycles</h4>
            <p>Align work with natural circadian rhythms for maximum efficiency.</p>
        </div>
    </div>
    
    <h3>Available Endpoints</h3>
    <div class="endpoint">
        <h3>GET /api/rhythm/:agent</h3>
        <p>Get rhythm data for specific agent</p>
        <code>curl https://agent-rhythm.workers.dev/api/rhythm/agent-001</code>
    </div>
    
    <div class="endpoint">
        <h3>GET /api/patterns</h3>
        <p>Get all agent patterns</p>
        <code>curl https://agent-rhythm.workers.dev/api/patterns</code>
    </div>
    
    <div class="endpoint">
        <h3>POST /api/optimize</h3>
        <p>Optimize agent schedule</p>
        <code>curl -X POST -H "Content-Type: application/json" -d '{"agentId":"agent-001","schedule":[0.8,0.9,0.7,0.6,0.8,0.9,0.5],"workload":7}' https://agent-rhythm.workers.dev/api/optimize</code>
    </div>
    
    <div class="endpoint">
        <h3>GET /health</h3>
        <p>Health check endpoint</p>
        <code>curl https://agent-rhythm.workers.dev/health</code>
    </div>
    
    <h3>Current Agent Patterns</h3>
    ${patternsHTML}
  `);
}

const handler: ExportedHandler = {
  async fetch(request: Request, env: unknown, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;
    
    const headers = {
      "Content-Type": "application/json",
      "X-Frame-Options": "DENY",
      "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com;"
    };
    
    if (path === "/" || path === "/dashboard") {
      return new Response(generateDashboard(), {
        headers: { "Content-Type": "text/html", ...headers }
      });
    }
    
    if (path === "/health") {
      return new Response(JSON.stringify({ status: "ok", timestamp: new Date().toISOString() }), {
        headers
      });
    }
    
    if (path.startsWith("/api/rhythm/")) {
      const agentId = path.split("/").pop();
      if (!agentId) {
        return new Response(JSON.stringify({ error: "Agent ID required" }), {
          status: 400,
          headers
        });
      }
      
      const rhythm = rhythmStore.getRhythm(agentId);
      if (!rhythm) {
        return new Response(JSON.stringify({ error: "Agent not found" }), {
          status: 404,
          headers
        });
      }
      
      return new Response(JSON.stringify(rhythm), { headers });
    }
    
    if (path === "/api/patterns") {
      const patterns = rhythmStore.getAllPatterns();
      return new Response(JSON.stringify({ patterns }), { headers });
    }
    
    if (path === "/api/optimize" && request.method === "POST") {
      try {
        const requestData = await request.json() as OptimizationRequest;
        
        if (!requestData.agentId || !requestData.schedule) {
          return new Response(JSON.stringify({ error: "Missing required fields" }), {
            status: 400,
            headers
          });
        }
        
        const optimized = rhythmStore.optimizeSchedule(requestData);
        return new Response(JSON.stringify({
          success: true,
          message: "Schedule optimized",
          rhythm: optimized
        }), { headers });
      } catch (error) {
        return new Response(JSON.stringify({ error: "Invalid request body" }), {
          status: 400,
          headers
        });
      }
    }
    
    return new Response(JSON.stringify({ error: "Not found" }), {
      status: 404,
      headers
    });
  }
};
const sh = {"Content-Security-Policy":"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; frame-ancestors 'none'","X-Frame-Options":"DENY"};
export default { async fetch(r: Request) { const u = new URL(r.url); if (u.pathname==='/health') return new Response(JSON.stringify({status:'ok'}),{headers:{'Content-Type':'application/json',...sh}}); return new Response(html,{headers:{'Content-Type':'text/html;charset=UTF-8',...sh}}); }};