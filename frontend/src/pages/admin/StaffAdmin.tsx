import { useEffect, useState } from "react";
import api from "../../api/client";

const ROLES = ["KITCHEN", "CASHIER", "BRANCH_ADMIN", "SUPER_ADMIN"];

export default function StaffAdmin() {
    const [staff, setStaff] = useState<any[]>([]);
    const [restaurantId, setRestaurantId] = useState<string>("");
    const [branchId, setBranchId] = useState<string>("");
    const [showNew, setShowNew] = useState(false);
    const [form, setForm] = useState({ name: "", phone: "", password: "", role: "KITCHEN" });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        let rId = "";
        const token = localStorage.getItem("hd_token");
        if (token) {
            try {
                const payload = JSON.parse(atob(token.split(".")[1]));
                rId = payload.restaurant_id || "";
                setRestaurantId(rId);
            } catch { }
        }
        const s = JSON.parse(localStorage.getItem("hd_staff") || "{}");
        const selectedBranchId = localStorage.getItem("hd_selected_branch");

        if (s.branch_id) {
            setBranchId(s.branch_id);
        } else if (selectedBranchId) {
            setBranchId(selectedBranchId);
        } else if (rId) {
            api.get(`/admin/branches?restaurant_id=${rId}`).then((r) => {
                if (r.data.length > 0) setBranchId(r.data[0].id);
            });
        }
    }, []);

    useEffect(() => {
        if (!restaurantId) return;
        api.get(`/admin/staff?restaurant_id=${restaurantId}`).then((r) => setStaff(r.data));
    }, [restaurantId]);

    async function createStaff() {
        setLoading(true);
        try {
            await api.post("/admin/staff", { ...form, restaurant_id: restaurantId, branch_id: branchId || null });
            setShowNew(false); setForm({ name: "", phone: "", password: "", role: "KITCHEN" });
            const r = await api.get(`/admin/staff?restaurant_id=${restaurantId}`);
            setStaff(r.data);
        } finally { setLoading(false); }
    }

    async function deactivate(id: string) {
        await api.patch(`/admin/staff/${id}/deactivate`);
        const r = await api.get(`/admin/staff?restaurant_id=${restaurantId}`);
        setStaff(r.data);
    }

    const roleColor: Record<string, string> = { SUPER_ADMIN: "var(--accent)", BRANCH_ADMIN: "var(--blue)", KITCHEN: "var(--orange)", CASHIER: "var(--green)" };

    return (
        <div>
            <div className="page-header">
                <div><h1 className="page-title">Staff Management</h1><p className="page-sub">{staff.length} staff members</p></div>
                <button className="btn btn-primary btn-sm" onClick={() => setShowNew(true)}>+ Add Staff</button>
            </div>

            <div className="card table-wrap">
                <table>
                    <thead><tr><th>Name</th><th>Phone</th><th>Role</th><th>Status</th><th></th></tr></thead>
                    <tbody>
                        {staff.map((s) => (
                            <tr key={s.id}>
                                <td style={{ fontWeight: 600 }}>{s.name}</td>
                                <td className="text-muted">{s.phone}</td>
                                <td><span className="badge" style={{ background: `${roleColor[s.role]}22`, color: roleColor[s.role] }}>{s.role}</span></td>
                                <td><span style={{ color: s.is_active ? "var(--green)" : "var(--red)" }}>{s.is_active ? "Active" : "Inactive"}</span></td>
                                <td>{s.is_active && <button className="btn btn-outline btn-sm" onClick={() => deactivate(s.id)}>Deactivate</button>}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {showNew && (
                <div className="modal-overlay" onClick={() => setShowNew(false)}>
                    <div className="card modal" onClick={(e) => e.stopPropagation()}>
                        <h2 style={{ marginBottom: 20 }}>New Staff Member</h2>
                        <div className="input-group"><label className="input-label">Full Name</label><input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
                        <div className="input-group"><label className="input-label">Phone</label><input className="input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
                        <div className="input-group"><label className="input-label">Password / PIN</label><input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></div>
                        <div className="input-group">
                            <label className="input-label">Role</label>
                            <select className="select" style={{ width: "100%" }} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                                {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>
                        <div className="flex gap-2">
                            <button className="btn btn-outline" onClick={() => setShowNew(false)}>Cancel</button>
                            <button className="btn btn-primary" onClick={createStaff} disabled={loading}>{loading ? "Creating…" : "Create Staff"}</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
