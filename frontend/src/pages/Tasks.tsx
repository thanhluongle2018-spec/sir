import { FormEvent, useEffect, useState } from "react";
import { api, Channel, PlatformInfo, Task } from "../api";

const INTERVALS = [
  { label: "30 秒", value: 30 },
  { label: "1 分钟", value: 60 },
  { label: "5 分钟", value: 300 },
  { label: "15 分钟", value: 900 },
];

const emptyForm = {
  name: "",
  keywords: "",
  exclude_keywords: "",
  match_mode: "any",
  platforms: ["mercari"] as string[],
  min_price: "",
  max_price: "",
  brand: "",
  model: "",
  category: "",
  seller: "",
  condition: "",
  interval_seconds: 60,
  channel_ids: [] as number[],
};

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const reload = () =>
    Promise.all([api.tasks.list(), api.platforms(), api.channels.list()]).then(
      ([t, p, c]) => {
        setTasks(t);
        setPlatforms(p);
        setChannels(c);
      }
    );

  useEffect(() => {
    reload().catch((e) => setError(String(e.message || e)));
  }, []);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setMsg("");
    const body = {
      name: form.name.trim(),
      keywords: form.keywords.split(/[,，\n]/).map((s) => s.trim()).filter(Boolean),
      exclude_keywords: form.exclude_keywords
        .split(/[,，\n]/)
        .map((s) => s.trim())
        .filter(Boolean),
      match_mode: form.match_mode,
      platforms: form.platforms,
      min_price: form.min_price === "" ? null : Number(form.min_price),
      max_price: form.max_price === "" ? null : Number(form.max_price),
      brand: form.brand || null,
      model: form.model || null,
      category: form.category || null,
      seller: form.seller || null,
      condition: form.condition || null,
      interval_seconds: Number(form.interval_seconds),
      channel_ids: form.channel_ids,
      status: "active",
    };
    try {
      if (editingId) {
        await api.tasks.update(editingId, body as Partial<Task>);
        setMsg("任务已更新");
      } else {
        await api.tasks.create(body as Partial<Task>);
        setMsg("任务已创建");
      }
      setForm(emptyForm);
      setEditingId(null);
      await reload();
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  const startEdit = (t: Task) => {
    setEditingId(t.id);
    setForm({
      name: t.name,
      keywords: t.keywords.join(", "),
      exclude_keywords: t.exclude_keywords.join(", "),
      match_mode: t.match_mode,
      platforms: t.platforms,
      min_price: t.min_price == null ? "" : String(t.min_price),
      max_price: t.max_price == null ? "" : String(t.max_price),
      brand: t.brand || "",
      model: t.model || "",
      category: t.category || "",
      seller: t.seller || "",
      condition: t.condition || "",
      interval_seconds: t.interval_seconds,
      channel_ids: t.channel_ids,
    });
  };

  const togglePlatform = (code: string) => {
    setForm((f) => ({
      ...f,
      platforms: f.platforms.includes(code)
        ? f.platforms.filter((p) => p !== code)
        : [...f.platforms, code],
    }));
  };

  const toggleChannel = (id: number) => {
    setForm((f) => ({
      ...f,
      channel_ids: f.channel_ids.includes(id)
        ? f.channel_ids.filter((x) => x !== id)
        : [...f.channel_ids, id],
    }));
  };

  return (
    <div>
      <h1 className="page-title">监控任务</h1>
      <p className="page-desc">任务、匹配、去重与通知已可用。煤炉 / 骏合屋数据源尚未接入：立即检查不会发现真实商品，界面会标明「未接入 / 当前不能监控」。</p>
      {error && <div className="error-box">{error}</div>}
      {msg && <div className="panel" style={{ color: "var(--ok)" }}>{msg}</div>}

      <div className="panel">
        <h2>{editingId ? `编辑任务 #${editingId}` : "新建任务"}</h2>
        <form onSubmit={onSubmit}>
          <div className="form-grid">
            <label>
              任务名称
              <input
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>
            <label>
              检查间隔
              <select
                value={form.interval_seconds}
                onChange={(e) =>
                  setForm({ ...form, interval_seconds: Number(e.target.value) })
                }
              >
                {INTERVALS.map((i) => (
                  <option key={i.value} value={i.value}>
                    {i.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="full">
              关键词（逗号分隔，支持日/中/英）
              <input
                required
                value={form.keywords}
                onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                placeholder="例: ポケカ, Switch"
              />
            </label>
            <label className="full">
              排除关键词
              <input
                value={form.exclude_keywords}
                onChange={(e) =>
                  setForm({ ...form, exclude_keywords: e.target.value })
                }
              />
            </label>
            <label>
              匹配逻辑
              <select
                value={form.match_mode}
                onChange={(e) => setForm({ ...form, match_mode: e.target.value })}
              >
                <option value="any">任意关键词命中</option>
                <option value="all">全部命中</option>
              </select>
            </label>
            <label>
              品牌
              <input
                value={form.brand}
                onChange={(e) => setForm({ ...form, brand: e.target.value })}
              />
            </label>
            <label>
              最低价 (JPY)
              <input
                type="number"
                value={form.min_price}
                onChange={(e) => setForm({ ...form, min_price: e.target.value })}
              />
            </label>
            <label>
              最高价 (JPY)
              <input
                type="number"
                value={form.max_price}
                onChange={(e) => setForm({ ...form, max_price: e.target.value })}
              />
            </label>
            <label>
              型号
              <input
                value={form.model}
                onChange={(e) => setForm({ ...form, model: e.target.value })}
              />
            </label>
            <label>
              分类
              <input
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              />
            </label>
            <label>
              卖家
              <input
                value={form.seller}
                onChange={(e) => setForm({ ...form, seller: e.target.value })}
              />
            </label>
            <label>
              商品状态
              <input
                value={form.condition}
                onChange={(e) => setForm({ ...form, condition: e.target.value })}
              />
            </label>
            <div className="full">
              <div className="muted" style={{ marginBottom: 8 }}>
                目标平台（本版本仅煤炉 / 骏合屋）
              </div>
              <div className="checks">
                {platforms.map((p) => (
                  <label key={p.code}>
                    <input
                      type="checkbox"
                      checked={form.platforms.includes(p.code)}
                      onChange={() => togglePlatform(p.code)}
                    />
                    {p.name_ja}
                    <span
                      className={`badge ${
                        p.status === "supported"
                          ? "ok"
                          : p.status === "partial"
                            ? "warn"
                            : "err"
                      }`}
                    >
                      {p.status === "unavailable" || p.status === "stub"
                        ? "当前不能监控"
                        : p.status === "partial"
                          ? "部分接入"
                          : p.status === "supported"
                            ? "已接入"
                            : p.status}
                    </span>
                  </label>
                ))}
              </div>
            </div>
            <div className="full">
              <div className="muted" style={{ marginBottom: 8 }}>
                通知渠道
              </div>
              <div className="checks">
                {channels.map((c) => (
                  <label key={c.id}>
                    <input
                      type="checkbox"
                      checked={form.channel_ids.includes(c.id)}
                      onChange={() => toggleChannel(c.id)}
                    />
                    {c.name} ({c.channel_type})
                  </label>
                ))}
                {!channels.length && <span className="muted">请先在「通知渠道」中添加</span>}
              </div>
            </div>
          </div>
          <div className="toolbar" style={{ marginTop: 14 }}>
            <button className="btn primary" type="submit">
              {editingId ? "保存" : "创建"}
            </button>
            {editingId && (
              <button
                className="btn ghost"
                type="button"
                onClick={() => {
                  setEditingId(null);
                  setForm(emptyForm);
                }}
              >
                取消编辑
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="panel">
        <h2>任务列表</h2>
        <table className="table">
          <thead>
            <tr>
              <th>名称</th>
              <th>状态</th>
              <th>关键词</th>
              <th>平台</th>
              <th>间隔</th>
              <th>上次 / 下次</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id}>
                <td>
                  <strong>{t.name}</strong>
                  {t.last_error && (
                    <div className="muted" style={{ color: "var(--err)" }}>
                      {t.last_error}
                    </div>
                  )}
                </td>
                <td>
                  <span
                    className={`badge ${
                      t.status === "active" ? "ok" : t.status === "paused" ? "warn" : "err"
                    }`}
                  >
                    {t.status}
                  </span>
                </td>
                <td>{t.keywords.join(", ")}</td>
                <td>{t.platforms.join(", ")}</td>
                <td>{t.interval_seconds}s</td>
                <td className="muted">
                  <div>{t.last_checked_at ? new Date(t.last_checked_at).toLocaleString() : "-"}</div>
                  <div>{t.next_check_at ? new Date(t.next_check_at).toLocaleString() : "-"}</div>
                </td>
                <td>
                  <div className="toolbar">
                    <button className="btn" type="button" onClick={() => startEdit(t)}>
                      编辑
                    </button>
                    <button
                      className="btn"
                      type="button"
                      onClick={async () => {
                        const r = await api.tasks.run(t.id);
                        setMsg(`立即检查完成：新增 ${r.new_items}，错误 ${r.errors.length}`);
                        await reload();
                      }}
                    >
                      立即检查
                    </button>
                    {t.status === "paused" ? (
                      <button
                        className="btn"
                        type="button"
                        onClick={async () => {
                          await api.tasks.resume(t.id);
                          await reload();
                        }}
                      >
                        恢复
                      </button>
                    ) : (
                      <button
                        className="btn"
                        type="button"
                        onClick={async () => {
                          await api.tasks.pause(t.id);
                          await reload();
                        }}
                      >
                        暂停
                      </button>
                    )}
                    <button
                      className="btn danger"
                      type="button"
                      onClick={async () => {
                        if (!confirm("确认删除？")) return;
                        await api.tasks.remove(t.id);
                        await reload();
                      }}
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!tasks.length && <div className="muted">暂无任务</div>}
      </div>
    </div>
  );
}
