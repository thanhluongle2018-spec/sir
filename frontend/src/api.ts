export type TaskStatus = "active" | "paused" | "error";
export type MatchMode = "any" | "all";

export interface Task {
  id: number;
  name: string;
  keywords: string[];
  exclude_keywords: string[];
  match_mode: MatchMode;
  platforms: string[];
  brand?: string | null;
  model?: string | null;
  category?: string | null;
  min_price?: number | null;
  max_price?: number | null;
  seller?: string | null;
  condition?: string | null;
  currency: string;
  interval_seconds: number;
  status: TaskStatus;
  channel_ids: number[];
  last_checked_at?: string | null;
  next_check_at?: string | null;
  last_error?: string | null;
  consecutive_failures: number;
  created_at: string;
  updated_at: string;
}

export interface Item {
  id: number;
  platform: string;
  external_id: string;
  title: string;
  price?: number | null;
  currency: string;
  image_url?: string | null;
  url: string;
  seller?: string | null;
  condition?: string | null;
  discovered_at: string;
  published_at?: string | null;
  is_read: boolean;
  matched_keywords: string[];
  task_ids: number[];
}

export interface Channel {
  id: number;
  name: string;
  channel_type: string;
  enabled: boolean;
  credentials_masked: Record<string, unknown>;
  config: Record<string, unknown>;
  last_test_at?: string | null;
  last_test_ok?: boolean | null;
  last_error?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlatformInfo {
  code: string;
  name: string;
  name_ja: string;
  status: string;
  data_source: string;
  capabilities: string[];
  limitations: string[];
  config_notes: string;
  can_monitor?: boolean;
  status_label?: string;
}

export interface DataSourceInfo {
  id: string;
  platform: string;
  kind: string;
  name: string;
  name_zh: string;
  status: string;
  summary: string;
  research_notes: string[];
  requirements: string[];
  limitations: string[];
  references: string[];
  status_label?: string;
}

export interface DashboardStats {
  task_total: number;
  task_active: number;
  task_paused: number;
  items_today: number;
  items_total: number;
  items_by_platform: Record<string, number>;
  notifications_success: number;
  notifications_failed: number;
  notifications_pending: number;
}

export interface StatsCharts {
  daily: { date: string; count: number }[];
  by_platform: Record<string, number>;
  by_keyword: Record<string, number>;
}

export interface RunLog {
  id: number;
  task_id?: number | null;
  platform?: string | null;
  level: string;
  message: string;
  detail?: Record<string, unknown> | null;
  created_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  health: () => request<{ ok: boolean }>("/api/health"),
  platforms: () => request<PlatformInfo[]>("/api/platforms"),
  datasources: () => request<DataSourceInfo[]>("/api/datasources"),
  dashboard: () => request<DashboardStats>("/api/stats/dashboard"),
  charts: () => request<StatsCharts>("/api/stats/charts?days=14"),
  tasks: {
    list: () => request<Task[]>("/api/tasks"),
    create: (body: Partial<Task>) =>
      request<Task>("/api/tasks", { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: Partial<Task>) =>
      request<Task>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    pause: (id: number) => request<Task>(`/api/tasks/${id}/pause`, { method: "POST" }),
    resume: (id: number) => request<Task>(`/api/tasks/${id}/resume`, { method: "POST" }),
    remove: (id: number) => request<{ ok: boolean }>(`/api/tasks/${id}`, { method: "DELETE" }),
    run: (id: number) =>
      request<{ ok: boolean; new_items: number; errors: string[] }>(`/api/tasks/${id}/run`, {
        method: "POST",
      }),
  },
  items: {
    list: (params: Record<string, string | number | boolean | undefined>) => {
      const q = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "" && v !== null) q.set(k, String(v));
      });
      return request<Item[]>(`/api/items?${q}`);
    },
    markRead: (id: number) => request<Item>(`/api/items/${id}/read`, { method: "POST" }),
  },
  channels: {
    list: () => request<Channel[]>("/api/channels"),
    create: (body: Record<string, unknown>) =>
      request<Channel>("/api/channels", { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: Record<string, unknown>) =>
      request<Channel>(`/api/channels/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    remove: (id: number) =>
      request<{ ok: boolean }>(`/api/channels/${id}`, { method: "DELETE" }),
    test: (id: number) =>
      request<{ ok: boolean; error?: string }>(`/api/channels/${id}/test`, { method: "POST" }),
  },
  logs: {
    runs: () => request<RunLog[]>("/api/logs/runs?limit=80"),
    notifications: () => request<unknown[]>("/api/logs/notifications?limit=80"),
  },
};
