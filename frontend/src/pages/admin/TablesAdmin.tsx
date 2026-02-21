import { useEffect, useState } from "react";
import api from "../../api/client";
import { QRCodeCanvas } from "qrcode.react";

export default function TablesAdmin() {
    const [tables, setTables] = useState<any[]>([]);
    const [branchId, setBranchId] = useState<string>("");
    const [newNum, setNewNum] = useState("");
    const [qrResult, setQrResult] = useState<{ table_number: number; wa_link: string } | null>(null);

    useEffect(() => {
        const staff = JSON.parse(localStorage.getItem("hd_staff") || "{}");
        if (staff.branch_id) {
            setBranchId(staff.branch_id);
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

    useEffect(() => {
        if (!branchId) return;
        api.get(`/admin/tables?branch_id=${branchId}`).then((r) => setTables(r.data));
    }, [branchId]);

    async function addTable() {
        if (!newNum) return;
        await api.post("/admin/tables", { branch_id: branchId, table_number: parseInt(newNum) });
        setNewNum("");
        const r = await api.get(`/admin/tables?branch_id=${branchId}`);
        setTables(r.data);
    }

    async function generateQR(tableId: string) {
        const r = await api.post(`/admin/tables/${tableId}/qr`);
        setQrResult(r.data);
    }

    return (
        <div>
            <div className="page-header">
                <div><h1 className="page-title">Tables</h1><p className="page-sub">{tables.length} tables configured</p></div>
            </div>

            <div className="flex gap-2 mb-3">
                <input className="input" style={{ maxWidth: 160 }} type="number" placeholder="Table number" value={newNum} onChange={(e) => setNewNum(e.target.value)} />
                <button className="btn btn-primary" onClick={addTable}>+ Add Table</button>
            </div>

            <div className="card table-wrap">
                <table>
                    <thead><tr><th>Table #</th><th>ID</th><th>Active</th><th>QR</th></tr></thead>
                    <tbody>
                        {tables.map((t) => (
                            <tr key={t.id}>
                                <td style={{ fontWeight: 700, fontSize: "1.1rem" }}>T{t.table_number}</td>
                                <td className="text-muted text-sm">{t.id.slice(0, 8)}…</td>
                                <td><span style={{ color: t.is_active ? "var(--green)" : "var(--red)" }}>{t.is_active ? "Active" : "Inactive"}</span></td>
                                <td><button className="btn btn-outline btn-sm" onClick={() => generateQR(t.id)}>🔗 Generate QR</button></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {qrResult && (
                <div className="modal-overlay" onClick={() => setQrResult(null)}>
                    <div className="card modal" onClick={(e) => e.stopPropagation()}>
                        <h2 style={{ marginBottom: 16 }}>✅ QR Generated — Table {qrResult.table_number}</h2>
                        <p className="text-muted text-sm" style={{ marginBottom: 12 }}>Share this WhatsApp link with the customer or print it as a QR code:</p>

                        <div style={{ display: "flex", justifyContent: "center", marginBottom: 16, background: "white", padding: 16, borderRadius: 8 }}>
                            <QRCodeCanvas
                                id="qr-canvas"
                                value={qrResult.wa_link}
                                size={200}
                                level="H"
                                includeMargin={true}
                            />
                        </div>

                        <div className="flex gap-2" style={{ marginBottom: 16, justifyContent: "center" }}>
                            <button className="btn btn-outline" onClick={() => {
                                const canvas = document.getElementById("qr-canvas") as HTMLCanvasElement;
                                if (canvas) {
                                    const a = document.createElement("a");
                                    a.href = canvas.toDataURL("image/png");
                                    a.download = `Table-${qrResult.table_number}-QR.png`;
                                    a.click();
                                }
                            }}>
                                ⬇️ Download Image
                            </button>
                            <a className="btn btn-primary" href={qrResult.wa_link} target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", textDecoration: "none" }}>
                                Open in WhatsApp
                            </a>
                        </div>

                        <div style={{ background: "var(--bg-base)", padding: 12, borderRadius: 8, wordBreak: "break-all", fontSize: "0.8rem", color: "var(--green)", marginBottom: 16 }}>
                            {qrResult.wa_link}
                        </div>

                        <div style={{ textAlign: "center" }}>
                            <button className="btn btn-outline" onClick={() => setQrResult(null)}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
