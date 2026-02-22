import { useState, useEffect } from "react";
import client from "../../api/client";

interface Restaurant {
    id: string;
    name: string;
    whatsapp_phone_number_id: string;
    whatsapp_display_number: string;
    max_branches: number;
    is_active: boolean;
    created_at: string;
}

export default function SystemAdmin() {
    const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        whatsapp_phone_number_id: "",
        whatsapp_display_number: "",
        max_branches: 1
    });

    useEffect(() => {
        fetchRestaurants();
    }, []);

    const fetchRestaurants = async () => {
        try {
            const res = await client.get("/api/admin/restaurants");
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
            await client.post("/api/admin/restaurants", formData);
            setFormData({ name: "", whatsapp_phone_number_id: "", whatsapp_display_number: "", max_branches: 1 });
            setShowAdd(false);
            fetchRestaurants();
        } catch (err) {
            alert("Failed to create restaurant");
        }
    };

    if (loading) return <div className="p-8">Loading System Dashboard...</div>;

    return (
        <div className="p-8">
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
                <div>
                    <h1 style={{ fontSize: "2rem", fontWeight: 800 }}>Provider Dashboard</h1>
                    <p style={{ color: "var(--text-muted)" }}>Manage restaurants and branch limits</p>
                </div>
                <button className="btn-primary" onClick={() => setShowAdd(true)}>+ Onboard Restaurant</button>
            </header>

            {showAdd && (
                <div className="modal-overlay">
                    <div className="modal" style={{ maxWidth: "500px" }}>
                        <h2>Onboard New Restaurant</h2>
                        <form onSubmit={handleCreate} style={{ marginTop: "20px" }}>
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
                                <label className="input-label">Max Allowed Branches</label>
                                <input
                                    type="number"
                                    className="input"
                                    required
                                    min="1"
                                    value={formData.max_branches}
                                    onChange={e => setFormData({ ...formData, max_branches: parseInt(e.target.value) })}
                                />
                                <p style={{ fontSize: "0.75rem", color: "var(--orange)", marginTop: "4px" }}>
                                    Customers will be charged based on this limit.
                                </p>
                            </div>
                            <div style={{ display: "flex", gap: "12px", marginTop: "24px" }}>
                                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Onboard</button>
                                <button type="button" className="btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
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
                            <th style={{ padding: "16px", textAlign: "right" }}>Joined</th>
                        </tr>
                    </thead>
                    <tbody>
                        {restaurants.map(r => (
                            <tr key={r.id} style={{ borderBottom: "1px solid var(--border)" }}>
                                <td style={{ padding: "16px" }}>
                                    <div style={{ fontWeight: 700 }}>{r.name}</div>
                                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{r.whatsapp_display_number}</div>
                                </td>
                                <td style={{ padding: "16px", fontFamily: "monospace", fontSize: "0.8rem" }}>{r.whatsapp_phone_number_id}</td>
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
                                <td style={{ padding: "16px", textAlign: "right", color: "var(--text-muted)", fontSize: "0.85rem" }}>
                                    {new Date(r.created_at).toLocaleDateString()}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
