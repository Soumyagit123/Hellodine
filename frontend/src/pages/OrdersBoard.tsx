import { useEffect, useState, useRef } from "react";
import api from "../api/client";
import { formatDistanceToNow } from "date-fns";

const COLUMNS = [
    { status: "NEW", label: "🆕 New", color: "var(--blue)" },
    { status: "ACCEPTED", label: "✅ Accepted", color: "var(--yellow)" },
    { status: "PREPARING", label: "👨‍🍳 Preparing", color: "var(--orange)" },
    { status: "READY", label: "🔔 Ready", color: "var(--green)" },
    { status: "SERVED", label: "🍽️ Served", color: "var(--text-muted)" },
];

const NEXT_STATUS: Record<string, string> = {
    NEW: "ACCEPTED",
    ACCEPTED: "PREPARING",
    PREPARING: "READY",
    READY: "SERVED",
};

const STATUS_BTN: Record<string, string> = {
    NEW: "Accept",
    ACCEPTED: "Start Prep",
    PREPARING: "Mark Ready",
    READY: "Mark Served",
};

type Order = {
    id: string;
    order_number: string;
    table_id: string;
    status: string;
    total: number;
    created_at: string;
    items: { id: string; quantity: number; notes: string | null; menu_item_id: string }[];
};

function OrderCard({ order, onStatusChange }: { order: Order; onStatusChange: () => void }) {
    const [loading, setLoading] = useState(false);

    async function advance() {
        const next = NEXT_STATUS[order.status];
        if (!next) return;
        setLoading(true);
        try {
            await api.patch(`/orders/${order.id}/status`, { status: next });
            onStatusChange();
        } finally {
            setLoading(false);
        }
    }

    const elapsed = formatDistanceToNow(new Date(order.created_at), { addSuffix: false });
    const tableLabel = order.table_id?.slice(-4) ?? "—";

    return (
        <div className="order-card">
            <div className="flex items-center justify-between">
                <div className="order-card-table">T{tableLabel}</div>
                <span className={`badge badge-${order.status.toLowerCase()}`}>{order.status}</span>
            </div>
            <div className="order-card-info">#{order.order_number} · {elapsed} ago</div>

            <div className="order-card-items">
                {order.items.map((item) => (
                    <div key={item.id}>
                        <span>×{item.quantity}</span>{" "}
                        <span style={{ color: "var(--text)" }}>{item.menu_item_id.slice(0, 8)}…</span>
                        {item.notes && (
                            <div className="order-card-note mt-1">📝 {item.notes}</div>
                        )}
                    </div>
                ))}
            </div>

            <div className="order-card-footer">
                <span className="text-muted text-sm">₹{Number(order.total).toFixed(2)}</span>
                {NEXT_STATUS[order.status] && (
                    <button className="btn btn-sm btn-primary" onClick={advance} disabled={loading}>
                        {loading ? "…" : STATUS_BTN[order.status]}
                    </button>
                )}
            </div>
        </div>
    );
}

export default function OrdersBoard() {
    const [orders, setOrders] = useState<Order[]>([]);
    const [branchId, setBranchId] = useState<string>("");
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const staff = JSON.parse(localStorage.getItem("hd_staff") || "{}");
        if (staff.branch_id) {
            setBranchId(staff.branch_id);
        }
    }, []);

    async function fetchOrders() {
        if (!branchId) return;
        const res = await api.get(`/orders?branch_id=${branchId}`);
        setOrders(res.data);
    }

    useEffect(() => {
        if (!branchId) return;
        fetchOrders();

        // WebSocket for realtime updates (Hardcoded for Production)
        const wsUrl = `wss://hellodine-api.onrender.com/api/orders/ws/kitchen/${branchId}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = () => fetchOrders(); // Refresh on any event
        ws.onclose = () => setTimeout(() => fetchOrders(), 3000);

        const interval = setInterval(fetchOrders, 15000); // Fallback polling
        return () => {
            ws.close();
            clearInterval(interval);
        };
    }, [branchId]);

    const activeOrders = orders.filter((o) => o.status !== "SERVED" && o.status !== "CANCELLED");

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Kitchen Board</h1>
                    <p className="page-sub">{activeOrders.length} active orders</p>
                </div>
                <div className="flex gap-2">
                    <div className="pulse" style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--green)", margin: "auto 0" }} />
                    <span className="text-sm text-muted">Live</span>
                    <button className="btn btn-outline btn-sm" onClick={fetchOrders}>Refresh</button>
                </div>
            </div>

            <div className="kanban">
                {COLUMNS.map((col) => {
                    const colOrders = orders.filter((o) => o.status === col.status);
                    return (
                        <div key={col.status} className="kanban-col">
                            <div className="kanban-col-header">
                                <span style={{ color: col.color }}>{col.label}</span>
                                <span style={{ background: col.color, color: "#0f0f1a", borderRadius: "999px", padding: "1px 8px", fontSize: "0.75rem", fontWeight: 700 }}>
                                    {colOrders.length}
                                </span>
                            </div>
                            <div className="kanban-col-body">
                                {colOrders.length === 0 && (
                                    <p className="text-muted text-sm" style={{ textAlign: "center", marginTop: 20 }}>No orders</p>
                                )}
                                {colOrders.map((o) => (
                                    <OrderCard key={o.id} order={o} onStatusChange={fetchOrders} />
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
