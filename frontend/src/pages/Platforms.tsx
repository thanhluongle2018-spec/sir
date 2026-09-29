import { useEffect, useState } from "react";
import { api, PlatformInfo } from "../api";

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
        各平台独立适配器。仅接入允许使用的数据源；占位平台不会伪造“已支持”。
      </p>
      {error && <div className="error-box">{error}</div>}
      {platforms.map((p) => (
        <div className="panel" key={p.code}>
          <h2>
            {p.name_ja}{" "}
            <span
              className={`badge ${
                p.status === "supported" ? "ok" : p.status === "partial" ? "warn" : "err"
              }`}
            >
              {p.status}
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
              <span>配置说明</span>
              <span>{p.config_notes}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
