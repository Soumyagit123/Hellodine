import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, NavLink, useNavigate } from "react-router-dom";
import Login from "./pages/Login";
import OrdersBoard from "./pages/OrdersBoard";
import Billing from "./pages/Billing";
import MenuAdmin from "./pages/admin/MenuAdmin";
import TablesAdmin from "./pages/admin/TablesAdmin";
import StaffAdmin from "./pages/admin/StaffAdmin";
import DailyReport from "./pages/admin/DailyReport";
import BranchAdmin from "./pages/admin/BranchAdmin";
import SystemAdmin from "./pages/admin/SystemAdmin";

function isLoggedIn() {
    return !!localStorage.getItem("hd_token");
}

function getRole() {
    try {
        const s = JSON.parse(localStorage.getItem("hd_staff") || "{}");
        return s.role || "";
    } catch {
        return "";
    }
}

function Sidebar({ hideSidebar }: { hideSidebar: () => void }) {
    const navigate = useNavigate();
    const role = getRole();

    function logout() {
        localStorage.clear();
        navigate("/login");
    }

    return (
        <aside className="sidebar">
            <div className="logo">
                <div className="logo-dot" />
                HelloDine
            </div>

            <NavLink to="/orders" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>
                🍽️ Orders
            </NavLink>

            {(role === "CASHIER" || role === "BRANCH_ADMIN" || role === "SUPER_ADMIN") && (
                <NavLink to="/billing" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>
                    💰 Billing
                </NavLink>
            )}

            {(role === "BRANCH_ADMIN" || role === "SUPER_ADMIN") && (
                <>
                    <div style={{ margin: "16px 0 8px", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)", padding: "0 14px" }}>
                        Admin
                    </div>
                    <NavLink to="/admin/menu" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>📋 Menu</NavLink>
                    <NavLink to="/admin/tables" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>🪑 Tables</NavLink>
                    <NavLink to="/admin/staff" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>👤 Staff</NavLink>
                    <NavLink to="/admin/report" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>📊 Daily Report</NavLink>
                    <NavLink to="/admin/branches" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>🏘️ Branches</NavLink>
                </>
            )}

            {role === "SYSTEM_ADMIN" && (
                <>
                    <div style={{ margin: "16px 0 8px", fontSize: "0.72rem", textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--accent)", padding: "0 14px" }}>
                        Provider
                    </div>
                    <NavLink to="/system" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`} onClick={hideSidebar}>🌐 System Dashboard</NavLink>
                </>
            )}

            <div style={{ flex: 1 }} />

            <button className="nav-link" onClick={logout} style={{ color: "var(--red)" }}>
                🚪 Logout
            </button>
        </aside>
    );
}

function ProtectedLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    if (!isLoggedIn()) return <Navigate to="/login" replace />;

    return (
        <div className="app-shell">
            <div className={`sidebar-overlay ${sidebarOpen ? "show" : ""}`} onClick={() => setSidebarOpen(false)} />
            <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
                <Sidebar hideSidebar={() => setSidebarOpen(false)} />
            </aside>
            <main className="main-content">
                <header className="mobile-header">
                    <button className="menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>
                    <div className="logo-text">HelloDine</div>
                </header>
                <Routes>
                    <Route path="/orders" element={<OrdersBoard />} />
                    <Route path="/billing" element={<Billing />} />
                    <Route path="/admin/menu" element={<MenuAdmin />} />
                    <Route path="/admin/tables" element={<TablesAdmin />} />
                    <Route path="/admin/staff" element={<StaffAdmin />} />
                    <Route path="/admin/report" element={<DailyReport />} />
                    <Route path="/admin/branches" element={<BranchAdmin />} />
                    <Route path="/system" element={<SystemAdmin />} />
                    <Route path="*" element={<Navigate to="/orders" replace />} />
                </Routes>
            </main>
        </div>
    );
}

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/*" element={<ProtectedLayout />} />
            </Routes>
        </BrowserRouter>
    );
}
