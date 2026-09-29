import { useEffect, useState } from "react";
import { api, RunLog } from "../api";

export default function Logs() {
  const [runs, setRuns] = useState<RunLog[]>([]);
  const [notifs, setNotifs] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.logs.runs(), api.logs.notifications()])
      .then(([r, n]) => {
        setRuns(r);
        setNotifs(n);
      })
      .catch((e) => setError(String(e.message || e)));
  }, []);

  return (
    <div>
      <h1 className="page-title">运行日志</h1>
      <p className="page-desc">任务运行状态与通知发送记录，便于排查平台接入问题。</p>
      {error && <div className="error-box">{error}</div>}

      <div className="panel">
        <h2>监控运行日志</h2>
        <table className="table">
          <thead>
            <tr>
              <th>时间</th>
              <th>级别</th>
              <th>任务</th>
              <th>平台</th>
              <th>消息</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td className="muted">{new Date(r.created_at).toLocaleString()}</td>
                <td>
                  <span
                    className={`badge ${
                      r.level === "error" ? "err" : r.level === "warning" ? "warn" : "ok"
                    }`}
                  >
                    {r.level}
                  </span>
                </td>
                <td>{r.task_id ?? "-"}</td>
                <td>{r.platform ?? "-"}</td>
                <td>{r.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!runs.length && <div className="muted">暂无日志</div>}
      </div>

      <div className="panel">
        <h2>通知发送记录</h2>
        <table className="table">
          <thead>
            <tr>
              <th>时间</th>
              <th>状态</th>
              <th>渠道</th>
              <th>商品</th>
              <th>尝试</th>
              <th>错误</th>
            </tr>
          </thead>
          <tbody>
            {notifs.map((n) => (
              <tr key={n.id}>
                <td className="muted">{new Date(n.created_at).toLocaleString()}</td>
                <td>
                  <span
                    className={`badge ${
                      n.status === "success" ? "ok" : n.status === "failed" ? "err" : "warn"
                    }`}
                  >
                    {n.status}
                  </span>
                </td>
                <td>{n.channel_id}</td>
                <td>{n.item_id ?? "-"}</td>
                <td>{n.attempts}</td>
                <td className="muted">{n.error || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!notifs.length && <div className="muted">暂无记录</div>}
      </div>
    </div>
  );
}
