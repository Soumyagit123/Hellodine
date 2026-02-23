import { useEffect, useState } from "react";
import api from "../../api/client";
import { format } from "date-fns";

export default function DailyReport() {
    const [date, setDate] = useState(format(new Date(), "yyyy-MM-dd"));
    const [report, setReport] = useState<any>(null);
    const [branchId, setBranchId] = useState<string>("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const s = JSON.parse(localStorage.getItem("hd_staff") || "{}");
        const selectedBranchId = localStorage.getItem("hd_selected_branch");

        if (s.branch_id) {
            setBranchId(s.branch_id);
        } else if (selectedBranchId) {
            setBranchId(selectedBranchId);
        } else {
            const token = localStorage.getItem("hd_token");
            if (token) {
                try {
                    const payload = JSON.parse(atob(token.split(".")[1]));
                    if (payload.restaurant_id) {
                        api.get(`/admin/branches?restaurant_id=${payload.restaurant_id}`).then((r) => {
                            if (r.data.length > 0) setBranchId(r.data[0].id);
                        });
                    }
                } catch { }
            }
        }
    }, []);

    async function fetchReport() {
        if (!branchId) return;
        setLoading(true);
        try {
            const r = await api.get(`/billing/report/daily?branch_id=${branchId}&date=${date}`);
            setReport(r.data);
        } finally { setLoading(false); }
    }

    useEffect(() => { if (branchId) fetchReport(); }, [branchId, date]);

    return (
        <div>
            <div className="page-header">
                <div><h1 className="page-title">Daily Report</h1></div>
                <input className="input" type="date" value={date} onChange={(e) => setDate(e.target.value)} style={{ width: 180 }} />
            </div>

            {loading && <p className="text-muted">Loading…</p>}

            {report && (
                <>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--accent)" }}>{report.total_bills}</div>
                            <div className="stat-label">Total Bills</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--green)" }}>₹{Number(report.total_revenue).toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
                            <div className="stat-label">Total Revenue</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--blue)" }}>₹{Number(report.total_cgst).toFixed(2)}</div>
                            <div className="stat-label">CGST Collected</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: "var(--yellow)" }}>₹{Number(report.total_sgst).toFixed(2)}</div>
                            <div className="stat-label">SGST Collected</div>
                        </div>
                    </div>

                    <div className="card">
                        <h3 style={{ marginBottom: 16 }}>GST Summary — {date}</h3>
                        <table style={{ width: "100%" }}>
                            <tbody>
                                <tr><td className="text-muted">Taxable Amount (Subtotal)</td><td style={{ textAlign: "right", fontWeight: 600 }}>₹{(Number(report.total_revenue) - Number(report.total_cgst) - Number(report.total_sgst)).toFixed(2)}</td></tr>
                                <tr><td className="text-muted">CGST (9%)</td><td style={{ textAlign: "right", fontWeight: 600 }}>₹{Number(report.total_cgst).toFixed(2)}</td></tr>
                                <tr><td className="text-muted">SGST (9%)</td><td style={{ textAlign: "right", fontWeight: 600 }}>₹{Number(report.total_sgst).toFixed(2)}</td></tr>
                                <tr style={{ borderTop: "1px solid var(--border)" }}>
                                    <td style={{ fontWeight: 700, paddingTop: 12 }}>Total Revenue</td>
                                    <td style={{ textAlign: "right", fontWeight: 800, color: "var(--green)", fontSize: "1.1rem", paddingTop: 12 }}>₹{Number(report.total_revenue).toFixed(2)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </>
            )}
        </div>
    );
}
