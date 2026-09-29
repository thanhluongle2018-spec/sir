import { useEffect, useState } from "react";
import { api, PlatformInfo } from "../api";

function statusLabel(status: string): string {
  if (status === "supported") return "已接入";
  if (status === "partial") return "部分接入";
  if (status === "unavailable" || status === "stub") return "未接入";
  return status;
}

function statusClass(status: string): string {
  if (status === "supported") return "ok";
  if (status === "partial") return "warn";
  return "err";
}

export default function Platforms() {
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.platforms()
      .then(setPlatforms)
      .catch((e) => setError(String(e.message || e)));
  }, []);

  return (
    <div>
      <h1 className="page-title">平台接入</h1>
      <p className="page-desc">
        本版本目标平台仅为煤炉与骏合屋，各自独立适配器维护。仅在存在允许使用且稳定的数据源时接入；未接入平台不会伪造抓取成功。
      </p>
      {error && <div className="error-box">{error}</div>}
      {platforms.map((p) => (
        <div className="panel" key={p.code}>
          <h2>
            {p.name_ja}{" "}
            <span className={`badge ${statusClass(p.status)}`}>
              {statusLabel(p.status)}
            </span>
          </h2>
          <div className="kv">
            <div className="kv-row">
              <span>代码</span>
              <strong>{p.code}</strong>
            </div>
            <div className="kv-row">
              <span>数据来源</span>
              <span>{p.data_source}</span>
            </div>
            <div className="kv-row">
              <span>能力</span>
              <span>{p.capabilities.join(", ") || "—"}</span>
            </div>
            <div className="kv-row">
              <span>限制</span>
              <span>{p.limitations.join("； ") || "—"}</span>
            </div>
            <div className="kv-row">
              <span>后续接入条件</span>
              <span>{p.config_notes}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
