# memory-lancedb-pro: memory_get Implementation Research

**研究日期**: 2026-04-11  
**目标**: 为 memory-lancedb-pro 插件设计并实现 memory_get 功能

---

## 1. 当前存储架构分析

### 1.1 LanceDB 表结构

```typescript
// src/store.ts 定义
interface MemoryEntry {
  id: string;                    // UUID v4
  text: string;                  // 记忆文本
  vector: number[];              // 768/1024 维 embedding 向量
  category: "preference" | "fact" | "decision" | "entity" | "other";
  scope: string;                // "global", "agent:<id>", "custom:<name>", etc.
  importance: number;            // 0.0 - 1.0
  timestamp: number;             // Unix ms
  metadata?: string;            // JSON 字符串，可扩展
}
```

**表名**: `memories`  
**索引**: 
- Vector ANN 索引 (HNSW_SQ/IVF_FLAT 等)
- FTS 全文索引 (用于 BM25 搜索)

### 1.2 现有存储方法 (store.ts)

| 方法 | 功能 | 适用场景 |
|------|------|----------|
| `store(entry)` | 插入新记忆 | 自动捕获、手动存储 |
| `importEntry(entry)` | 导入带 ID/timestamp 的记忆 | 迁移、重新嵌入 |
| `getById(id)` | **按 ID 精确读取单条记忆** | ⚠️ 已有，待暴露为工具 |
| `vectorSearch(vector, limit, minScore, scopeFilter)` | 向量相似度搜索 | memory_recall 核心 |
| `bm25Search(query, limit, scopeFilter)` | BM25 全文搜索 | memory_recall 辅助 |
| `list(scopeFilter, category, limit, offset)` | 列表查询 | memory_list 工具 |
| `update(id, updates, scopeFilter)` | 更新记忆 | memory_update 工具 |
| `delete(id, scopeFilter)` | 删除记忆 | memory_forget 工具 |
| `stats(scopeFilter)` | 统计信息 | memory_stats 工具 |

### 1.3 现有工具 (tools.ts)

| 工具名 | 功能 | 状态 |
|--------|------|------|
| `memory_recall` | 语义搜索记忆 | ✅ 已有 |
| `memory_store` | 存储新记忆 | ✅ 已有 |
| `memory_forget` | 删除记忆 | ✅ 已有 |
| `memory_update` | 更新记忆 | ✅ 已有 |
| `memory_stats` | 统计信息 | ✅ 已有 |
| `memory_list` | 列出记忆 | ✅ 已有 |
| **`memory_get`** | **按 ID 读取或按路径读取文件** | ❌ **缺失** |

---

## 2. 需求分析

### 2.1 功能目标

`memory_get` 工具需要支持两种读取模式：

**模式 A: 按 ID 读取记忆条目**
- 输入: 记忆 ID (完整 UUID 或 8+ 字符前缀)
- 输出: 该记忆的完整信息 (text, category, scope, importance, timestamp)
- 类似: 内置 memory-core 的 `memory_get` 工具

**模式 B: 按路径读取工作区文件**
- 输入: 文件路径 + 可选行范围 (from, lines)
- 输出: 文件指定行的内容
- 用途: 读取 MEMORY.md、daily notes 等记忆文件
- 类似: 传统 `read` 工具但专注记忆相关文件

### 2.2 为什么需要 memory_get

1. **调试需求**: 当 memory_recall 搜索结果不理想时，直接用 ID 获取特定记忆
2. **上下文补充**: 在复杂推理中按 ID 读取特定记忆而非依赖搜索
3. **文件访问**: 读取记忆文件 (MEMORY.md, daily notes) 而非只搜索向量记忆
4. **一致性**: 与 memory-core 内置工具保持 API 一致性

---

## 3. API 设计

### 3.1 函数签名

```typescript
// src/tools.ts 新增

interface MemoryGetParams {
  /** 要读取的记忆 ID (完整 UUID 或 8+ 字符前缀) */
  memoryId?: string;
  
  /** 要读取的文件路径 (相对于工作区) */
  filePath?: string;
  
  /** 文件读取起始行 (1-indexed，默认 1) */
  from?: number;
  
  /** 文件读取行数 (默认读取全部) */
  lines?: number;
  
  /** 限定读取的 scope (可选) */
  scope?: string;
}

interface MemoryGetResult {
  // 成功时
  content: [{ type: "text"; text: string }];
  details: {
    action: "memory_fetched" | "file_read";
    // Memory 模式
    id?: string;
    text?: string;
    category?: string;
    scope?: string;
    importance?: number;
    timestamp?: number;
    // File 模式
    filePath?: string;
    totalLines?: number;
    returnedLines?: { from: number; to: number };
  };
  
  // 失败时
  content: [{ type: "text"; text: string }];
  details: { error: string; ... };
}
```

### 3.2 参数约束

| 参数 | 约束 | 说明 |
|------|------|------|
| `memoryId` | 可选，与 filePath 二选一 | ID 优先于文件路径 |
| `filePath` | 可选，相对工作区路径 | 仅允许读取记忆相关文件 |
| `from` | 1-indexed，默认 1 | 仅用于文件模式 |
| `lines` | 正整数，可选 | 仅用于文件模式 |
| `scope` | 可选 | 用于验证访问权限 |

### 3.3 允许读取的文件路径

为安全起见，`memory_get` 只允许读取以下记忆相关文件：

```
~/.openclaw/workspace/
├── MEMORY.md
├── memory/
│   ├── YYYY-MM-DD.md           # 每日笔记
│   ├── projects/
│   │   └── <project>.md        # 项目笔记
├── .learnings/
│   ├── LEARNINGS.md
│   ├── ERRORS.md
│   └── FEATURE_REQUESTS.md
├── research/
│   └── **/*.md                 # 研究文档
└── self-improving/
    └── **/*.md                 # 自我改进文档
```

**黑名单模式**:
- ❌ 排除 `AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md` (身份文件)
- ❌ 排除 `.json`, `.yaml`, `.config.*` (配置文件)
- ❌ 排除 `scripts/`, `skills/` 目录 (工具/技能)

---

## 4. 实现方案

### 4.1 代码结构

```typescript
// src/tools.ts 新增

/**
 * memory_get 工具实现
 * 支持两种模式:
 * 1. Memory 模式: 按 ID 读取 LanceDB 记忆
 * 2. File 模式: 按路径读取记忆相关文件
 */
export function registerMemoryGetTool(
  api: OpenClawPluginApi,
  context: ToolContext,
) {
  api.registerTool(
    (toolCtx) => {
      const agentId = resolveAgentId(
        (toolCtx as any)?.agentId,
        context.agentId,
      ) ?? "main";
      
      return {
        name: "memory_get",
        label: "Memory Get",
        description:
          "Read specific memory entries by ID or read memory-related files by path and line range. Use when you need exact memory content rather than search.",
        parameters: Type.Object({
          memoryId: Type.Optional(
            Type.String({
              description:
                "Memory ID to read (full UUID or 8+ char prefix). Takes precedence over filePath.",
            }),
          ),
          filePath: Type.Optional(
            Type.String({
              description:
                "File path relative to workspace to read (e.g., 'MEMORY.md', 'memory/2026-04-11.md'). Only memory-related files are allowed.",
            }),
          ),
          from: Type.Optional(
            Type.Number({
              description: "Starting line number for file read (1-indexed, default: 1)",
            }),
          ),
          lines: Type.Optional(
            Type.Number({
              description: "Number of lines to read (default: all lines from 'from')",
            }),
          ),
          scope: Type.Optional(
            Type.String({
              description: "Scope filter for memory read (optional)",
            }),
          ),
        }),
        
        async execute(_toolCallId, params) {
          const { memoryId, filePath, from, lines, scope } = params;
          
          // 验证参数
          if (!memoryId && !filePath) {
            return {
              content: [{ type: "text", text: "Provide either 'memoryId' or 'filePath'" }],
              details: { error: "missing_param" },
            };
          }
          
          // 优先处理 Memory 模式
          if (memoryId) {
            return executeMemoryMode(memoryId, scope, agentId, context);
          }
          
          // File 模式
          return executeFileMode(filePath!, from, lines, context);
        },
      };
    },
    { name: "memory_get" },
  );
}

// ============================================================================
// 内部实现
// ============================================================================

/**
 * Memory 模式: 按 ID 读取 LanceDB 记忆
 */
async function executeMemoryMode(
  memoryId: string,
  scope: string | undefined,
  agentId: string,
  context: ToolContext,
) {
  try {
    // 验证 scope 权限
    let scopeFilter = context.scopeManager.getAccessibleScopes(agentId);
    if (scope) {
      if (!context.scopeManager.isAccessible(scope, agentId)) {
        return {
          content: [{ type: "text", text: `Access denied to scope: ${scope}` }],
          details: { error: "scope_access_denied", requestedScope: scope },
        };
      }
      scopeFilter = [scope];
    }
    
    // 读取记忆
    const entry = await context.store.getById(memoryId);
    
    if (!entry) {
      return {
        content: [{ type: "text", text: `Memory ${memoryId} not found` }],
        details: { error: "not_found", id: memoryId },
      };
    }
    
    // 验证 scope 权限 (防止跨 scope 读取)
    if (!scopeFilter.includes(entry.scope) && entry.scope !== "global") {
      return {
        content: [{ type: "text", text: `Memory ${memoryId} not found` }],
        details: { error: "not_found", id: memoryId },
      };
    }
    
    // 格式化输出
    const date = new Date(entry.timestamp).toISOString();
    const text = [
      `Memory ID: ${entry.id}`,
      `Category: ${entry.category}`,
      `Scope: ${entry.scope}`,
      `Importance: ${entry.importance}`,
      `Created: ${date}`,
      ``,
      `Content:`,
      entry.text,
    ].join("\n");
    
    return {
      content: [{ type: "text", text }],
      details: {
        action: "memory_fetched",
        id: entry.id,
        text: entry.text,
        category: entry.category,
        scope: entry.scope,
        importance: entry.importance,
        timestamp: entry.timestamp,
      },
    };
  } catch (error) {
    return {
      content: [{
        type: "text",
        text: `Failed to read memory: ${error instanceof Error ? error.message : String(error)}`,
      }],
      details: { error: "read_failed", message: String(error) },
    };
  }
}

/**
 * File 模式: 读取记忆相关文件
 */
async function executeFileMode(
  filePath: string,
  from: number = 1,
  lines: number | undefined,
  context: ToolContext,
) {
  const WORKSPACE = process.cwd(); // 或从 context 获取
  
  // 1. 安全检查: 规范化路径
  const safePath = validateMemoryFilePath(filePath, WORKSPACE);
  if (!safePath) {
    return {
      content: [{
        type: "text",
        text: `Access denied: '${filePath}' is not a memory-related file`,
      }],
      details: { error: "path_not_allowed" },
    };
  }
  
  // 2. 读取文件
  try {
    const absolutePath = path.join(WORKSPACE, safePath);
    const content = await readFile(absolutePath, "utf-8");
    const allLines = content.split("\n");
    const totalLines = allLines.length;
    
    // 3. 提取行范围
    const startLine = Math.max(1, from);
    const endLine = lines
      ? Math.min(totalLines, startLine + lines - 1)
      : totalLines;
    
    const selectedLines = allLines.slice(startLine - 1, endLine);
    const selectedContent = selectedLines.join("\n");
    
    // 4. 格式化输出
    const header = lines
      ? `[${safePath}] Lines ${startLine}-${endLine} of ${totalLines}:`
      : `[${safePath}] (${totalLines} lines):`;
    
    const displayContent = selectedContent.length > 4000
      ? selectedContent.slice(0, 4000) + "\n... (truncated)"
      : selectedContent;
    
    return {
      content: [{ type: "text", text: `${header}\n\`\`\`\n${displayContent}\n\`\`\`` }],
      details: {
        action: "file_read",
        filePath: safePath,
        totalLines,
        returnedLines: { from: startLine, to: endLine },
        content: selectedContent, // 包含原始内容供后续处理
      },
    };
  } catch (error) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") {
      return {
        content: [{ type: "text", text: `File not found: '${filePath}'` }],
        details: { error: "file_not_found" },
      };
    }
    return {
      content: [{
        type: "text",
        text: `Failed to read file: ${error instanceof Error ? error.message : String(error)}`,
      }],
      details: { error: "read_failed" },
    };
  }
}

/**
 * 验证文件路径是否允许读取
 */
function validateMemoryFilePath(
  relativePath: string,
  workspace: string,
): string | null {
  // 1. 规范化路径 (防止 ../ 逃逸)
  const normalized = path.normalize(relativePath).replace(/\\/g, "/");
  
  // 2. 必须在工作区内
  const absolute = path.resolve(workspace, normalized);
  if (!absolute.startsWith(workspace)) {
    return null; // 路径逃逸
  }
  
  // 3. 必须是 .md 文件
  if (!normalized.endsWith(".md")) {
    return null;
  }
  
  // 4. 白名单目录检查
  const ALLOWED_PREFIXES = [
    "memory/",
    ".learnings/",
    "research/",
    "self-improving/",
  ];
  
  const BASENAME_CHECKS = [
    "MEMORY.md",
  ];
  
  const isInAllowedDir = ALLOWED_PREFIXES.some(prefix =>
    normalized.startsWith(prefix),
  );
  const isAllowedBasename = BASENAME_CHECKS.includes(
    path.basename(normalized),
  );
  
  if (!isInAllowedDir && !isAllowedBasename) {
    return null;
  }
  
  // 5. 黑名单排除
  const BLOCKED = [
    /AGENTS\.md$/i,
    /SOUL\.md$/i,
    /USER\.md$/i,
    /IDENTITY\.md$/i,
    /TOOLS\.md$/i,
    /HEARTBEAT\.md$/i,
  ];
  
  for (const pattern of BLOCKED) {
    if (pattern.test(normalized)) {
      return null;
    }
  }
  
  return normalized;
}
```

### 4.2 注册到工具集

```typescript
// index.ts 修改
export function registerAllMemoryTools(
  api: OpenClawPluginApi,
  context: ToolContext,
  options: {
    enableManagementTools?: boolean;
  } = {},
) {
  // 核心工具 (始终启用)
  registerMemoryRecallTool(api, context);
  registerMemoryStoreTool(api, context);
  registerMemoryForgetTool(api, context);
  registerMemoryUpdateTool(api, context);
  
  // ✅ 新增: memory_get
  registerMemoryGetTool(api, context);
  
  // 管理工具 (可选)
  if (options.enableManagementTools) {
    registerMemoryStatsTool(api, context);
    registerMemoryListTool(api, context);
  }
}
```

---

## 5. 安全考虑

### 5.1 Scope 隔离

- Memory 模式必须验证 scope 权限
- 用户只能读取自己有权访问的 scope
- 不存在的 scope 返回 "not found" 而非 "access denied" (防止枚举攻击)

### 5.2 文件路径安全

| 防护措施 | 实现 |
|----------|------|
| 路径规范化 | `path.normalize()` 去除 `..` |
| 工作区边界检查 | 解析后的路径必须在 workspace 内 |
| 仅允许 .md | 防止读取配置/代码 |
| 白名单目录 | 限制在 memory/, .learnings/, research/, self-improving/ |
| 黑名单文件 | 排除 AGENTS.md, SOUL.md 等身份文件 |

### 5.3 输出限制

- 单次返回内容过长时截断 (max 4000 chars)
- 文件读取支持行范围限制
- 避免在 details 中暴露敏感信息

---

## 6. 与现有工具的关系

### 6.1 与 memory_recall 的对比

| 特性 | memory_recall | memory_get |
|------|---------------|------------|
| 读取方式 | 语义搜索 | ID/路径精确读取 |
| 返回数量 | 多条 (limit) | 单条 |
| 适用场景 | "记得我之前说过什么？" | "那条记忆的具体内容是什么？" |
| 性能 | 需要向量计算 | 直接读取，无向量计算 |

### 6.2 与 read 工具的对比

| 特性 | read | memory_get |
|------|------|------------|
| 访问范围 | 所有工作区文件 | 仅记忆相关文件 |
| 权限模型 | 基于 workspace | 基于 scope + path 白名单 |
| 用途 | 通用文件读取 | 专注记忆文件访问 |

---

## 7. 实施计划

### Phase 1: 核心实现 (2-3 小时)

1. 实现 `registerMemoryGetTool()` 函数
2. 实现 `executeMemoryMode()` - 使用已有的 `store.getById()`
3. 实现 `validateMemoryFilePath()` - 路径安全检查
4. 实现 `executeFileMode()` - 文件读取
5. 单元测试

### Phase 2: 集成与测试 (1-2 小时)

1. 注册到 `registerAllMemoryTools()`
2. 更新 `openclaw.plugin.json` Schema
3. 端到端测试

### Phase 3: 文档与发布 (1 小时)

1. 更新 README.md
2. 编写使用示例
3. 发布

---

## 8.  Effort Estimation

| 任务 | 时间 | 复杂度 |
|------|------|--------|
| memory_get Tool 核心实现 | 2h | Medium |
| 路径安全验证 | 1h | Low |
| 文件读取逻辑 | 1h | Low |
| 单元测试 | 1h | Low |
| 集成测试 | 1h | Medium |
| 文档更新 | 0.5h | Low |
| **总计** | **6.5h** | **Medium** |

---

## 9. 附录: 已有实现参考

### 9.1 store.getById() 已实现

```typescript
// src/store.ts 第 175-196 行
async getById(id: string): Promise<MemoryEntry | null> {
  await this.ensureInitialized();
  const safeId = escapeSqlLiteral(id);
  const rows = await this.table!.query()
    .where(`id = '${safeId}'`)
    .limit(1)
    .toArray();
  if (rows.length === 0) return null;

  const row = rows[0];
  return {
    id: row.id as string,
    text: row.text as string,
    vector: Array.from(row.vector as Iterable<number>),
    category: row.category as MemoryEntry["category"],
    scope: (row.scope as string | undefined) ?? "global",
    importance: Number(row.importance),
    timestamp: Number(row.timestamp),
    metadata: (row.metadata as string) || "{}",
  };
}
```

### 9.2 工具注册模式参考

```typescript
// src/tools.ts 第 50-120 行 - memory_recall 实现
export function registerMemoryRecallTool(
  api: OpenClawPluginApi,
  context: ToolContext,
) {
  api.registerTool(
    (toolCtx) => {
      const agentId = resolveAgentId(
        (toolCtx as any)?.agentId,
        context.agentId,
      ) ?? "main";
      return {
        name: "memory_recall",
        // ... parameters and execute
      };
    },
    { name: "memory_recall" },
  );
}
```

---

*研究完成 | 2026-04-11*
