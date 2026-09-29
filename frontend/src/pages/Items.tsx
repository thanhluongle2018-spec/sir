import { useEffect, useState } from "react";
import { api, Item, PlatformInfo } from "../api";

export default function ItemsPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [platforms, setPlatforms] = useState<PlatformInfo[]>([]);
  const [q, setQ] = useState("");
  const [platform, setPlatform] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [isRead, setIsRead] = useState("");
  const [error, setError] = useState("");

  const load = () =>
    api.items
      .list({
        q: q || undefined,
        platform: platform || undefined,
        min_price: minPrice || undefined,
        max_price: maxPrice || undefined,
        is_read: isRead === "" ? undefined : isRead === "1",
      })
      .then(setItems);

  useEffect(() => {
    api.platforms().then(setPlatforms).catch(() => undefined);
    load().catch((e) => setError(String(e.message || e)));
  }, []);

  return (
    <div>
      <h1 className="page-title">商品</h1>
      <p className="page-desc">已发现商品列表，支持搜索、平台与价格筛选，以及已读标记。</p>
      {error && <div className="error-box">{error}</div>}

      <div className="panel">
        <div className="toolbar">
          <input
            placeholder="搜索标题"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <select value={platform} onChange={(e) => setPlatform(e.target.value)}>
            <option value="">全部平台</option>
            {platforms.map((p) => (
              <option key={p.code} value={p.code}>
                {p.name_ja}
              </option>
            ))}
          </select>
          <input
            type="number"
            placeholder="最低价"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            style={{ width: 110 }}
          />
          <input
            type="number"
            placeholder="最高价"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            style={{ width: 110 }}
          />
          <select value={isRead} onChange={(e) => setIsRead(e.target.value)}>
            <option value="">全部状态</option>
            <option value="0">未读</option>
            <option value="1">已读</option>
          </select>
          <button
            className="btn primary"
            type="button"
            onClick={() => load().catch((e) => setError(String(e.message || e)))}
          >
            筛选
          </button>
        </div>
      </div>

      <div className="item-list">
        {items.map((item) => (
          <article className="item" key={item.id}>
            {item.image_url ? (
              <img src={item.image_url} alt="" loading="lazy" />
            ) : (
              <div style={{ aspectRatio: 1, background: "#dfe8ea" }} />
            )}
            <div className="body">
              <div className="title">{item.title}</div>
              <div className="price">
                {item.price != null
                  ? `¥${Number(item.price).toLocaleString()} ${item.currency}`
                  : "价格未知"}
              </div>
              <div className="muted">
                {item.platform} · {item.seller || "卖家未知"}
                {!item.is_read && (
                  <span className="badge warn" style={{ marginLeft: 6 }}>
                    未读
                  </span>
                )}
              </div>
              <div className="muted">
                发现于 {new Date(item.discovered_at).toLocaleString()}
              </div>
              {!!item.matched_keywords?.length && (
                <div className="muted">匹配：{item.matched_keywords.join(", ")}</div>
              )}
              <div className="toolbar">
                <a className="btn primary" href={item.url} target="_blank" rel="noreferrer">
                  打开商品
                </a>
                {!item.is_read && (
                  <button
                    className="btn"
                    type="button"
                    onClick={async () => {
                      await api.items.markRead(item.id);
                      await load();
                    }}
                  >
                    标为已读
                  </button>
                )}
              </div>
            </div>
          </article>
        ))}
      </div>
      {!items.length && <div className="muted">暂无商品</div>}
    </div>
  );
}
