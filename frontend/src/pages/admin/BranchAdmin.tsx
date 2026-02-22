import { useState, useEffect } from "react";
import client from "../../api/client";

interface Branch {
    id: string;
    restaurant_id: string;
    name: string;
    address: string;
    city: string;
    state: string;
    pincode: string;
    gstin?: string;
    created_at: string;
}

export default function BranchAdmin() {
    const [branches, setBranches] = useState<Branch[]>([]);
    const [maxBranches, setMaxBranches] = useState(1);
    const [loading, setLoading] = useState(true);
    const [showAdd, setShowAdd] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        address: "",
        city: "",
        state: "",
        pincode: "",
        gstin: ""
    });

    const staffData = JSON.parse(localStorage.getItem("hd_staff") || "{}");
    const restaurantId = staffData.restaurant_id;

    useEffect(() => {
        if (restaurantId) {
            Promise.all([
                fetchBranches(),
                fetchRestaurantInfo()
            ]).finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, [restaurantId]);

    const fetchBranches = async () => {
        try {
            const res = await client.get(`/admin/branches?restaurant_id=${restaurantId}`);
            setBranches(res.data);
        } catch (err) {
            console.error("Failed to fetch branches", err);
        }
    };

    const fetchRestaurantInfo = async () => {
        try {
            const res = await client.get(`/admin/restaurants/${restaurantId}`);
            if (res.data) setMaxBranches(res.data.max_branches);
        } catch (err) {
            console.error("Failed to fetch restaurant info", err);
        }
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await client.post("/admin/branches", {
                ...formData,
                restaurant_id: restaurantId
            });
            setFormData({ name: "", address: "", city: "", state: "", pincode: "", gstin: "" });
            setShowAdd(false);
            fetchBranches();
        } catch (err: any) {
            alert(err.response?.data?.detail || "Failed to create branch");
        }
    };

    if (loading) return <div className="p-8">Loading Branch Manager...</div>;

    const limitReached = branches.length >= maxBranches;

    return (
        <div className="p-8">
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
                <div>
                    <h1 style={{ fontSize: "2rem", fontWeight: 800 }}>Manage Branches</h1>
                    <p style={{ color: "var(--text-muted)" }}>
                        You are using <strong>{branches.length}</strong> of <strong>{maxBranches}</strong> allowed branches.
                    </p>
                </div>
                {!limitReached ? (
                    <button className="btn-primary" onClick={() => setShowAdd(true)}>+ Add Branch</button>
                ) : (
                    <button className="btn-secondary" style={{ opacity: 0.6, cursor: "not-allowed" }} title="Limit reached">
                        Limit Reached
                    </button>
                )}
            </header>

            {showAdd && (
                <div className="modal-overlay">
                    <div className="modal" style={{ maxWidth: "600px" }}>
                        <h2>Add New Branch</h2>
                        <form onSubmit={handleCreate} style={{ marginTop: "20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                            <div className="input-group" style={{ gridColumn: "span 2" }}>
                                <label className="input-label">Branch Name</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="e.g. Indiranagar Outlet"
                                />
                            </div>
                            <div className="input-group" style={{ gridColumn: "span 2" }}>
                                <label className="input-label">Address</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.address}
                                    onChange={e => setFormData({ ...formData, address: e.target.value })}
                                    placeholder="Full street address"
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">City</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.city}
                                    onChange={e => setFormData({ ...formData, city: e.target.value })}
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">State</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.state}
                                    onChange={e => setFormData({ ...formData, state: e.target.value })}
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">Pincode</label>
                                <input
                                    className="input"
                                    required
                                    value={formData.pincode}
                                    onChange={e => setFormData({ ...formData, pincode: e.target.value })}
                                />
                            </div>
                            <div className="input-group">
                                <label className="input-label">GSTIN (Optional)</label>
                                <input
                                    className="input"
                                    value={formData.gstin}
                                    onChange={e => setFormData({ ...formData, gstin: e.target.value })}
                                />
                            </div>
                            <div style={{ display: "flex", gap: "12px", marginTop: "12px", gridColumn: "span 2" }}>
                                <button type="submit" className="btn-primary" style={{ flex: 1 }}>Create Branch</button>
                                <button type="button" className="btn-secondary" onClick={() => setShowAdd(false)}>Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "24px" }}>
                {branches.map(b => (
                    <div key={b.id} className="card" style={{ padding: "24px" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                            <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>{b.name}</h3>
                            <span className="badge-ready">ACTIVE</span>
                        </div>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: "1.6", marginBottom: "16px" }}>
                            📍 {b.address}<br />
                            {b.city}, {b.state} - {b.pincode}
                        </p>
                        {b.gstin && (
                            <div style={{ fontSize: "0.8rem", color: "var(--accent)", marginBottom: "16px" }}>
                                🧾 GSTIN: {b.gstin}
                            </div>
                        )}
                        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "16px", display: "flex", gap: "12px" }}>
                            <button className="btn-secondary" style={{ padding: "8px 16px", fontSize: "0.8rem" }}>⚙️ Settings</button>
                            <button className="btn-secondary" style={{ padding: "8px 16px", fontSize: "0.8rem" }}>📋 View Menu</button>
                        </div>
                    </div>
                ))}
            </div>

            {limitReached && (
                <div style={{
                    marginTop: "32px",
                    padding: "24px",
                    background: "rgba(255,159,67,0.05)",
                    borderRadius: "var(--radius)",
                    border: "1px dashed var(--orange)",
                    textAlign: "center"
                }}>
                    <p style={{ color: "var(--orange)", fontWeight: 600 }}>
                        ⚠️ You have reached your branch limit ({maxBranches}).
                    </p>
                    <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "4px" }}>
                        To open more locations, please contact the application provider to upgrade your plan.
                    </p>
                </div>
            )}
        </div>
    );
}
