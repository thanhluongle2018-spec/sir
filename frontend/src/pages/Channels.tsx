import { FormEvent, useEffect, useState } from "react";
import { api, Channel } from "../api";

const TYPES = [
  { value: "telegram", label: "Telegram Bot", fields: ["bot_token", "chat_id"] },
  { value: "bark", label: "Bark", fields: ["device_key", "server"] },
  { value: "wecom", label: "企业微信机器人", fields: ["webhook_url"] },
  { value: "dingtalk", label: "钉钉机器人", fields: ["webhook_url", "secret"] },
  { value: "feishu", label: "飞书机器人", fields: ["webhook_url"] },
  { value: "email", label: "Email", fields: ["smtp_host", "smtp_port", "smtp_user", "smtp_password", "from", "to"] },
  { value: "webhook", label: "通用 Webhook", fields: ["url", "auth_header"] },
  { value: "wechat_mp", label: "微信推送 (PushPlus 等)", fields: ["token", "endpoint"] },
];

export default function Channels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [name, setName] = useState("");
  const [channelType, setChannelType] = useState("telegram");
  const [creds, setCreds] = useState<Record<string, string>>({});
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");

  const reload = () => api.channels.list().then(setChannels);

  useEffect(() => {
    reload().catch((e) => setError(String(e.message || e)));
  }, []);

  const fields = TYPES.find((t) => t.value === channelType)?.fields || [];

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      await api.channels.create({
        name,
        channel_type: channelType,
        enabled: true,
        credentials: creds,
        config: {},
      });
      setName("");
      setCreds({});
      setMsg("渠道已创建（凭证已加密存储）");
      await reload();
    } catch (err) {
      setError(String((err as Error).message || err));
    }
  };

  return (
    <div>
      <h1 className="page-title">通知渠道</h1>
      <p className="page-desc">
        煤炉 / 骏合屋监控的统一通知接口。凭证加密保存，支持测试发送与失败记录。
      </p>
      {error && <div className="error-box">{error}</div>}
      {msg && <div className="panel" style={{ color: "var(--ok)" }}>{msg}</div>}

      <div className="panel">
        <h2>添加渠道</h2>
        <form onSubmit={onSubmit}>
          <div className="form-grid">
            <label>
              名称
              <input required value={name} onChange={(e) => setName(e.target.value)} />
            </label>
            <label>
              类型
              <select
                value={channelType}
                onChange={(e) => {
                  setChannelType(e.target.value);
                  setCreds({});
                }}
              >
                {TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>
            {fields.map((f) => (
              <label key={f} className={f.includes("url") || f === "token" ? "full" : ""}>
                {f}
                <input
                  type={f.includes("password") || f.includes("token") || f.includes("secret") ? "password" : "text"}
                  value={creds[f] || ""}
                  onChange={(e) => setCreds({ ...creds, [f]: e.target.value })}
                  required={f !== "server" && f !== "auth_header" && f !== "secret" && f !== "endpoint"}
                />
              </label>
            ))}
          </div>
          <div className="toolbar" style={{ marginTop: 14 }}>
            <button className="btn primary" type="submit">
              保存
            </button>
          </div>
        </form>
      </div>

      <div className="panel">
        <h2>已配置渠道</h2>
        <table className="table">
          <thead>
            <tr>
              <th>名称</th>
              <th>类型</th>
              <th>启用</th>
              <th>凭证（脱敏）</th>
              <th>测试</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {channels.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.channel_type}</td>
                <td>
                  <span className={`badge ${c.enabled ? "ok" : "warn"}`}>
                    {c.enabled ? "on" : "off"}
                  </span>
                </td>
                <td className="muted">
                  <code>{JSON.stringify(c.credentials_masked)}</code>
                </td>
                <td>
                  {c.last_test_ok == null
                    ? "-"
                    : c.last_test_ok
                      ? "成功"
                      : `失败：${c.last_error || ""}`}
                </td>
                <td>
                  <div className="toolbar">
                    <button
                      className="btn"
                      type="button"
                      onClick={async () => {
                        const r = await api.channels.test(c.id);
                        setMsg(r.ok ? "测试发送成功" : `测试失败：${r.error}`);
                        await reload();
                      }}
                    >
                      测试发送
                    </button>
                    <button
                      className="btn"
                      type="button"
                      onClick={async () => {
                        await api.channels.update(c.id, { enabled: !c.enabled });
                        await reload();
                      }}
                    >
                      {c.enabled ? "禁用" : "启用"}
                    </button>
                    <button
                      className="btn danger"
                      type="button"
                      onClick={async () => {
                        if (!confirm("确认删除？")) return;
                        await api.channels.remove(c.id);
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
        {!channels.length && <div className="muted">暂无渠道</div>}
      </div>
    </div>
  );
}
