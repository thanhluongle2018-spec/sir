import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Tasks from "./pages/Tasks";
import Items from "./pages/Items";
import Channels from "./pages/Channels";
import Platforms from "./pages/Platforms";
import Logs from "./pages/Logs";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1 className="brand">
          SIR <span>Monitor</span>
        </h1>
        <div className="brand-sub">煤炉 · 骏合屋上新监控</div>
        <nav className="nav">
          <NavLink to="/" end>
            总览
          </NavLink>
          <NavLink to="/tasks">监控任务</NavLink>
          <NavLink to="/items">商品</NavLink>
          <NavLink to="/channels">通知渠道</NavLink>
          <NavLink to="/platforms">平台接入</NavLink>
          <NavLink to="/logs">运行日志</NavLink>
        </nav>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/items" element={<Items />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/platforms" element={<Platforms />} />
          <Route path="/logs" element={<Logs />} />
        </Routes>
      </main>
    </div>
  );
}
