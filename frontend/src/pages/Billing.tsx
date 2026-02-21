import { useEffect, useState } from "react";
import api from "../api/client";

type Bill = {
    id: string;
    bill_number: string;
    table_id: string;
    subtotal: number;
    cgst_amount: number;
    sgst_amount: number;
    service_charge: number;
    discount: number;
    total: number;
    status: string;
    created_at: string;
};

function PayModal({ bill, onClose, onPaid }: { bill: Bill; onClose: () => void; onPaid: () => void }) {
    const [method, setMethod] = useState("CASH");
    const [amount, setAmount] = useState(String(bill.total));
    const [ref, setRef] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function pay() {
        setLoading(true);
        setError("");
        try {
            await api.post(`/billing/${bill.id}/pay`, {
                method,
                amount: parseFloat(amount),
                upi_reference_id: ref || null,
            });
            onPaid();
        } catch (e: any) {
            setError(e.response?.data?.detail || "Payment failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="card modal" onClick={(e) => e.stopPropagation()}>
                <h2 style={{ marginBottom: 20 }}>💳 Mark Payment — {bill.bill_number}</h2>

                <div style={{ background: "var(--bg-base)", borderRadius: 8, padding: "14px", marginBottom: 20 }}>
                    <div className="flex justify-between text-sm"><span className="text-muted">Subtotal</span><span>₹{Number(bill.subtotal).toFixed(2)}</span></div>
                    <div className="flex justify-between text-sm mt-1"><span className="text-muted">CGST</span><span>₹{Number(bill.cgst_amount).toFixed(2)}</span></div>
                    <div className="flex justify-between text-sm mt-1"><span className="text-muted">SGST</span><span>₹{Number(bill.sgst_amount).toFixed(2)}</span></div>
                    <div className="flex justify-between mt-2" style={{ borderTop: "1px solid var(--border)", paddingTop: 10 }}>
                        <span style={{ fontWeight: 700 }}>Total</span>
                        <span style={{ fontWeight: 800, color: "var(--green)", fontSize: "1.1rem" }}>₹{Number(bill.total).toFixed(2)}</span>
                    </div>
                </div>

                <div className="input-group">
                    <label className="input-label">Payment Method</label>
                    <select className="select" style={{ width: "100%" }} value={method} onChange={(e) => setMethod(e.target.value)}>
                        <option value="CASH">💵 Cash</option>
                        <option value="UPI">📱 UPI</option>
                        <option value="CARD">💳 Card</option>
                    </select>
                </div>
                <div className="input-group">
                    <label className="input-label">Amount Received</label>
                    <input className="input" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
                </div>
                {method !== "CASH" && (
                    <div className="input-group">
                        <label className="input-label">Reference / UTR</label>
                        <input className="input" type="text" placeholder="UPI ref / UTR number" value={ref} onChange={(e) => setRef(e.target.value)} />
                    </div>
                )}

                {error && <p style={{ color: "var(--red)", fontSize: "0.85rem", marginBottom: 12 }}>{error}</p>}

                <div className="flex gap-2">
                    <button className="btn btn-outline" onClick={onClose} style={{ flex: 1 }}>Cancel</button>
                    <button className="btn btn-success" onClick={pay} disabled={loading} style={{ flex: 1 }}>
                        {loading ? "Processing…" : "✅ Mark Paid"}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function Billing() {
    const [bills, setBills] = useState<Bill[]>([]);
    const [selected, setSelected] = useState<Bill | null>(null);
    const [loading, setLoading] = useState(true);

    async function fetchBills() {
        const staff = JSON.parse(localStorage.getItem("hd_staff") || "{}");
        if (!staff.branch_id) return;
        // We fetch branch tables then their open bills
        const tablesRes = await api.get(`/admin/tables?branch_id=${staff.branch_id}`);
        const allBills: Bill[] = [];
        for (const table of tablesRes.data) {
            try {
                const res = await api.get(`/billing/table/${table.id}/open`);
                allBills.push(...res.data);
            } catch { }
        }
        setBills(allBills);
        setLoading(false);
    }

    useEffect(() => { fetchBills(); }, []);

    if (loading) return <div className="text-muted">Loading bills…</div>;

    return (
        <div>
            <div className="page-header">
                <div>
                    <h1 className="page-title">Billing</h1>
                    <p className="page-sub">{bills.length} unpaid table(s)</p>
                </div>
                <button className="btn btn-outline btn-sm" onClick={fetchBills}>Refresh</button>
            </div>

            {bills.length === 0 && (
                <div className="card" style={{ textAlign: "center", padding: 40 }}>
                    <p style={{ fontSize: "2rem" }}>🎉</p>
                    <p className="text-muted mt-2">No unpaid bills right now.</p>
                </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
                {bills.map((bill) => (
                    <div key={bill.id} className="card" style={{ cursor: "pointer" }} onClick={() => setSelected(bill)}>
                        <div className="flex justify-between items-center">
                            <span style={{ fontWeight: 700, fontSize: "1.1rem" }}>{bill.bill_number}</span>
                            <span className="badge" style={{ background: "rgba(255,95,87,0.15)", color: "var(--red)" }}>UNPAID</span>
                        </div>
                        <div className="text-muted text-sm mt-1">Table: {bill.table_id.slice(-6)}</div>
                        <div style={{ marginTop: 16, borderTop: "1px solid var(--border)", paddingTop: 12 }}>
                            <div className="flex justify-between text-sm"><span className="text-muted">Subtotal</span><span>₹{Number(bill.subtotal).toFixed(2)}</span></div>
                            <div className="flex justify-between text-sm mt-1"><span className="text-muted">GST</span><span>₹{(Number(bill.cgst_amount) + Number(bill.sgst_amount)).toFixed(2)}</span></div>
                            <div className="flex justify-between mt-2" style={{ fontWeight: 800, fontSize: "1.1rem", color: "var(--green)" }}>
                                <span>Total</span><span>₹{Number(bill.total).toFixed(2)}</span>
                            </div>
                        </div>
                        <button className="btn btn-success" style={{ width: "100%", marginTop: 14, justifyContent: "center" }}>
                            💳 Mark as Paid
                        </button>
                    </div>
                ))}
            </div>

            {selected && (
                <PayModal bill={selected} onClose={() => setSelected(null)} onPaid={() => { setSelected(null); fetchBills(); }} />
            )}
        </div>
    );
}
