import { useEffect, useState } from "react";
import { api, DataSourceInfo, PlatformInfo } from "../api";

function dsStatusClass(status: string): string {
  if (status === "available") return "ok";
  if (status === "pending_confirmation") return "warn";
  return "err";
}

export default function Platforms() {
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [sources, setSources] = useState<DataSourceInfo[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.platforms(), api.datasources()])
      .then(([p, d]) => {
        setPlatforms(p);
        setSources(d);
      })
      .catch((e) => setError(String(e.message || e)));
  }, []);

  return (
    <div>
      <h1 className="page-title">平台与数据源</h1>
      <p className="page-desc">
        监控管道（任务 / 去重 / 通知）已就绪。煤炉与骏合屋商品数据源尚未形成可监控链路——界面显示「当前不能监控」，不会伪造抓取成功。
      </p>
      {error && <div className="error-box">{error}</div>}

      <div className="panel" style={{ borderColor: "rgba(161, 92, 0, 0.35)" }}>
        <h2>重要说明</h2>
        <p className="muted" style={{ margin: 0, lineHeight: 1.6 }}>
          不会绕过 401 / 403 / Cloudflare / 登录 / 验证码。官方邮件提醒仅评估经用户 OAuth
          只读接入，不保存邮箱密码。用户入库接口用于主动提交有权使用的数据。
        </p>
      </div>

      {platforms.map((p) => (
        <div className="panel" key={p.code}>
          <h2>
            {p.name_ja}{" "}
            <span className={`badge ${p.can_monitor ? "ok" : "err"}`}>
              {p.status_label || (p.can_monitor ? "可监控" : "当前不能监控")}
            </span>
          </h2>
          <div className="kv">
            <div className="kv-row">
              <span>代码</span>
              <strong>{p.code}</strong>
            </div>
            <div className="kv-row">
              <span>数据来源策略</span>
              <span>{p.data_source}</span>
            </div>
            <div className="kv-row">
              <span>限制</span>
              <span>{p.limitations.join("； ") || "—"}</span>
            </div>
            <div className="kv-row">
              <span>说明</span>
              <span>{p.config_notes}</span>
            </div>
          </div>
        </div>
      ))}

      <div className="panel">
        <h2>可插拔数据源清单</h2>
        <table className="table">
          <thead>
            <tr>
              <th>数据源</th>
              <th>平台</th>
              <th>类型</th>
              <th>状态</th>
              <th>摘要</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id}>
                <td>
                  <strong>{s.name_zh}</strong>
                  <div className="muted">{s.id}</div>
                </td>
                <td>{s.platform}</td>
                <td>{s.kind}</td>
                <td>
                  <span className={`badge ${dsStatusClass(s.status)}`}>
                    {s.status_label || s.status}
                  </span>
                </td>
                <td>
                  <div>{s.summary}</div>
                  {!!s.research_notes?.length && (
                    <ul className="muted" style={{ margin: "8px 0 0", paddingLeft: 18 }}>
                      {s.research_notes.map((n) => (
                        <li key={n.slice(0, 24)}>{n}</li>
                      ))}
                    </ul>
                  )}
                  {!!s.requirements?.length && (
                    <div className="muted" style={{ marginTop: 6 }}>
                      接入条件：{s.requirements.join("； ")}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
