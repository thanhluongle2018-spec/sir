import { useEffect, useMemo, useState } from "react";
import { api, DashboardStats, StatsCharts } from "../api";

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [charts, setCharts] = useState<StatsCharts | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.dashboard(), api.charts()])
      .then(([s, c]) => {
        setStats(s);
        setCharts(c);
      })
      .catch((e) => setError(String(e.message || e)));
  }, []);

  const maxDaily = useMemo(
    () => Math.max(1, ...(charts?.daily.map((d) => d.count) || [1])),
    [charts]
  );

  return (
    <div>
      <h1 className="page-title">总览</h1>
      <p className="page-desc">
        监控与通知聚合已就绪；煤炉 / 骏合屋商品数据源尚未接入，任务不会发现真实平台商品。
      </p>
      <div className="error-box" style={{ background: "rgba(161, 92, 0, 0.08)", borderColor: "rgba(161, 92, 0, 0.3)", color: "var(--warn)" }}>
        当前不能监控真实煤炉 / 骏合屋商品。请到「平台接入」查看可插拔数据源状态；不会使用演示数据冒充结果。
      </div>
      {error && <div className="error-box">{error}</div>}
      {stats && (
        <div className="grid-stats">
          <div className="stat">
            <div className="label">监控任务</div>
            <div className="value">{stats.task_total}</div>
            <div className="muted">
              运行 {stats.task_active} · 暂停 {stats.task_paused}
            </div>
          </div>
          <div className="stat">
            <div className="label">今日发现</div>
            <div className="value">{stats.items_today}</div>
            <div className="muted">累计 {stats.items_total}</div>
          </div>
          <div className="stat">
            <div className="label">通知成功</div>
            <div className="value">{stats.notifications_success}</div>
          </div>
          <div className="stat">
            <div className="label">通知失败</div>
            <div className="value">{stats.notifications_failed}</div>
            <div className="muted">待发送 {stats.notifications_pending}</div>
          </div>
        </div>
      )}

      <div className="panel">
        <h2>近 14 天发现量</h2>
        <div className="chart-bars">
          {(charts?.daily || []).map((d) => (
            <div className="bar-wrap" key={d.date}>
              <div
                className="bar"
                style={{ height: `${Math.max(6, (d.count / maxDaily) * 100)}%` }}
                title={`${d.date}: ${d.count}`}
              />
              <div className="bar-label">{d.date.slice(5)}</div>
            </div>
          ))}
          {!charts?.daily?.length && <div className="muted">暂无数据</div>}
        </div>
      </div>

      <div className="panel">
        <h2>各平台商品数</h2>
        <div className="kv">
          {Object.entries(stats?.items_by_platform || {}).map(([k, v]) => (
            <div className="kv-row" key={k}>
              <span>{k}</span>
              <strong>{v}</strong>
            </div>
          ))}
          {!Object.keys(stats?.items_by_platform || {}).length && (
            <div className="muted">暂无数据</div>
          )}
        </div>
      </div>

      <div className="panel">
        <h2>关键词命中</h2>
        <div className="kv">
          {Object.entries(charts?.by_keyword || {})
            .sort((a, b) => b[1] - a[1])
            .slice(0, 12)
            .map(([k, v]) => (
              <div className="kv-row" key={k}>
                <span>{k}</span>
                <strong>{v}</strong>
              </div>
            ))}
          {!Object.keys(charts?.by_keyword || {}).length && (
            <div className="muted">暂无数据</div>
          )}
        </div>
      </div>
    </div>
  );
}
