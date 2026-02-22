import { useState, useEffect } from "react";
import client from "../../api/client";

interface Restaurant {
    id: string;
    name: string;
    whatsapp_phone_number_id: string;
    whatsapp_display_number: string;
    whatsapp_access_token?: string;
    whatsapp_verify_token?: string;
    max_branches: number;
    is_active: boolean;
    created_at: string;
}

export default function SystemAdmin() {
    const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [editTarget, setEditTarget] = useState<Restaurant | null>(null);
    const [resetTarget, setResetTarget] = useState<Restaurant | null>(null);
    const [newPass, setNewPass] = useState("");
    const [formData, setFormData] = useState({
        name: "",
        whatsapp_phone_number_id: "",
        whatsapp_display_number: "",
        whatsapp_access_token: "",
        whatsapp_verify_token: "hellodine",
        max_branches: 1,
        owner_phone: "",
        owner_password: ""
    });

    useEffect(() => {
        fetchRestaurants();
    }, []);

    const fetchRestaurants = async () => {
        try {
            const res = await client.get("/admin/restaurants");
            setRestaurants(res.data);
        } catch (err) {
            console.error("Failed to fetch restaurants", err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            // 1. Create Restaurant
            const restRes = await client.post("/admin/restaurants", {
                name: formData.name,
                whatsapp_phone_number_id: formData.whatsapp_phone_number_id,
                whatsapp_display_number: formData.whatsapp_display_number,
                whatsapp_access_token: formData.whatsapp_access_token,
                whatsapp_verify_token: formData.whatsapp_verify_token,
                max_branches: formData.max_branches
            });

            const restaurantId = restRes.data.id;

            // 2. Create Owner Account (SUPER_ADMIN)
            await client.post("/admin/staff", {
                restaurant_id: restaurantId,
                role: "SUPER_ADMIN",
                name: `${formData.name} Owner`,
                phone: formData.owner_phone,
                password: formData.owner_password
            });

            setFormData({ name: "", whatsapp_phone_number_id: "", whatsapp_display_number: "", whatsapp_access_token: "", whatsapp_verify_token: "hellodine", max_branches: 1, owner_phone: "", owner_password: "" });
            setShowAdd(false);
            fetchRestaurants();
            alert("Restaurant and Owner Account created successfully!");
        } catch (err: any) {
            alert(err.response?.data?.detail || "Failed to create restaurant");
        }
    };

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editTarget) return;
        try {
            await client.patch(`/admin/restaurants/${editTarget.id}`, {
                name: formData.name,
                max_branches: formData.max_branches,
                whatsapp_phone_number_id: formData.whatsapp_phone_number_id,
                whatsapp_display_number: formData.whatsapp_display_number,
                whatsapp_access_token: formData.whatsapp_access_token,
                whatsapp_verify_token: formData.whatsapp_verify_token
            });
            setEditTarget(null);
            fetchRestaurants();
        } catch (err) {
            alert("Failed to update restaurant");
        }
    };

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!resetTarget) return;
        try {
            await client.post(`/admin/restaurants/${resetTarget.id}/reset-owner-password`, {
                new_password: newPass
            });
            setResetTarget(null);
            setNewPass("");
            alert("Owner password reset successfully!");
        } catch (err) {
            alert("Failed to reset password");
        }
    }

    const openEdit = (r: Restaurant) => {
        setEditTarget(r);
        setFormData({
            ...formData,
            name: r.name,
            whatsapp_phone_number_id: r.whatsapp_phone_number_id,
            whatsapp_display_number: r.whatsapp_display_number,
            whatsapp_access_token: r.whatsapp_access_token || "",
            whatsapp_verify_token: r.whatsapp_verify_token || "hellodine",
            max_branches: r.max_branches
        });
    };

    if (loading) return <div className="p-8">Loading System Dashboard...</div>;

    return (
        <div className="p-8">
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
                <div>
                    <h1 style={{ fontSize: "2rem", fontWeight: 800 }}>Provider Dashboard</h1>
                    <p style={{ color: "var(--text-muted)" }}>Manage restaurants and branch limits</p>
                </div>
                <button className="btn-primary" onClick={() => { setEditTarget(null); setShowAdd(true); }}>+ Onboard Restaurant</button>
            </header>

            {resetTarget && (
                <div className="modal-overlay">
                    <div className="modal" style={{ maxWidth: "400px" }}>
                        <h2>Reset Owner Password</h2>
                        <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", margin: "12px 0" }}>
                            Resetting password for <strong>{resetTarget.name}</strong> owner.
                        </p>
                        <form onSubmit={handleResetPassword}>
                            <div className="input-group">
                                <label className="input-label">New Password</label>
                                <input
                                    type="password"
                                    className="input"
                                    required
                                    value={newPass}
                                    onChange={e => setNewPass(e.target.value)}
                                    placeholder="Enter new complex password"
                                />
                            </div>
                            <div style={{ display: "flex", gap: "12px", marginTop: "24px" }}>
                                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Reset Password</button>
                                <button type="button" className="btn-secondary" onClick={() => setResetTarget(null)}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {(showAdd || editTarget) && (
                <div className="modal-overlay">
                    <div className="modal" style={{ maxWidth: "500px" }}>
                        <h2>{editTarget ? "Edit Restaurant" : "Onboard New Restaurant"}</h2>
                        <form onSubmit={editTarget ? handleUpdate : handleCreate} style={{ marginTop: "20px" }}>
                            <div className="input-group">
                                <label className="input-label">Restaurant Name</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="e.g. Pizza Paradise"
                                />
                            </div>

                            {!editTarget && (
                                <div style={{ background: "rgba(255,255,255,0.03)", padding: "16px", borderRadius: "8px", marginBottom: "20px", border: "1px solid var(--border)" }}>
                                    <h3 style={{ fontSize: "0.9rem", marginBottom: "12px", color: "var(--orange)" }}>Initial Owner Account</h3>
                                    <div className="input-group">
                                        <label className="input-label">Owner Phone (+91...)</label>
                                        <input
                                            className="input"
                                            required
                                            value={formData.owner_phone}
                                            onChange={e => setFormData({ ...formData, owner_phone: e.target.value })}
                                            placeholder="+91 90000 00000"
                                        />
                                    </div>
                                    <div className="input-group" style={{ marginBottom: 0 }}>
                                        <label className="input-label">Owner Password</label>
                                        <input
                                            type="password"
                                            className="input"
                                            required
                                            value={formData.owner_password}
                                            onChange={e => setFormData({ ...formData, owner_password: e.target.value })}
                                            placeholder="Initial password"
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="input-group">
                                <label className="input-label">WhatsApp Phone Number ID</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.whatsapp_phone_number_id}
                                    onChange={e => setFormData({ ...formData, whatsapp_phone_number_id: e.target.value })}
                                    placeholder="from Meta Dev Portal"
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">WhatsApp Display Number</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.whatsapp_display_number}
                                    onChange={e => setFormData({ ...formData, whatsapp_display_number: e.target.value })}
                                    placeholder="e.g. +91 98765 43210"
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Meta Access Token</label>
                                <input
                                    className="input"
                                    type="password"
                                    value={formData.whatsapp_access_token}
                                    onChange={e => setFormData({ ...formData, whatsapp_access_token: e.target.value })}
                                    placeholder="EAAB..."
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Webhook Verify Token</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.whatsapp_verify_token}
                                    onChange={e => setFormData({ ...formData, whatsapp_verify_token: e.target.value })}
                                    placeholder="e.g. hellodine"
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Max Allowed Branches</label>
                                <input
                                    type="number"
                                    className="input"
                                    required
                                    min="1"
                                    value={formData.max_branches}
                                    onChange={e => setFormData({ ...formData, max_branches: parseInt(e.target.value) })}
                                />
                            </div>
                            <div style={{ display: "flex", gap: "12px", marginTop: "24px" }}>
                                <button type="submit" className="btn-primary" style={{ flex: 1 }}>{editTarget ? "Save Changes" : "Onboard"}</button>
                                <button type="button" className="btn-secondary" onClick={() => { setShowAdd(false); setEditTarget(null); }}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div className="card" style={{ padding: 0, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid var(--border)" }}>
                            <th style={{ padding: "16px", textAlign: "left" }}>Restaurant</th>
                            <th style={{ padding: "16px", textAlign: "left" }}>WhatsApp ID</th>
                            <th style={{ padding: "16px", textAlign: "center" }}>Branch Limit</th>
                            <th style={{ padding: "16px", textAlign: "center" }}>Status</th>
                            <th style={{ padding: "16px", textAlign: "center" }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {restaurants.map(r => (
                            <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }}>
                                <td style={{ padding: "16px" }}>
                                    <div style={{ fontWeight: 700 }}>{r.name}</div>
                                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{r.whatsapp_display_number}</div>
                                </td>
                                <td style={{ padding: "16px", fontFamily: "monospace", fontSize: "0.8rem" }}>
                                    <div>ID: {r.whatsapp_phone_number_id}</div>
                                    <div style={{ color: "var(--accent)", marginTop: "4px" }}>
                                        URL: {window.location.origin.replace("5173", "8000")}/api/webhook/{r.id}
                                    </div>
                                </td>
                                <td style={{ padding: "16px", textAlign: "center" }}>
                                    <span style={{
                                        padding: "4px 12px",
                                        borderRadius: "20px",
                                        background: "rgba(84,160,255,0.1)",
                                        color: "var(--blue)",
                                        fontWeight: 600
                                    }}>
                                        {r.max_branches}
                                    </span>
                                </td>
                                <td style={{ padding: "16px", textAlign: "center" }}>
                                    <span className={r.is_active ? "badge-ready" : "badge-new"}>
                                        {r.is_active ? "ACTIVE" : "INACTIVE"}
                                    </span>
                                </td>
                                <td style={{ padding: "16px", textAlign: "center" }}>
                                    <div style={{ display: "flex", gap: "8px", justifyContent: "center" }}>
                                        <button className="btn-secondary" style={{ padding: "6px 12px", fontSize: "0.8rem" }} onClick={() => openEdit(r)}>
                                            ✏️ Edit
                                        </button>
                                        <button className="btn-secondary" style={{ padding: "6px 12px", fontSize: "0.8rem", border: "1px solid var(--orange)", color: "var(--orange)" }} onClick={() => setResetTarget(r)}>
                                            🔑 Reset Pass
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
